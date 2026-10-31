import { createHash, randomUUID } from "node:crypto";
import sql from "mssql";
import { fixtures, type Product } from "./database.js";
import { AppError, notFound } from "./errors.js";
import { calculateTotals, validateQuantity } from "./pricing.js";
import type { Repository, Cart } from "./repository.js";

export type Params = Record<string, string | number>;
export interface SqlSession {
  query<T>(text: string, params?: Params): Promise<T[]>;
}
export interface SqlExecutor extends SqlSession {
  transaction<T>(action: (session: SqlSession) => Promise<T>): Promise<T>;
  close(): Promise<void>;
}
const unavailable = () =>
  new AppError(
    503,
    "DATABASE_UNAVAILABLE",
    "The database is temporarily unavailable.",
  );

export function sqlConfiguration(
  env: NodeJS.ProcessEnv,
  migration = false,
): sql.config {
  if (
    !/^[a-zA-Z0-9.-]+$/.test(env.SQL_SERVER ?? "") ||
    !/^[a-zA-Z0-9_-]{1,128}$/.test(env.SQL_DATABASE ?? "")
  )
    throw new Error(
      "SQL_SERVER and SQL_DATABASE must be explicit bounded host/database names.",
    );
  const clientId = migration ? env.SQL_MIGRATOR_CLIENT_ID : env.SQL_CLIENT_ID;
  const uuid = /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i;
  if (!uuid.test(env.SQL_CLIENT_ID ?? "") || !uuid.test(clientId ?? ""))
    throw new Error("An explicit managed identity client ID is required.");
  if (migration && clientId!.toLowerCase() === env.SQL_CLIENT_ID!.toLowerCase())
    throw new Error("Migrator and runtime identities must differ.");
  return {
    server: env.SQL_SERVER!,
    database: env.SQL_DATABASE!,
    authentication: {
      type: "azure-active-directory-msi-app-service",
      options: { clientId },
    },
    options: {
      encrypt: true,
      trustServerCertificate: false,
      abortTransactionOnError: true,
    },
    connectionTimeout: 1000,
    requestTimeout: 1000,
    pool: {
      max: 4,
      min: 0,
      idleTimeoutMillis: 10000,
      acquireTimeoutMillis: 1000,
    },
  };
}

export class DriverExecutor implements SqlExecutor {
  private pool: sql.ConnectionPool;
  private connected?: Promise<sql.ConnectionPool>;
  constructor(config: sql.config) {
    this.pool = new sql.ConnectionPool(config);
    this.pool.on("error", () => {});
  }
  private connect() {
    this.connected ??= this.pool.connect().catch(() => {
      this.connected = undefined;
      throw unavailable();
    });
    return this.connected;
  }
  private session(source: sql.ConnectionPool | sql.Transaction): SqlSession {
    return {
      query: async <T>(text: string, params: Params = {}) => {
        try {
          const request =
            source instanceof sql.Transaction
              ? new sql.Request(source)
              : new sql.Request(source);
          for (const [name, value] of Object.entries(params)) {
            if (typeof value === "number")
              request.input(name, sql.BigInt, value);
            else request.input(name, sql.NVarChar(256), value);
          }
          return (await request.query<T>(text)).recordset;
        } catch {
          throw unavailable();
        }
      },
    };
  }
  async query<T>(text: string, params?: Params) {
    return this.session(await this.connect()).query<T>(text, params);
  }
  async transaction<T>(action: (session: SqlSession) => Promise<T>) {
    const tx = new sql.Transaction(await this.connect());
    let started = false;
    try {
      await tx.begin(sql.ISOLATION_LEVEL.SERIALIZABLE);
      started = true;
      const value = await action(this.session(tx));
      await tx.commit();
      return value;
    } catch (error) {
      if (started) await tx.rollback().catch(() => {});
      if (error instanceof AppError) throw error;
      throw unavailable();
    }
  }
  async close() {
    await this.pool.close();
  }
}

export const sqlMigrations = [
  {
    version: 1,
    sql: `
CREATE TABLE dbo.products (
 id int NOT NULL PRIMARY KEY CHECK(id > 0),
 name nvarchar(120) COLLATE Latin1_General_100_CI_AS NOT NULL CHECK(LEN(name) BETWEEN 1 AND 120),
 unit_price_minor int NOT NULL CHECK(unit_price_minor >= 0),
 category varchar(16) NOT NULL CHECK(category IN ('feeding','play','everyday'))
);
CREATE TABLE dbo.carts (id uniqueidentifier NOT NULL PRIMARY KEY, owner_key varchar(80) NOT NULL);
CREATE TABLE dbo.cart_items (
 cart_id uniqueidentifier NOT NULL REFERENCES dbo.carts(id) ON DELETE CASCADE,
 product_id int NOT NULL REFERENCES dbo.products(id),
 quantity int NOT NULL CHECK(quantity BETWEEN 1 AND 99),
 PRIMARY KEY(cart_id,product_id)
);
CREATE INDEX products_name ON dbo.products(name);
`,
  },
];
export const migrationHash = (text: string) =>
  createHash("sha256").update(text).digest("hex");
const columns =
  "id, name, unit_price_minor AS unitPriceMinor, category, 'GBP' AS currency";
const ownerRequired = (owner?: string) => {
  if (!owner || !/^oidc:[a-f0-9]{64}$/.test(owner))
    throw new AppError(
      403,
      "FORBIDDEN",
      "SQL carts require an authenticated owner.",
    );
  return owner;
};

export async function migrateSql(executor: SqlExecutor, list = sqlMigrations) {
  // Separate explicit DDL entrypoint. Runtime/readiness never creates these objects.
  await executor.transaction(async (q) => {
    await q.query(`DECLARE @result int;
EXEC @result=sys.sp_getapplock @Resource=N'morrow-schema', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=1000;
IF @result < 0 THROW 51000, 'Migration lock unavailable', 1;
IF OBJECT_ID(N'dbo.schema_migrations',N'U') IS NULL
 CREATE TABLE dbo.schema_migrations(version int NOT NULL PRIMARY KEY, checksum char(64) NOT NULL);`);
    const applied = await q.query<{ version: number; checksum: string }>(
      "SELECT version,checksum FROM dbo.schema_migrations ORDER BY version",
    );
    for (let i = 0; i < applied.length; i++)
      if (
        !list[i] ||
        list[i].version !== applied[i].version ||
        migrationHash(list[i].sql) !== applied[i].checksum
      )
        throw new Error("Applied SQL migration checksum/order mismatch.");
    for (let i = 0; i < list.length; i++) {
      if (list[i].version !== i + 1)
        throw new Error("Invalid SQL migration order.");
      if (i < applied.length) continue;
      await q.query(list[i].sql);
      await q.query(
        "INSERT INTO dbo.schema_migrations(version,checksum) VALUES(@version,@checksum)",
        { version: list[i].version, checksum: migrationHash(list[i].sql) },
      );
    }
  });
}

export async function seedSql(executor: SqlExecutor) {
  await executor.transaction(async (q) => {
    for (const p of fixtures)
      await q.query(
        `IF NOT EXISTS(SELECT id FROM dbo.products WITH(UPDLOCK,HOLDLOCK) WHERE id=@id)
INSERT INTO dbo.products(id,name,unit_price_minor,category) VALUES(@id,@name,@price,@category)`,
        {
          id: p.id,
          name: p.name,
          price: p.unitPriceMinor,
          category: p.category,
        },
      );
    const rows = await q.query<Product>(
      `SELECT ${columns} FROM dbo.products ORDER BY id`,
    );
    if (JSON.stringify(rows) !== JSON.stringify(fixtures))
      throw new Error(
        "SQL fixture mismatch; no destructive reset is provided.",
      );
  });
}

export class SqlStore implements Repository {
  private readiness?: Promise<boolean>;
  constructor(readonly executor: SqlExecutor) {}
  close() {
    return this.executor.close();
  }
  async ready() {
    // Share an in-flight read to avoid accumulating probes during a dependency outage.
    this.readiness ??= this.checkReady().finally(() => {
      this.readiness = undefined;
    });
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      return await Promise.race([
        this.readiness,
        new Promise<boolean>((resolve) => {
          timer = setTimeout(() => resolve(false), 1000);
        }),
      ]);
    } finally {
      clearTimeout(timer);
    }
  }
  private async checkReady() {
    try {
      const rows = await this.executor.query<{
        version: number;
        checksum: string;
      }>("SELECT version,checksum FROM dbo.schema_migrations ORDER BY version");
      if (
        rows.length !== sqlMigrations.length ||
        rows.some(
          (r, i) =>
            r.version !== sqlMigrations[i].version ||
            r.checksum !== migrationHash(sqlMigrations[i].sql),
        )
      )
        return false;
      return (
        JSON.stringify(
          await this.executor.query<Product>(
            `SELECT ${columns} FROM dbo.products ORDER BY id`,
          ),
        ) === JSON.stringify(fixtures)
      );
    } catch {
      return false;
    }
  }
  async products(
    search: string,
    category: string,
    sort: "name" | "price",
    limit: number,
    offset: number,
  ) {
    const params = {
      term: `%${search.replace(/[\\%_[]/g, "\\$&")}%`,
      category,
      limit,
      offset,
    };
    const where =
      "WHERE name LIKE @term ESCAPE '\\' AND (@category='all' OR category=@category)";
    const order = sort === "price" ? "unit_price_minor" : "name";
    const items = await this.executor.query<Product>(
      `SELECT ${columns} FROM dbo.products ${where} ORDER BY ${order},id OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY`,
      params,
    );
    const rows = await this.executor.query<{ total: number }>(
      `SELECT COUNT(*) AS total FROM dbo.products ${where}`,
      { term: params.term, category },
    );
    return { items, total: rows[0].total, limit, offset };
  }
  async product(id: number): Promise<Product> {
    return (
      (
        await this.executor.query<Product>(
          `SELECT ${columns} FROM dbo.products WHERE id=@id`,
          { id },
        )
      )[0] ?? notFound()
    );
  }
  private async cartIn(
    q: SqlSession,
    id: string,
    owner: string,
  ): Promise<Cart> {
    if (
      !(
        await q.query(
          "SELECT id FROM dbo.carts WITH(UPDLOCK,HOLDLOCK) WHERE id=@id AND owner_key=@owner",
          { id, owner },
        )
      ).length
    )
      notFound();
    const items = await q.query<Cart["items"][number]>(
      `SELECT p.id AS productId,p.name,p.unit_price_minor AS unitPriceMinor,i.quantity,
 p.unit_price_minor*i.quantity AS lineTotalMinor FROM dbo.cart_items i JOIN dbo.products p ON p.id=i.product_id
 JOIN dbo.carts c ON c.id=i.cart_id WHERE c.id=@id AND c.owner_key=@owner ORDER BY p.id`,
      { id, owner },
    );
    return { id, items, ...calculateTotals(items) };
  }
  async createCart(owner?: string) {
    owner = ownerRequired(owner);
    const id = randomUUID();
    return this.executor.transaction(async (q) => {
      await q.query("INSERT INTO dbo.carts(id,owner_key) VALUES(@id,@owner)", {
        id,
        owner: owner!,
      });
      return this.cartIn(q, id, owner!);
    });
  }
  async cart(id: string, owner?: string) {
    const key = ownerRequired(owner);
    return this.executor.transaction((q) => this.cartIn(q, id, key));
  }
  async setQuantity(
    id: string,
    productId: number,
    quantity: number,
    owner?: string,
  ) {
    const key = ownerRequired(owner);
    validateQuantity(quantity);
    return this.executor.transaction(async (q) => {
      const cart = await this.cartIn(q, id, key);
      if (
        !(
          await q.query("SELECT id FROM dbo.products WHERE id=@productId", {
            productId,
          })
        ).length
      )
        notFound();
      if (
        cart.items.length >= 100 &&
        !cart.items.some((i) => i.productId === productId)
      )
        throw new AppError(
          400,
          "CART_LIMIT",
          "A cart may contain at most 100 different products.",
        );
      await q.query(
        `UPDATE dbo.cart_items SET quantity=@quantity WHERE cart_id=@id AND product_id=@productId;
IF @@ROWCOUNT=0 INSERT INTO dbo.cart_items(cart_id,product_id,quantity) VALUES(@id,@productId,@quantity);`,
        { id, productId, quantity },
      );
      return this.cartIn(q, id, key);
    });
  }
  async removeItem(id: string, productId: number, owner?: string) {
    const key = ownerRequired(owner);
    await this.executor.transaction(async (q) => {
      await this.cartIn(q, id, key);
      await q.query(
        "DELETE FROM dbo.cart_items WHERE cart_id=@id AND product_id=@productId",
        { id, productId },
      );
    });
  }
  async deleteCart(id: string, owner?: string) {
    const key = ownerRequired(owner);
    await this.executor.transaction(async (q) => {
      await this.cartIn(q, id, key);
      await q.query("DELETE FROM dbo.carts WHERE id=@id AND owner_key=@owner", {
        id,
        owner: key,
      });
    });
  }
}
