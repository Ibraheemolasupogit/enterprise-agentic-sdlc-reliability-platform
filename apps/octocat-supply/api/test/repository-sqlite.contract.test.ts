import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { Store } from "../src/database.js";
import { repositoryContract } from "./contracts/repository.contract.js";

function sqliteFixture() {
  const root = mkdtempSync(join(tmpdir(), "supply-contract-"));
  const file = join(root, "contract.sqlite");
  try {
    const bootstrap = new Store(file);
    try {
      bootstrap.migrate();
      bootstrap.seed();
    } finally {
      bootstrap.close();
    }
  } catch (error) {
    rmSync(root, { recursive: true, force: true });
    throw error;
  }
  return {
    open: () => new Store(file),
    dispose: () => rmSync(root, { recursive: true, force: true }),
  };
}

repositoryContract(
  "Repository acceptance — real file-backed SQLite",
  sqliteFixture,
);

// Engine-specific fault injection belongs outside the shared domain contract.
// These triggers exist only inside this test's disposable SQLite database.
describe("Real SQLite transaction/constraint regressions", () => {
  let fixture: ReturnType<typeof sqliteFixture>;
  let store: Store;
  let observer: Store;
  const owner = `oidc:${"a".repeat(64)}`;

  beforeEach(() => {
    fixture = sqliteFixture();
    store = fixture.open();
    observer = fixture.open();
  });
  afterEach(() => {
    try {
      store?.close();
    } finally {
      try {
        observer?.close();
      } finally {
        fixture?.dispose();
      }
    }
  });

  it.each(["INSERT", "UPDATE", "DELETE"] as const)(
    "S01/%s: rolls back a post-write failure and releases the transaction",
    (operation) => {
      const { id } = store.createCart(owner);
      if (operation !== "INSERT") store.setQuantity(id, 1, 2, owner);
      const before = observer.cart(id, owner);
      // RAISE(FAIL) leaves the statement's earlier changes intact unless the
      // repository rolls back its transaction. ABORT would mask that regression.
      store.db
        .exec(`CREATE TRIGGER contract_failure AFTER ${operation} ON cart_items
        BEGIN SELECT RAISE(FAIL, 'contract injected post-write failure'); END;`);
      expect(() => {
        if (operation === "DELETE") store.removeItem(id, 1, owner);
        else store.setQuantity(id, 1, 3, owner);
      }).toThrow(/contract injected post-write failure/);
      expect(store.db.isTransaction).toBe(false);
      expect(observer.cart(id, owner)).toEqual(before);
      store.db.exec("DROP TRIGGER contract_failure");
      // A different connection can write immediately after the failed mutation.
      expect(
        observer.setQuantity(id, 2, 1, owner).items.at(-1)?.productId,
      ).toBe(2);
    },
  );

  it("S02: enforces foreign keys/quantity/uniqueness and cascades only the deleted cart's lines", () => {
    const first = store.createCart(owner);
    const second = store.createCart(owner);
    store.setQuantity(first.id, 1, 2, owner);
    const before = store.setQuantity(second.id, 2, 3, owner);
    const insert = store.db.prepare("INSERT INTO cart_items VALUES (?, ?, ?)");
    expect(() => insert.run("missing", 1, 1)).toThrow();
    expect(() => insert.run(first.id, 999, 1)).toThrow();
    expect(() => insert.run(first.id, 2, 0)).toThrow();
    expect(() => insert.run(first.id, 1, 2)).toThrow();
    store.deleteCart(first.id, owner);
    expect(
      observer.db
        .prepare("SELECT count(*) AS count FROM cart_items WHERE cart_id = ?")
        .get(first.id),
    ).toEqual({ count: 0 });
    expect(observer.cart(second.id, owner)).toEqual(before);
    expect(observer.db.prepare("PRAGMA foreign_key_check").all()).toEqual([]);
    expect(observer.ready()).toBe(true);
  });

  it("S03: hides uncommitted changes, rejects a contending writer and recovers after rollback", () => {
    const { id } = store.createCart(owner);
    const before = store.setQuantity(id, 1, 2, owner);
    store.db.exec("BEGIN IMMEDIATE");
    try {
      store.db
        .prepare("UPDATE cart_items SET quantity = 4 WHERE cart_id = ?")
        .run(id);
      expect(observer.cart(id, owner)).toEqual(before);
      // The second real connection exhausts the existing 1s SQLite busy timeout.
      // No fake clock or retry is used. This is contention, not parallel writers.
      expect(() => observer.setQuantity(id, 1, 3, owner)).toThrow(/locked/);
      expect(observer.db.isTransaction).toBe(false);
    } finally {
      store.db.exec("ROLLBACK");
    }
    expect(observer.cart(id, owner)).toEqual(before);
    expect(observer.setQuantity(id, 1, 3, owner).items[0].quantity).toBe(3);
    expect(store.cart(id, owner).items[0].quantity).toBe(3);
  });

  it("S04: rolls back a failed cart deletion including its cascaded line deletions", () => {
    const { id } = store.createCart(owner);
    const before = store.setQuantity(id, 1, 2, owner);
    store.db.exec(`CREATE TRIGGER contract_failure AFTER DELETE ON carts
      BEGIN SELECT RAISE(FAIL, 'contract injected cascade failure'); END;`);
    expect(() => store.deleteCart(id, owner)).toThrow(
      /contract injected cascade failure/,
    );
    expect(store.db.isTransaction).toBe(false);
    expect(observer.cart(id, owner)).toEqual(before);
    store.db.exec("DROP TRIGGER contract_failure");
    observer.deleteCart(id, owner);
    expect(() => store.cart(id, owner)).toThrow(/not found/);
  });
});
