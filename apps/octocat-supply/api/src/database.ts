import { createHash, randomUUID } from "node:crypto";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { AppError, notFound } from "./errors.js";
import { calculateTotals, validateQuantity } from "./pricing.js";
import { anonymousOwner } from "./auth.js";

export const migrations = [
  {
    version: 1,
    sql: `
    CREATE TABLE products (
      id INTEGER PRIMARY KEY CHECK(id > 0),
      name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 120),
      unit_price_minor INTEGER NOT NULL CHECK(unit_price_minor >= 0),
      category TEXT NOT NULL CHECK(category IN ('feeding', 'play', 'everyday'))
    ) STRICT;
    CREATE TABLE carts (id TEXT PRIMARY KEY NOT NULL) STRICT;
    CREATE TABLE cart_items (
      cart_id TEXT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
      product_id INTEGER NOT NULL REFERENCES products(id),
      quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 99),
      PRIMARY KEY(cart_id, product_id)
    ) STRICT;
  `,
  },
  {
    version: 2,
    sql: "CREATE INDEX products_name ON products(name COLLATE NOCASE);",
  },
  {
    version: 3,
    sql: "ALTER TABLE carts ADD COLUMN owner_key TEXT NOT NULL DEFAULT 'anonymous:v1';",
  },
];

export type Product = {
  id: number;
  name: string;
  unitPriceMinor: number;
  category: "feeding" | "play" | "everyday";
  currency: "GBP";
};

export const fixtures: Product[] = Array.from({ length: 12 }, (_, index) => ({
  id: index + 1,
  name:
    index === 0
      ? "Demo Feeder"
      : index === 1
        ? "Demo Toy"
        : `Synthetic Product ${String(index + 1).padStart(2, "0")}`,
  unitPriceMinor: index === 0 ? 12999 : index === 1 ? 1999 : 1500,
  category: index === 0 ? "feeding" : index === 1 ? "play" : "everyday",
  currency: "GBP",
}));

const productColumns =
  "id, name, unit_price_minor AS unitPriceMinor, category, 'GBP' AS currency";
const checksum = (sql: string) =>
  createHash("sha256").update(sql).digest("hex");

export class Store {
  readonly db: DatabaseSync;

  constructor(file: string) {
    if (file !== ":memory:") mkdirSync(dirname(file), { recursive: true });
    this.db = new DatabaseSync(file, { timeout: 1000 });
    this.db.exec("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;");
  }

  close() {
    this.db.close();
  }

  private transaction<T>(action: () => T): T {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const result = action();
      this.db.exec("COMMIT");
      return result;
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  migrate(list = migrations) {
    this.db.exec(
      "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL) STRICT;",
    );
    const applied = this.db
      .prepare(
        "SELECT version, checksum FROM schema_migrations ORDER BY version",
      )
      .all() as { version: number; checksum: string }[];
    // Reject unknown, removed, reordered and edited applied migrations.
    for (let index = 0; index < applied.length; index++) {
      const migration = list[index];
      if (
        !migration ||
        migration.version !== applied[index].version ||
        checksum(migration.sql) !== applied[index].checksum
      ) {
        throw new Error("Applied migration checksum/order mismatch.");
      }
    }
    for (let index = 0; index < list.length; index++) {
      const migration = list[index];
      if (migration.version !== index + 1)
        throw new Error("Migration order is not valid.");
      if (index < applied.length) continue;
      this.transaction(() => {
        this.db.exec(migration.sql);
        this.db
          .prepare("INSERT INTO schema_migrations VALUES (?, ?)")
          .run(migration.version, checksum(migration.sql));
      });
    }
  }

  schemaReady(): boolean {
    try {
      const rows = this.db
        .prepare(
          "SELECT version, checksum FROM schema_migrations ORDER BY version",
        )
        .all() as { version: number; checksum: string }[];
      return (
        rows.length === migrations.length &&
        rows.every(
          (row, index) =>
            row.version === migrations[index].version &&
            row.checksum === checksum(migrations[index].sql),
        )
      );
    } catch {
      return false;
    }
  }

  ready(): boolean {
    if (!this.schemaReady()) return false;
    try {
      const rows = this.db
        .prepare(`SELECT ${productColumns} FROM products ORDER BY id`)
        .all();
      return JSON.stringify(rows) === JSON.stringify(fixtures);
    } catch {
      return false;
    }
  }

  seed(reset = false) {
    if (!this.schemaReady()) throw new Error("Run migrations before seeding.");
    this.transaction(() => {
      if (reset)
        this.db.exec(
          "DELETE FROM cart_items; DELETE FROM carts; DELETE FROM products;",
        );
      const insert = this.db.prepare(
        "INSERT INTO products (id, name, unit_price_minor, category) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
      );
      for (const product of fixtures)
        insert.run(
          product.id,
          product.name,
          product.unitPriceMinor,
          product.category,
        );
      if (!this.ready())
        throw new Error("Fixture mismatch; use an explicit demo reset.");
    });
  }

  products(
    search: string,
    category: string,
    sort: "name" | "price",
    limit: number,
    offset: number,
  ) {
    const term = `%${search.replace(/[\\%_]/g, "\\$&")}%`;
    const where =
      "WHERE name LIKE ? ESCAPE '\\' AND (? = 'all' OR category = ?)";
    const values = [term, category, category];
    const order = sort === "price" ? "unit_price_minor" : "name COLLATE NOCASE";
    const items = this.db
      .prepare(
        `SELECT ${productColumns} FROM products ${where} ORDER BY ${order}, id LIMIT ? OFFSET ?`,
      )
      .all(...values, limit, offset) as Product[];
    const total = (
      this.db
        .prepare(`SELECT count(*) AS count FROM products ${where}`)
        .get(...values) as { count: number }
    ).count;
    return { items, total, limit, offset };
  }

  product(id: number): Product {
    return (
      (this.db
        .prepare(`SELECT ${productColumns} FROM products WHERE id = ?`)
        .get(id) as Product | undefined) ?? notFound()
    );
  }

  createCart(owner = anonymousOwner) {
    const id = randomUUID();
    this.db
      .prepare("INSERT INTO carts (id, owner_key) VALUES (?, ?)")
      .run(id, owner);
    return this.cart(id, owner);
  }

  cart(id: string, owner = anonymousOwner) {
    if (
      !this.db
        .prepare("SELECT id FROM carts WHERE id = ? AND owner_key = ?")
        .get(id, owner)
    )
      notFound();
    const items = this.db
      .prepare(
        `SELECT p.id AS productId, p.name, p.unit_price_minor AS unitPriceMinor, i.quantity,
      p.unit_price_minor * i.quantity AS lineTotalMinor
      FROM cart_items i JOIN products p ON p.id = i.product_id WHERE i.cart_id = ? ORDER BY p.id`,
      )
      .all(id) as {
      productId: number;
      name: string;
      unitPriceMinor: number;
      quantity: number;
      lineTotalMinor: number;
    }[];
    return { id, items, ...calculateTotals(items) };
  }

  setQuantity(
    cartId: string,
    productId: number,
    quantity: number,
    owner = anonymousOwner,
  ) {
    validateQuantity(quantity);
    return this.transaction(() => {
      const cart = this.cart(cartId, owner);
      this.product(productId);
      if (
        cart.items.length >= 100 &&
        !cart.items.some((item) => item.productId === productId)
      ) {
        throw new AppError(
          400,
          "CART_LIMIT",
          "A cart may contain at most 100 different products.",
        );
      }
      this.db
        .prepare(
          "INSERT INTO cart_items VALUES (?, ?, ?) ON CONFLICT(cart_id, product_id) DO UPDATE SET quantity = excluded.quantity",
        )
        .run(cartId, productId, quantity);
      return this.cart(cartId, owner);
    });
  }

  removeItem(cartId: string, productId: number, owner = anonymousOwner) {
    this.transaction(() => {
      this.cart(cartId, owner);
      this.db
        .prepare("DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?")
        .run(cartId, productId);
    });
  }

  deleteCart(id: string, owner = anonymousOwner) {
    this.transaction(() => {
      this.cart(id, owner);
      this.db.prepare("DELETE FROM carts WHERE id = ?").run(id);
    });
  }
}
