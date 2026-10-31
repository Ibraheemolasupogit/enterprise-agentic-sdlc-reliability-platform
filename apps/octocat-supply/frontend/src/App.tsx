import { useEffect, useState, type FormEvent } from "react";
import {
  api,
  ApiError,
  money,
  type Cart,
  type Client,
  type Product,
} from "./api";
import "./styles.css";

function savedCart(storageKey: string) {
  try {
    return localStorage.getItem(storageKey);
  } catch {
    return null;
  }
}
function remember(storageKey: string, id: string | null) {
  try {
    if (id) localStorage.setItem(storageKey, id);
    else localStorage.removeItem(storageKey);
  } catch {
    /* In-memory shopping still works with storage disabled. */
  }
}
function errorText(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

function ProductArt({ id }: { id: number }) {
  // Original geometric illustrations; no downloaded images, fonts or brand assets.
  return (
    <svg
      viewBox="0 0 240 170"
      aria-hidden="true"
      className={`product-art art-${id % 3}`}
    >
      <ellipse cx="120" cy="143" rx="66" ry="9" className="shadow" />
      {id % 3 === 1 ? (
        <>
          <path
            d="M87 53 Q87 29 120 29 Q153 29 153 53 L160 116 Q158 132 120 132 Q82 132 80 116Z"
            className="object"
          />
          <ellipse cx="120" cy="58" rx="31" ry="12" className="highlight" />
          <path d="M94 105 Q120 116 146 105" className="line" />
          <circle cx="120" cy="85" r="5" className="detail" />
        </>
      ) : id % 3 === 2 ? (
        <>
          <circle cx="107" cy="85" r="42" className="object" />
          <circle cx="137" cy="102" r="31" className="highlight" />
          <path
            d="M78 58 Q108 77 111 111 M111 43 Q92 83 68 91"
            className="line"
          />
          <circle cx="155" cy="51" r="10" className="detail" />
        </>
      ) : (
        <>
          <path
            d="M67 103 Q74 64 120 64 Q166 64 173 103 L162 130 L78 130Z"
            className="object"
          />
          <ellipse cx="120" cy="96" rx="44" ry="20" className="highlight" />
          <path d="M88 100 Q120 115 152 100" className="line" />
          <path d="M113 45 L120 33 L127 45" className="line" />
        </>
      )}
    </svg>
  );
}

function BasketLine({
  item,
  busy,
  onUpdate,
  onRemove,
}: {
  item: Cart["items"][number];
  busy: boolean;
  onUpdate: (quantity: number) => void;
  onRemove: () => void;
}) {
  const [draft, setDraft] = useState(String(item.quantity));
  const [invalid, setInvalid] = useState(false);
  useEffect(() => setDraft(String(item.quantity)), [item.quantity]);
  function submit(event: FormEvent) {
    event.preventDefault();
    const quantity = Number(draft);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    onUpdate(quantity);
  }
  return (
    <li className="basket-line">
      <div className="line-heading">
        <strong>{item.name}</strong>
        <span>{money(item.lineTotalMinor)}</span>
      </div>
      <small>{money(item.unitPriceMinor)} each</small>
      <form onSubmit={submit} noValidate className="quantity-form">
        <label>
          Qty{" "}
          <input
            aria-label={`Quantity for ${item.name}`}
            type="number"
            min="1"
            max="99"
            step="1"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={busy}
          />
        </label>
        <button
          type="submit"
          className="text-button"
          disabled={busy}
          aria-label={`Update ${item.name}`}
        >
          Update
        </button>
        <button
          type="button"
          className="text-button remove"
          disabled={busy}
          onClick={onRemove}
          aria-label={`Remove ${item.name}`}
        >
          Remove
        </button>
      </form>
      {invalid && (
        <p role="alert" className="error">
          Use a whole quantity from 1 to 99.
        </p>
      )}
    </li>
  );
}

export default function App({
  client = api,
  storageKey = "morrow-demo-cart",
}: {
  client?: Client;
  storageKey?: string;
}) {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState("name");
  const [loading, setLoading] = useState(true);
  const [catalogError, setCatalogError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [cart, setCart] = useState<Cart | null>(null);
  const [busy, setBusy] = useState(false);
  const [cartLoading, setCartLoading] = useState(() =>
    Boolean(savedCart(storageKey)),
  );
  const [restoreFailed, setRestoreFailed] = useState(false);
  const [stale, setStale] = useState(false);
  const [basketError, setBasketError] = useState("");
  const [announcement, setAnnouncement] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setCatalogError("");
    client
      .products(search, category, sort, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setProducts(result.items);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setCatalogError(errorText(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [client, search, category, sort, refresh]);

  useEffect(() => {
    const id = savedCart(storageKey);
    if (!id) return;
    let active = true;
    client
      .cart(id)
      .then((result) => {
        if (active) setCart(result);
      })
      .catch((error) => {
        if (!active) return;
        if (error instanceof ApiError && [400, 404].includes(error.status)) {
          setStale(true);
          remember(storageKey, null);
        } else {
          setRestoreFailed(true);
          setBasketError(errorText(error));
        }
      })
      .finally(() => {
        if (active) setCartLoading(false);
      });
    return () => {
      active = false;
    };
  }, [client, storageKey]);

  async function change(
    action: (current: Cart) => Promise<Cart>,
    message: string,
  ) {
    setBusy(true);
    setBasketError("");
    try {
      const current = cart ?? (await client.createCart());
      remember(storageKey, current.id);
      setCart(current);
      const updated = await action(current);
      setCart(updated);
      setAnnouncement(message);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        remember(storageKey, null);
        setCart(null);
        setStale(true);
      } else setBasketError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function retrySavedBasket() {
    const id = savedCart(storageKey);
    if (!id) return;
    setCartLoading(true);
    setBasketError("");
    try {
      setCart(await client.cart(id));
      setRestoreFailed(false);
    } catch (error) {
      if (error instanceof ApiError && [400, 404].includes(error.status)) {
        remember(storageKey, null);
        setStale(true);
        setRestoreFailed(false);
      } else setBasketError(errorText(error));
    } finally {
      setCartLoading(false);
    }
  }
  const disabled = busy || cartLoading || stale || restoreFailed;
  const count = cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0;

  return (
    <>
      <a className="skip-link" href="#collection">
        Skip to collection
      </a>
      <header className="site-header">
        <a className="brand" href="/" aria-label="Morrow Supply home">
          <span className="brand-mark" aria-hidden="true">
            m
          </span>
          <span>
            morrow<span className="brand-subtitle">SUPPLY</span>
          </span>
        </a>
        <span className="header-note">SMALL THINGS. GOOD DAYS.</span>
        <a href="#basket" className="basket-link">
          Basket <span>{count}</span>
        </a>
      </header>
      <main>
        <section className="intro">
          <div>
            <p className="eyebrow">THE EVERYDAY COLLECTION · 01</p>
            <h1>
              A little more play.
              <br />
              <span>A little less ordinary.</span>
            </h1>
            <p className="intro-copy">
              Thoughtful little essentials for curious companions.
              <br />
              Explore our original, synthetic demo collection.
            </p>
          </div>
          <div className="offer">
            <span className="offer-symbol" aria-hidden="true">
              ✳
            </span>
            <p>A little extra, on us.</p>
            <strong>10% off baskets £300+</strong>
            <small>Applied automatically. Prices in GBP.</small>
          </div>
        </section>
        <div className="shop-layout">
          <section id="collection" aria-labelledby="collection-title">
            <div className="section-heading">
              <h2 id="collection-title">Find your everyday</h2>
              <span className="collection-count">
                12 ORIGINAL DEMO PRODUCTS
              </span>
            </div>
            <div className="toolbar">
              <label className="search-label">
                <span className="sr-only">Search products</span>
                <input
                  type="search"
                  placeholder="Find something good…"
                  maxLength={100}
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
              <label className="sort-label">
                Sort{" "}
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                >
                  <option value="name">Name</option>
                  <option value="price">Price: low to high</option>
                </select>
              </label>
            </div>
            <div className="filters" aria-label="Product categories">
              {[
                ["all", "All things"],
                ["feeding", "Feeding"],
                ["play", "Play"],
                ["everyday", "Everyday"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  aria-pressed={category === value}
                  onClick={() => setCategory(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            {loading ? (
              <p role="status" className="empty-state">
                Gathering the collection…
              </p>
            ) : catalogError ? (
              <div className="empty-state">
                <p role="alert" className="error">
                  {catalogError}
                </p>
                <button onClick={() => setRefresh((value) => value + 1)}>
                  Try again
                </button>
              </div>
            ) : products.length === 0 ? (
              <p role="status" className="empty-state">
                No matches yet. Try another search or category.
              </p>
            ) : (
              <div className="product-grid">
                {products.map((product) => (
                  <article className="product-card" key={product.id}>
                    <div className="art-panel">
                      <span className="product-number">
                        NO. {String(product.id).padStart(2, "0")}
                      </span>
                      <ProductArt id={product.id} />
                    </div>
                    <div className="product-meta">
                      <p>{product.category}</p>
                      <h3>{product.name}</h3>
                      <div className="product-bottom">
                        <strong>{money(product.unitPriceMinor)}</strong>
                        <button
                          disabled={
                            disabled ||
                            Boolean(
                              cart?.items.some(
                                (item) =>
                                  item.productId === product.id &&
                                  item.quantity >= 99,
                              ),
                            )
                          }
                          onClick={() =>
                            void change(
                              (current) =>
                                client.setQuantity(
                                  current.id,
                                  product.id,
                                  Math.min(
                                    99,
                                    (current.items.find(
                                      (item) => item.productId === product.id,
                                    )?.quantity ?? 0) + 1,
                                  ),
                                ),
                              `${product.name} added to your basket.`,
                            )
                          }
                          aria-label={`Add ${product.name}`}
                        >
                          Add <span aria-hidden="true">↗</span>
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
          <aside id="basket" className="basket" aria-labelledby="basket-title">
            <div className="basket-heading">
              <h2 id="basket-title">Your basket</h2>
              <span>
                {count} {count === 1 ? "item" : "items"}
              </span>
            </div>
            {cartLoading && <p role="status">Restoring your basket…</p>}
            {restoreFailed && (
              <button
                disabled={cartLoading}
                onClick={() => void retrySavedBasket()}
              >
                Retry saved basket
              </button>
            )}
            {stale && (
              <div>
                <p role="alert">
                  Your saved basket was reset. Start a new basket to continue.
                </p>
                <button
                  onClick={() => {
                    setStale(false);
                    setBasketError("");
                  }}
                >
                  Start a new basket
                </button>
              </div>
            )}
            {basketError && (
              <p role="alert" className="error">
                {basketError}
              </p>
            )}
            {!cart?.items.length ? (
              <div className="basket-empty">
                <span aria-hidden="true">⌑</span>
                <p>Good things start small.</p>
                <small>Add a favourite from the collection.</small>
              </div>
            ) : (
              <ul className="basket-items">
                {cart.items.map((item) => (
                  <BasketLine
                    key={item.productId}
                    item={item}
                    busy={disabled}
                    onUpdate={(quantity) =>
                      void change(
                        (current) =>
                          client.setQuantity(
                            current.id,
                            item.productId,
                            quantity,
                          ),
                        "Basket updated.",
                      )
                    }
                    onRemove={() =>
                      void change(async (current) => {
                        await client.remove(current.id, item.productId);
                        return client.cart(current.id);
                      }, "Item removed.")
                    }
                  />
                ))}
              </ul>
            )}
            <dl className="totals">
              <div>
                <dt>Subtotal</dt>
                <dd data-testid="subtotal">
                  {money(cart?.subtotalMinor ?? 0)}
                </dd>
              </div>
              <div className="discount">
                <dt>Basket offer {cart?.discountMinor ? "(10%)" : ""}</dt>
                <dd data-testid="discount">
                  −{money(cart?.discountMinor ?? 0)}
                </dd>
              </div>
              <div className="grand-total">
                <dt>Total</dt>
                <dd data-testid="total">{money(cart?.totalMinor ?? 0)}</dd>
              </div>
            </dl>
            <p className="basket-caption">
              A demo basket, made for exploring.
              <br />
              No checkout, payments or personal details.
            </p>
            <button
              className="text-button refresh-basket"
              disabled={disabled || !cart}
              onClick={() =>
                void change(
                  (current) => client.cart(current.id),
                  "Basket refreshed.",
                )
              }
            >
              Refresh basket
            </button>
          </aside>
        </div>
        <p role="status" aria-live="polite" className="sr-only">
          {announcement}
        </p>
      </main>
      <footer className="site-footer">
        <span>morrow supply</span>
        <p>
          Original illustrations. Synthetic products. Everyday possibilities.
        </p>
        <small>© 2026 Morrow Supply demo contributors</small>
      </footer>
    </>
  );
}
