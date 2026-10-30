import { randomUUID } from "node:crypto";
import request from "supertest";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createApp } from "../src/app.js";
import { Store } from "../src/database.js";

let store: Store;
let app: ReturnType<typeof createApp>;
beforeEach(() => {
  store = new Store(":memory:");
  store.migrate();
  store.seed();
  app = createApp(store);
});
afterEach(() => store.close());
const makeCart = async () =>
  (await request(app).post("/api/carts").send({}).expect(201)).body
    .id as string;

describe("validated catalogue contracts", () => {
  it("lists twelve products, reads details, and filters/searches/sorts/pages deterministically", async () => {
    const list = await request(app).get("/api/products").expect(200);
    expect(list.body.total).toBe(12);
    expect(list.body.items).toHaveLength(12);
    expect(list.headers["x-request-id"]).toBe(list.body.requestId);
    expect(
      (await request(app).get("/api/products/1").expect(200)).body
        .unitPriceMinor,
    ).toBe(12999);
    expect(
      (
        await request(app).get("/api/products?search=%20FEEDER%20").expect(200)
      ).body.items.map((p: { id: number }) => p.id),
    ).toEqual([1]);
    expect(
      (
        await request(app).get("/api/products?category=play").expect(200)
      ).body.items.map((p: { id: number }) => p.id),
    ).toEqual([2]);
    expect(
      (
        await request(app)
          .get("/api/products?sort=price&limit=2&offset=1")
          .expect(200)
      ).body.items.map((p: { id: number }) => p.id),
    ).toEqual([4, 5]);
    for (const search of [
      "no-such-product",
      "' OR 1=1 --",
      "%",
      "_",
      "<script>alert(1)</script>",
    ]) {
      expect(
        (await request(app).get("/api/products").query({ search }).expect(200))
          .body.total,
      ).toBe(0);
    }
  });
  it.each([
    "/api/products/0",
    "/api/products/1.2",
    "/api/products/9007199254740992",
    "/api/products?limit=101",
    "/api/products?offset=-1",
    "/api/products?sort=sql",
    "/api/products?sort=name&sort=price",
    "/api/products?category=unknown",
    "/api/products?unknown=1",
    `/api/products?search=${"x".repeat(101)}`,
  ])("rejects invalid input: %s", async (path) => {
    const response = await request(app).get(path).expect(400);
    expect(response.body.code).toBe("INVALID_INPUT");
    expect(response.body.requestId).toMatch(/^[0-9a-f-]{36}$/);
  });
  it("returns safe missing-resource and body/media/origin errors", async () => {
    await request(app).get("/api/products/999").expect(404);
    await request(app).get("/api/carts/not-a-uuid").expect(400);
    await request(app).get(`/api/carts/${randomUUID()}`).expect(404);
    await request(app).get("/unknown").expect(404);
    await request(app)
      .post("/api/carts")
      .set("Content-Type", "text/plain")
      .send("x")
      .expect(415);
    await request(app)
      .post("/api/carts")
      .set("Content-Type", "application/json")
      .send("{")
      .expect(400);
    await request(app)
      .post("/api/carts")
      .send({ data: "x".repeat(17000) })
      .expect(413);
    await request(app)
      .post("/api/carts")
      .set("Origin", "https://untrusted.example")
      .send({})
      .expect(403);
    await request(app)
      .post("/api/carts")
      .set("Content-Encoding", "gzip")
      .set("Content-Type", "application/json")
      .send("{}")
      .expect(415);
    const response = await request(app)
      .get("/api/products")
      .set("X-Request-ID", "fake-attacker-value")
      .expect(200);
    expect(response.body.requestId).not.toBe("fake-attacker-value");
    expect(JSON.stringify(response.body)).not.toMatch(/SELECT |sqlite|stack/);
  });
});

describe("cart integrity, pricing and cleanup", () => {
  it("persists absolute quantities, canonical prices and an automatic deterministic discount", async () => {
    const id = await makeCart();
    const other = await makeCart();
    await request(app)
      .put(`/api/carts/${id}/items/1`)
      .send({ quantity: 2 })
      .expect(200);
    await request(app)
      .put(`/api/carts/${id}/items/1`)
      .send({ quantity: 2 })
      .expect(200);
    const result = await request(app)
      .put(`/api/carts/${id}/items/2`)
      .send({ quantity: 3 })
      .expect(200);
    expect(result.body.items).toHaveLength(2);
    expect(result.body).toMatchObject({
      subtotalMinor: 31995,
      discountMinor: 3199,
      totalMinor: 28796,
    });
    expect(
      (await request(app).get(`/api/carts/${other}`).expect(200)).body.items,
    ).toHaveLength(0);
    await request(app)
      .put(`/api/carts/${id}/items/1`)
      .send({ quantity: 1, unitPriceMinor: 1 })
      .expect(400);
    await request(app)
      .put(`/api/carts/${id}/items/999`)
      .send({ quantity: 1 })
      .expect(404);
    for (const quantity of [0, -1, 1.2, 100, "1", null])
      await request(app)
        .put(`/api/carts/${id}/items/1`)
        .send({ quantity })
        .expect(400);
    await request(app).delete(`/api/carts/${id}/items/1`).expect(204);
    await request(app).delete(`/api/carts/${id}/items/1`).expect(204);
    expect(
      (await request(app).get(`/api/carts/${id}`).expect(200)).body.totalMinor,
    ).toBe(5997);
    await request(app).delete(`/api/carts/${id}`).expect(204);
    await request(app).get(`/api/carts/${id}`).expect(404);
    expect(
      store.db.prepare("SELECT * FROM cart_items WHERE cart_id = ?").all(id),
    ).toHaveLength(0);
  });
  it("retains all concurrent product updates and never creates duplicate cart lines", async () => {
    const id = await makeCart();
    await Promise.all(
      [1, 2, 3, 4].map((productId) =>
        request(app)
          .put(`/api/carts/${id}/items/${productId}`)
          .send({ quantity: 2 })
          .expect(200),
      ),
    );
    const result = await request(app).get(`/api/carts/${id}`).expect(200);
    expect(result.body.items).toHaveLength(4);
    expect(
      result.body.items.every(
        (item: { quantity: number }) => item.quantity === 2,
      ),
    ).toBe(true);
  });
});

it("separates process liveness from database/seed readiness and fails safely", async () => {
  const empty = new Store(":memory:");
  const unready = createApp(empty);
  await request(unready).get("/health/live").expect(200);
  await request(unready).get("/health/ready").expect(503);
  const response = await request(unready).get("/api/products").expect(503);
  expect(response.body.code).toBe("NOT_READY");
  empty.close();
  store.db.exec("DROP TABLE products");
  await request(app).get("/health/live").expect(200);
  await request(app).get("/health/ready").expect(503);
});
