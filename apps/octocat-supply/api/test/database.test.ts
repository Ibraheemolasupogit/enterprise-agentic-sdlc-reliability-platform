import { mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { Store, fixtures, migrations } from "../src/database.js";
import { demoDatabasePath } from "../src/config.js";

const folders: string[] = [];
afterEach(() => {
  for (const folder of folders.splice(0))
    rmSync(folder, { recursive: true, force: true });
});

describe("SQLite lifecycle and integrity", () => {
  it("migrates and seeds twice, preserves carts across a fresh connection, and resets deterministically", () => {
    const root = mkdtempSync(join(tmpdir(), "supply-test-"));
    folders.push(root);
    const file = join(root, "test.sqlite");
    let store = new Store(file);
    expect(store.ready()).toBe(false);
    store.migrate();
    store.migrate();
    store.seed();
    store.seed();
    expect(store.products("", "all", "name", 100, 0).total).toBe(12);
    const cart = store.createCart();
    store.setQuantity(cart.id, 1, 2);
    store.close();
    store = new Store(file);
    expect(store.cart(cart.id).subtotalMinor).toBe(25998);
    expect(store.ready()).toBe(true);
    store.seed(true);
    const snapshot = store.db
      .prepare("SELECT * FROM products ORDER BY id")
      .all();
    expect(() => store.cart(cart.id)).toThrow();
    store.seed(true);
    expect(
      store.db.prepare("SELECT * FROM products ORDER BY id").all(),
    ).toEqual(snapshot);
    expect(
      store.products("", "all", "price", 100, 0).items.map((p) => p.id),
    ).toEqual([3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 2, 1]);
    store.close();
  });
  it("rejects edited, reordered and unknown migrations without damaging existing data", () => {
    const store = new Store(":memory:");
    store.migrate();
    store.seed();
    expect(() =>
      store.migrate([
        { ...migrations[0], sql: migrations[0].sql + "-- changed" },
        migrations[1],
      ]),
    ).toThrow(/mismatch/);
    expect(() => store.migrate([...migrations].reverse())).toThrow();
    expect(() => store.migrate([])).toThrow();
    expect(store.ready()).toBe(true);
    store.db.exec("DROP TABLE products");
    expect(store.ready()).toBe(false);
    store.close();
  });
  it("enforces foreign keys and rejects unsafe local database/reset paths, including dangling links", () => {
    const store = new Store(":memory:");
    store.migrate();
    store.seed();
    expect(() =>
      store.db
        .prepare("INSERT INTO cart_items VALUES (?, ?, ?)")
        .run("missing", fixtures[0].id, 1),
    ).toThrow();
    store.close();
    const root = mkdtempSync(join(tmpdir(), "supply-path-"));
    folders.push(root);
    for (const name of [
      "/tmp/other.sqlite",
      "../other.sqlite",
      "https://example.test/db",
      "data/unrelated.sqlite",
    ])
      expect(() => demoDatabasePath(name, root)).toThrow();
    const file = demoDatabasePath("data/demo.sqlite", root);
    const outside = join(root, "outside.sqlite");
    writeFileSync(outside, "unrelated");
    symlinkSync(outside, file);
    expect(() => demoDatabasePath("data/demo.sqlite", root)).toThrow();
    rmSync(file);
    symlinkSync(join(root, "missing.sqlite"), file);
    expect(() => demoDatabasePath("data/demo.sqlite", root)).toThrow();
  });
});
