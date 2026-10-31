import { describe, expect, it, vi } from "vitest";
import request from "supertest";
import {
  SqlStore,
  migrateSql,
  seedSql,
  sqlConfiguration,
  sqlMigrations,
  migrationHash,
  type Params,
  type SqlExecutor,
  type SqlSession,
} from "../src/sql.js";
import { fixtures } from "../src/database.js";
import { createApp } from "../src/app.js";

const owner = "oidc:" + "a".repeat(64),
  id = "c18eb8c7-276c-4330-83fe-e842c7e5fb2e";
class RecordingExecutor implements SqlExecutor {
  calls: { text: string; params: Params }[] = [];
  commits = 0;
  rollbacks = 0;
  constructor(
    public answer: (text: string, params: Params) => unknown[] = () => [],
  ) {}
  async query<T>(text: string, params: Params = {}) {
    this.calls.push({ text, params });
    return this.answer(text, params) as T[];
  }
  async transaction<T>(action: (session: SqlSession) => Promise<T>) {
    try {
      const value = await action(this);
      this.commits++;
      return value;
    } catch (error) {
      this.rollbacks++;
      throw error;
    }
  }
  async close() {}
}

describe("SQL adapter contracts — recording driver simulation, not a SQL engine", () => {
  it("bounds total SQL readiness to one second and shares outstanding dependency reads", async () => {
    vi.useFakeTimers();
    try {
      const query = vi.fn(() => new Promise<never>(() => {}));
      const store = new SqlStore({
        query,
        transaction: async () => {
          throw new Error();
        },
        close: async () => {},
      });
      const checks = [store.ready(), store.ready()];
      await vi.advanceTimersByTimeAsync(1000);
      expect(await Promise.all(checks)).toEqual([false, false]);
      expect(query).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });
  it("keeps search input in parameters, escapes wildcard syntax and bounds sorting", async () => {
    const db = new RecordingExecutor((text) =>
      text.includes("COUNT(*)") ? [{ total: 12 }] : fixtures,
    );
    const malicious = "[x]%' OR 1=1 --";
    const result = await new SqlStore(db).products(
      malicious,
      "all",
      "price",
      20,
      0,
    );
    expect(result.total).toBe(12);
    expect(db.calls[0].text).not.toContain(malicious);
    expect(db.calls[0].text).toContain("ORDER BY unit_price_minor,id");
    expect(db.calls[0].params).toMatchObject({
      limit: 20,
      offset: 0,
      category: "all",
    });
    expect(db.calls[0].params.term).toBe("%\\[x]\\%' OR 1=1 --%");
  });
  it("checks/locks the owner before every cart mutation and returns no existence disclosure", async () => {
    const db = new RecordingExecutor();
    const store = new SqlStore(db);
    await expect(store.setQuantity(id, 1, 2, owner)).rejects.toMatchObject({
      status: 404,
    });
    await expect(store.removeItem(id, 1, owner)).rejects.toMatchObject({
      status: 404,
    });
    await expect(store.deleteCart(id, owner)).rejects.toMatchObject({
      status: 404,
    });
    expect(db.calls).toHaveLength(3);
    for (const call of db.calls) {
      expect(call.text).toContain("WITH(UPDLOCK,HOLDLOCK)");
      expect(call.text).toContain("owner_key=@owner");
      expect(call.params).toEqual({ id, owner });
    }
    expect(db.rollbacks).toBe(3);
    await expect(store.createCart("anonymous:v1")).rejects.toMatchObject({
      status: 403,
    });
  });
  it("returns canonical integer totals from transactional mutation results", async () => {
    let updated = false;
    const db = new RecordingExecutor((text, params) => {
      if (text.startsWith("SELECT id FROM dbo.carts")) return [{ id }];
      if (text.startsWith("SELECT id FROM dbo.products")) return [{ id: 1 }];
      if (text.startsWith("UPDATE dbo.cart_items")) {
        expect(params).toEqual({ id, productId: 1, quantity: 2 });
        updated = true;
        return [];
      }
      if (text.includes("AS productId"))
        return updated
          ? [
              {
                productId: 1,
                name: "Demo Feeder",
                unitPriceMinor: 12999,
                quantity: 2,
                lineTotalMinor: 25998,
              },
            ]
          : [];
      throw new Error("Unexpected query");
    });
    const result = await new SqlStore(db).setQuantity(id, 1, 2, owner);
    expect(result.totalMinor).toBe(25998);
    expect(db.commits).toBe(1);
    expect(
      db.calls
        .filter((c) => c.text.includes("AS productId"))
        .every((c) => c.params.owner === owner),
    ).toBe(true);
  });
  it("replays/checksums migrations and rejects edited, removed or reordered history before DDL", async () => {
    const applied: { version: number; checksum: string }[] = [];
    const db = new RecordingExecutor((text, params) => {
      if (text.startsWith("SELECT version")) return applied;
      if (text.startsWith("INSERT INTO dbo.schema_migrations"))
        applied.push({
          version: Number(params.version),
          checksum: String(params.checksum),
        });
      return [];
    });
    await migrateSql(db);
    await migrateSql(db);
    expect(applied).toEqual([
      { version: 1, checksum: migrationHash(sqlMigrations[0].sql) },
    ]);
    expect(
      db.calls.filter((c) => c.text === sqlMigrations[0].sql),
    ).toHaveLength(1);
    const before = db.calls.length;
    await expect(
      migrateSql(db, [{ version: 1, sql: sqlMigrations[0].sql + "--edited" }]),
    ).rejects.toThrow(/mismatch/);
    await expect(migrateSql(db, [])).rejects.toThrow(/mismatch/);
    await expect(
      migrateSql(db, [{ version: 2, sql: sqlMigrations[0].sql }]),
    ).rejects.toThrow();
    expect(
      db.calls.slice(before).some((c) => c.text === sqlMigrations[0].sql),
    ).toBe(false);
    expect(db.rollbacks).toBe(3);
  });
  it("seeds only exact synthetic rows and fails on drift instead of destructive reset", async () => {
    const db = new RecordingExecutor((text) =>
      text.startsWith("SELECT") ? fixtures : [],
    );
    await seedSql(db);
    await seedSql(db);
    expect(
      db.calls.filter((c) => c.text.startsWith("IF NOT EXISTS")),
    ).toHaveLength(24);
    expect(db.calls.some((c) => /DELETE|DROP/.test(c.text))).toBe(false);
    db.answer = (text) => (text.startsWith("SELECT") ? [] : []);
    await expect(seedSql(db)).rejects.toThrow(/mismatch/);
    expect(db.rollbacks).toBe(1);
  });
  it("fails readiness safely on missing schema, drift or unavailable database without DDL", async () => {
    const db = new RecordingExecutor((text) =>
      text.startsWith("SELECT version")
        ? [{ version: 1, checksum: migrationHash(sqlMigrations[0].sql) }]
        : fixtures,
    );
    const store = new SqlStore(db);
    expect(await store.ready()).toBe(true);
    db.answer = () => {
      throw new Error("sensitive connection details");
    };
    expect(await store.ready()).toBe(false);
    const app = createApp(store, { authenticate: async () => owner });
    await request(app).get("/health/live").expect(200);
    const bad = await request(app).get("/health/ready").expect(503);
    expect(JSON.stringify(bad.body)).not.toContain("sensitive");
    expect(db.calls.every((c) => c.text.startsWith("SELECT"))).toBe(true);
  });
  it("requires a pinned managed identity, verified TLS and a separate migrator; no password/default credential fallback", () => {
    const env = {
      SQL_SERVER: "demo.database.windows.net",
      SQL_DATABASE: "morrow",
      SQL_CLIENT_ID: "00000000-0000-4000-8000-000000000001",
    };
    const config = sqlConfiguration(env);
    expect(config.options).toMatchObject({
      encrypt: true,
      trustServerCertificate: false,
    });
    expect(config.authentication?.type).toBe(
      "azure-active-directory-msi-app-service",
    );
    expect(config).not.toHaveProperty("password");
    expect(() => sqlConfiguration({ ...env, SQL_CLIENT_ID: "" })).toThrow();
    expect(() =>
      sqlConfiguration({ ...env, SQL_CLIENT_ID: "-".repeat(36) }),
    ).toThrow();
    expect(() =>
      sqlConfiguration(
        {
          ...env,
          SQL_CLIENT_ID: undefined,
          SQL_MIGRATOR_CLIENT_ID: env.SQL_CLIENT_ID,
        },
        true,
      ),
    ).toThrow();
    expect(() =>
      sqlConfiguration(
        { ...env, SQL_MIGRATOR_CLIENT_ID: env.SQL_CLIENT_ID },
        true,
      ),
    ).toThrow();
    expect(() =>
      sqlConfiguration(
        {
          ...env,
          SQL_CLIENT_ID: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          SQL_MIGRATOR_CLIENT_ID: "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
        },
        true,
      ),
    ).toThrow();
    expect(() =>
      sqlConfiguration({ ...env, SQL_SERVER: "host;Password=bad" }),
    ).toThrow();
  });
});
