import { randomUUID } from "node:crypto";
import express, { type ErrorRequestHandler } from "express";
import type { Repository } from "./repository.js";
import { anonymousAuthenticator, type Authenticate } from "./auth.js";
import { AppError, badInput, notFound } from "./errors.js";
import { validateQuantity } from "./pricing.js";

const categories = ["all", "feeding", "play", "everyday"];
function productId(value: unknown) {
  if (
    typeof value !== "string" ||
    !/^[1-9]\d*$/.test(value) ||
    !Number.isSafeInteger(Number(value))
  )
    badInput("Product ID must be a positive integer.");
  return Number(value);
}
function cartId(value: unknown): string {
  if (
    typeof value !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
      value,
    )
  )
    badInput("Cart ID is not valid.");
  return value;
}
function integerQuery(
  value: unknown,
  fallback: number,
  min: number,
  max: number,
) {
  if (value === undefined) return fallback;
  if (
    typeof value !== "string" ||
    !/^\d+$/.test(value) ||
    !Number.isSafeInteger(Number(value)) ||
    Number(value) < min ||
    Number(value) > max
  )
    badInput("Pagination is not valid.");
  return Number(value);
}

export function createApp(
  store: Repository,
  options: {
    log?: boolean;
    origins?: string[];
    authenticate?: Authenticate;
  } = {},
) {
  const app = express();
  app.disable("x-powered-by");
  app.set("trust proxy", false);
  const origins = options.origins ?? [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
  ];
  app.use((req, res, next) => {
    const requestId = randomUUID();
    res.locals.requestId = requestId;
    res.set({
      "X-Request-ID": requestId,
      "X-Content-Type-Options": "nosniff",
      "Cache-Control": "no-store",
    });
    req.setTimeout(5000);
    res.setTimeout(5000, () => {
      if (!res.headersSent)
        res.status(503).json({
          code: "REQUEST_TIMEOUT",
          message: "The request timed out.",
          requestId,
        });
    });
    const started = performance.now();
    if (options.log)
      res.on("finish", () =>
        console.log(
          JSON.stringify({
            requestId,
            method: req.method,
            route: req.route?.path ?? "unmatched",
            status: res.statusCode,
            durationMs: Math.round(performance.now() - started),
          }),
        ),
      );
    if (req.get("origin") && !origins.includes(req.get("origin")!))
      return next(
        new AppError(403, "ORIGIN_DENIED", "This origin is not allowed."),
      );
    next();
  });
  app.use(express.json({ limit: "16kb", strict: true, inflate: false }));
  app.use("/api", async (req, res, next) => {
    if (["POST", "PUT"].includes(req.method) && !req.is("application/json"))
      return next(
        new AppError(415, "UNSUPPORTED_MEDIA_TYPE", "Send application/json."),
      );
    res.locals.owner = await (options.authenticate ?? anonymousAuthenticator)(
      req.get("authorization"),
    );
    if (!(await store.ready()))
      return next(
        new AppError(503, "NOT_READY", "The demo database is not ready."),
      );
    next();
  });
  const respond = (res: express.Response, value: object, status = 200) =>
    res.status(status).json({ ...value, requestId: res.locals.requestId });
  app.get("/health/live", (_req, res) => respond(res, { status: "live" }));
  app.get("/health/ready", async (_req, res) => {
    const ready = await store.ready();
    respond(res, { status: ready ? "ready" : "not-ready" }, ready ? 200 : 503);
  });
  app.get("/api/products", async (req, res) => {
    if (
      Object.keys(req.query).some(
        (key) =>
          !["search", "category", "sort", "limit", "offset"].includes(key),
      )
    )
      badInput("Unknown product filter.");
    const search = req.query.search ?? "";
    const category = req.query.category ?? "all";
    const sort = req.query.sort ?? "name";
    if (
      typeof search !== "string" ||
      search.length > 100 ||
      typeof category !== "string" ||
      !categories.includes(category) ||
      !["name", "price"].includes(String(sort)) ||
      typeof sort !== "string"
    )
      badInput("Search, category or sort is not valid.");
    const limit = integerQuery(req.query.limit, 20, 1, 100);
    const offset = integerQuery(
      req.query.offset,
      0,
      0,
      Number.MAX_SAFE_INTEGER,
    );
    respond(
      res,
      await store.products(
        search.trim(),
        category,
        sort as "name" | "price",
        limit,
        offset,
      ),
    );
  });
  app.get("/api/products/:id", async (req, res) =>
    respond(res, await store.product(productId(req.params.id))),
  );
  app.post("/api/carts", async (req, res) => {
    if (
      req.body &&
      (Array.isArray(req.body) || Object.keys(req.body as object).length)
    )
      badInput("A new cart needs no fields.");
    respond(res, await store.createCart(res.locals.owner), 201);
  });
  app.get("/api/carts/:id", async (req, res) =>
    respond(res, await store.cart(cartId(req.params.id), res.locals.owner)),
  );
  app.delete("/api/carts/:id", async (req, res) => {
    await store.deleteCart(cartId(req.params.id), res.locals.owner);
    res.sendStatus(204);
  });
  app.put("/api/carts/:id/items/:productId", async (req, res) => {
    if (
      !req.body ||
      Array.isArray(req.body) ||
      Object.keys(req.body as object).length !== 1 ||
      !Object.hasOwn(req.body, "quantity")
    )
      badInput("Only quantity may be supplied.");
    respond(
      res,
      await store.setQuantity(
        cartId(req.params.id),
        productId(req.params.productId),
        validateQuantity(req.body.quantity),
        res.locals.owner,
      ),
    );
  });
  app.delete("/api/carts/:id/items/:productId", async (req, res) => {
    await store.removeItem(
      cartId(req.params.id),
      productId(req.params.productId),
      res.locals.owner,
    );
    res.sendStatus(204);
  });
  app.use((_req, _res) => notFound());
  const handleError: ErrorRequestHandler = (
    error: unknown,
    _req,
    res,
    _next,
  ) => {
    const parserStatus =
      typeof error === "object" && error && "status" in error
        ? error.status
        : undefined;
    const status =
      error instanceof AppError
        ? error.status
        : parserStatus === 413
          ? 413
          : parserStatus === 415
            ? 415
            : error instanceof SyntaxError
              ? 400
              : 500;
    const safeErrors: Record<number, [string, string]> = {
      400: ["INVALID_JSON", "JSON body is not valid."],
      413: ["BODY_TOO_LARGE", "Request body exceeds 16 KiB."],
      415: [
        "UNSUPPORTED_MEDIA_TYPE",
        "Use uncompressed UTF-8 application/json.",
      ],
      500: ["INTERNAL_ERROR", "The request could not be completed."],
    };
    const [code, message] =
      error instanceof AppError
        ? [error.code, error.message]
        : safeErrors[status];
    if (!res.headersSent)
      res
        .status(status)
        .json({ code, message, requestId: res.locals.requestId });
  };
  app.use(handleError);
  return app;
}
