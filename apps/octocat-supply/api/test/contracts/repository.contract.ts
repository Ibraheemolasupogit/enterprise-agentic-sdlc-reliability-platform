import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { Repository } from "../../src/repository.js";

type Maybe<T> = T | Promise<T>;

// Each factory owns an isolated, migrated/seeded database. Every open() must
// return an independent connection to that same database, not a new database.
export interface RepositoryFixture {
  open(): Maybe<Repository>;
  dispose(): Maybe<void>;
}

const owners = [`oidc:${"a".repeat(64)}`, `oidc:${"b".repeat(64)}`];
const absentCart = "00000000-0000-4000-8000-000000000000";
const notFound = {
  status: 404,
  code: "NOT_FOUND",
  message: "The requested resource was not found.",
};
const emptyTotals = {
  items: [],
  currency: "GBP",
  subtotalMinor: 0,
  discountMinor: 0,
  totalMinor: 0,
  discountLabel: null,
};

// Wrapping invocation also captures synchronous SQLite errors. All contract
// operations are awaited so the same assertions exercise an async SQL adapter.
const invoke = <T>(action: () => Maybe<T>) => Promise.resolve().then(action);

export function repositoryContract(
  name: string,
  createFixture: () => Maybe<RepositoryFixture>,
) {
  describe(name, () => {
    let fixture: RepositoryFixture | undefined;
    let repository: Repository;
    const connections = new Set<Repository>();

    async function open() {
      if (!fixture) throw new Error("Repository fixture is not initialized.");
      const connection = await fixture.open();
      connections.add(connection);
      return connection;
    }

    async function closeAll() {
      const results = await Promise.allSettled(
        [...connections].map(async (connection) => {
          await connection.close();
          connections.delete(connection);
        }),
      );
      const failures = results.filter((result) => result.status === "rejected");
      if (failures.length)
        throw new AggregateError(
          failures.map((result) => result.reason),
          "Repository connection cleanup failed.",
        );
    }

    beforeEach(async () => {
      fixture = undefined;
      fixture = await createFixture();
      repository = await open();
    });

    afterEach(async () => {
      try {
        await closeAll();
      } finally {
        try {
          await fixture?.dispose();
        } finally {
          fixture = undefined;
          connections.clear();
        }
      }
    });

    it("R01: exposes the exact seeded catalogue and product details on a ready database", async () => {
      expect(await repository.ready()).toBe(true);
      const expected = Array.from({ length: 12 }, (_, index) => ({
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
      expect(await repository.products("", "all", "name", 100, 0)).toEqual({
        items: expected,
        total: 12,
        limit: 100,
        offset: 0,
      });
      for (const product of expected)
        expect(await repository.product(product.id)).toEqual(product);
    });

    it("R02: combines case-insensitive search/category filters and counts before pagination", async () => {
      const result = await repository.products(
        "SYNTHETIC",
        "everyday",
        "name",
        2,
        3,
      );
      expect(result).toMatchObject({ total: 10, limit: 2, offset: 3 });
      expect(result.items.map((p) => p.id)).toEqual([6, 7]);
      expect(
        (await repository.products("demo", "feeding", "name", 10, 0)).items.map(
          (p) => p.id,
        ),
      ).toEqual([1]);
      expect(
        await repository.products("demo", "everyday", "name", 10, 0),
      ).toEqual({
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      });
      expect(await repository.products("", "all", "name", 2, 12)).toEqual({
        items: [],
        total: 12,
        limit: 2,
        offset: 12,
      });
    });

    it("R03: treats wildcard and SQL-like search input as literal data", async () => {
      for (const term of ["%", "_", "\\", "[", "' OR 1=1 --"])
        expect(await repository.products(term, "all", "name", 100, 0)).toEqual({
          items: [],
          total: 0,
          limit: 100,
          offset: 0,
        });
      expect(await repository.ready()).toBe(true);
    });

    it("R04: sorts and pages equal prices deterministically by product ID", async () => {
      const ids: number[] = [];
      for (let offset = 0; offset < 12; offset += 3) {
        const page = await repository.products("", "all", "price", 3, offset);
        expect(page.total).toBe(12);
        ids.push(...page.items.map((p) => p.id));
      }
      expect(ids).toEqual([3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 2, 1]);
    });

    it("R05: reports a missing product with the safe domain error", async () => {
      await expect(invoke(() => repository.product(999))).rejects.toMatchObject(
        notFound,
      );
    });

    it("R06: creates distinct empty carts, including two for the same owner", async () => {
      const carts = await Promise.all([
        invoke(() => repository.createCart(owners[0])),
        invoke(() => repository.createCart(owners[0])),
        invoke(() => repository.createCart(owners[1])),
      ]);
      expect(new Set(carts.map((cart) => cart.id)).size).toBe(3);
      for (const cart of carts) {
        expect(cart.id).toMatch(
          /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i,
        );
        expect(cart).toEqual({ id: cart.id, ...emptyTotals });
      }
    });

    it.each(["cart", "setQuantity", "removeItem", "deleteCart"] as const)(
      "R07/%s: both owners receive the same denial as a missing cart, without mutation",
      async (method) => {
        const observer = await open();
        const carts = await Promise.all(
          owners.map((owner) => repository.createCart(owner)),
        );
        const snapshots = await Promise.all(
          carts.map((cart, i) =>
            repository.setQuantity(cart.id, 1, i + 1, owners[i]),
          ),
        );
        const call = (id: string, owner: string) =>
          invoke(() => {
            if (method === "setQuantity")
              return repository.setQuantity(id, 1, 9, owner);
            if (method === "removeItem")
              return repository.removeItem(id, 1, owner);
            if (method === "deleteCart")
              return repository.deleteCart(id, owner);
            return repository.cart(id, owner);
          });
        for (let i = 0; i < owners.length; i++) {
          await expect(call(carts[1 - i].id, owners[i])).rejects.toMatchObject(
            notFound,
          );
          await expect(call(absentCart, owners[i])).rejects.toMatchObject(
            notFound,
          );
        }
        for (let i = 0; i < owners.length; i++)
          expect(await observer.cart(carts[i].id, owners[i])).toEqual(
            snapshots[i],
          );
      },
    );

    it("R08: isolates same-product mutations and removals across carts and owners", async () => {
      const first = await repository.createCart(owners[0]);
      const second = await repository.createCart(owners[0]);
      const foreign = await repository.createCart(owners[1]);
      await repository.setQuantity(first.id, 2, 2, owners[0]);
      const secondSnapshot = await repository.setQuantity(
        second.id,
        2,
        3,
        owners[0],
      );
      const foreignSnapshot = await repository.setQuantity(
        foreign.id,
        2,
        4,
        owners[1],
      );
      await repository.removeItem(first.id, 2, owners[0]);
      const observer = await open();
      expect(await observer.cart(first.id, owners[0])).toEqual({
        id: first.id,
        ...emptyTotals,
      });
      expect(await observer.cart(second.id, owners[0])).toEqual(secondSnapshot);
      expect(await observer.cart(foreign.id, owners[1])).toEqual(
        foreignSnapshot,
      );
    });

    it("R09: sets absolute quantities at both bounds, deduplicates retries and orders lines", async () => {
      const { id } = await repository.createCart(owners[0]);
      expect(
        (await repository.setQuantity(id, 2, 99, owners[0])).items,
      ).toEqual([
        {
          productId: 2,
          name: "Demo Toy",
          unitPriceMinor: 1999,
          quantity: 99,
          lineTotalMinor: 197901,
        },
      ]);
      await repository.setQuantity(id, 1, 1, owners[0]);
      const result = await repository.setQuantity(id, 2, 1, owners[0]);
      expect(result.items).toEqual([
        {
          productId: 1,
          name: "Demo Feeder",
          unitPriceMinor: 12999,
          quantity: 1,
          lineTotalMinor: 12999,
        },
        {
          productId: 2,
          name: "Demo Toy",
          unitPriceMinor: 1999,
          quantity: 1,
          lineTotalMinor: 1999,
        },
      ]);
      expect(await repository.setQuantity(id, 2, 1, owners[0])).toEqual(result);
      expect((await repository.cart(id, owners[0])).totalMinor).toBe(14998);
    });

    it("R10: computes authoritative integer prices, floors the discount and reprices after removal", async () => {
      const { id } = await repository.createCart(owners[0]);
      await repository.setQuantity(id, 1, 2, owners[0]);
      expect(await repository.setQuantity(id, 2, 3, owners[0])).toMatchObject({
        currency: "GBP",
        subtotalMinor: 31995,
        discountMinor: 3199,
        totalMinor: 28796,
        discountLabel: "10% basket offer",
      });
      await repository.removeItem(id, 1, owners[0]);
      expect(await repository.cart(id, owners[0])).toMatchObject({
        subtotalMinor: 5997,
        discountMinor: 0,
        totalMinor: 5997,
        discountLabel: null,
      });
    });

    it("R11: applies the exact discount threshold and removes it below the threshold", async () => {
      const { id } = await repository.createCart(owners[0]);
      expect(await repository.setQuantity(id, 3, 19, owners[0])).toMatchObject({
        subtotalMinor: 28500,
        discountMinor: 0,
        totalMinor: 28500,
        discountLabel: null,
      });
      expect(await repository.setQuantity(id, 3, 20, owners[0])).toMatchObject({
        subtotalMinor: 30000,
        discountMinor: 3000,
        totalMinor: 27000,
        discountLabel: "10% basket offer",
      });
      expect(await repository.setQuantity(id, 3, 19, owners[0])).toMatchObject({
        subtotalMinor: 28500,
        discountMinor: 0,
        totalMinor: 28500,
        discountLabel: null,
      });
    });

    it.each([0, -1, 1.5, 100, NaN, Infinity, -Infinity])(
      "R12/%s: rejects invalid quantities without changing committed state or poisoning the connection",
      async (quantity) => {
        const { id } = await repository.createCart(owners[0]);
        const before = await repository.setQuantity(id, 1, 2, owners[0]);
        await expect(
          invoke(() => repository.setQuantity(id, 1, quantity, owners[0])),
        ).rejects.toMatchObject({ status: 400, code: "INVALID_INPUT" });
        expect(await (await open()).cart(id, owners[0])).toEqual(before);
        expect(await repository.setQuantity(id, 2, 1, owners[0])).toMatchObject(
          { subtotalMinor: 27997 },
        );
      },
    );

    it("R13: missing-product failure preserves the cart and allows a subsequent transaction", async () => {
      const { id } = await repository.createCart(owners[0]);
      const before = await repository.setQuantity(id, 1, 2, owners[0]);
      await expect(
        invoke(() => repository.setQuantity(id, 999, 1, owners[0])),
      ).rejects.toMatchObject(notFound);
      expect(await (await open()).cart(id, owners[0])).toEqual(before);
      await repository.setQuantity(id, 2, 3, owners[0]);
      expect((await repository.cart(id, owners[0])).totalMinor).toBe(28796);
    });

    it("R14: removing a line is idempotent, including absent products, and leaves a usable empty cart", async () => {
      const { id } = await repository.createCart(owners[0]);
      await repository.setQuantity(id, 2, 2, owners[0]);
      await repository.removeItem(id, 999, owners[0]);
      expect((await repository.cart(id, owners[0])).totalMinor).toBe(3998);
      await repository.removeItem(id, 2, owners[0]);
      await repository.removeItem(id, 2, owners[0]);
      expect(await (await open()).cart(id, owners[0])).toEqual({
        id,
        ...emptyTotals,
      });
      expect(
        (await repository.setQuantity(id, 1, 1, owners[0])).totalMinor,
      ).toBe(12999);
    });

    it("R15: deletes only the chosen cart and a repeated delete reports not found", async () => {
      const first = await repository.createCart(owners[0]);
      const second = await repository.createCart(owners[0]);
      await repository.setQuantity(first.id, 1, 2, owners[0]);
      const before = await repository.setQuantity(second.id, 2, 3, owners[0]);
      await repository.deleteCart(first.id, owners[0]);
      const observer = await open();
      await expect(
        invoke(() => observer.cart(first.id, owners[0])),
      ).rejects.toMatchObject(notFound);
      await expect(
        invoke(() => repository.deleteCart(first.id, owners[0])),
      ).rejects.toMatchObject(notFound);
      expect(await observer.cart(second.id, owners[0])).toEqual(before);
      expect(await observer.ready()).toBe(true);
    });

    it("R16: retains ownership, changes and deletions after every connection closes and reopens", async () => {
      const first = await repository.createCart(owners[0]);
      const second = await repository.createCart(owners[1]);
      await repository.setQuantity(first.id, 1, 2, owners[0]);
      const before = await repository.setQuantity(first.id, 2, 3, owners[0]);
      await repository.setQuantity(second.id, 3, 20, owners[1]);
      await closeAll();
      repository = await open();
      expect(await repository.ready()).toBe(true);
      expect(await repository.cart(first.id, owners[0])).toEqual(before);
      expect((await repository.cart(second.id, owners[1])).totalMinor).toBe(
        27000,
      );
      await expect(
        invoke(() => repository.cart(first.id, owners[1])),
      ).rejects.toMatchObject(notFound);
      await repository.deleteCart(second.id, owners[1]);
      const updated = await repository.setQuantity(first.id, 2, 1, owners[0]);
      await closeAll();
      repository = await open();
      expect(await repository.cart(first.id, owners[0])).toEqual(updated);
      await expect(
        invoke(() => repository.cart(second.id, owners[1])),
      ).rejects.toMatchObject(notFound);
    });

    it("R17: two connections retain distinct-product absolute updates over 20 scheduled rounds", async () => {
      const other = await open();
      expect(other).not.toBe(repository);
      const { id } = await repository.createCart(owners[0]);
      for (let round = 1; round <= 20; round++) {
        await Promise.all([
          invoke(() => repository.setQuantity(id, 3, round, owners[0])),
          invoke(() => other.setQuantity(id, 4, 21 - round, owners[0])),
        ]);
        const result = await repository.cart(id, owners[0]);
        expect(
          result.items.map(({ productId, quantity }) => ({
            productId,
            quantity,
          })),
        ).toEqual([
          { productId: 3, quantity: round },
          { productId: 4, quantity: 21 - round },
        ]);
        expect(result).toMatchObject({
          subtotalMinor: 31500,
          discountMinor: 3150,
          totalMinor: 28350,
        });
      }
    });

    it("R18: scheduled same-product writes produce one serialized absolute value and duplicate retries stay idempotent", async () => {
      const other = await open();
      const { id } = await repository.createCart(owners[0]);
      await Promise.all([
        invoke(() => repository.setQuantity(id, 2, 2, owners[0])),
        invoke(() => other.setQuantity(id, 2, 3, owners[0])),
      ]);
      const result = await repository.cart(id, owners[0]);
      expect(result.items).toHaveLength(1);
      expect([2, 3]).toContain(result.items[0].quantity);
      expect(result.totalMinor).toBe(result.items[0].quantity * 1999);
      await Promise.all([
        invoke(() => repository.setQuantity(id, 2, 3, owners[0])),
        invoke(() => other.setQuantity(id, 2, 3, owners[0])),
      ]);
      expect((await other.cart(id, owners[0])).items).toEqual([
        {
          productId: 2,
          name: "Demo Toy",
          unitPriceMinor: 1999,
          quantity: 3,
          lineTotalMinor: 5997,
        },
      ]);
    });
  });
}
