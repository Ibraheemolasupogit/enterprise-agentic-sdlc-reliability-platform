export type Product = {
  id: number;
  name: string;
  unitPriceMinor: number;
  category: string;
  currency: "GBP";
};
export type Cart = {
  id: string;
  items: {
    productId: number;
    name: string;
    quantity: number;
    unitPriceMinor: number;
    lineTotalMinor: number;
  }[];
  subtotalMinor: number;
  discountMinor: number;
  totalMinor: number;
  discountLabel: string | null;
  currency: "GBP";
};
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public requestId?: string,
  ) {
    super(message);
  }
}
export function createClient(
  tokenProvider: () => Promise<string | undefined> = async () => undefined,
) {
  async function request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const token = await tokenProvider();
    let response: Response;
    try {
      response = await fetch(path, {
        ...options,
        signal: options.signal ?? AbortSignal.timeout(6000),
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
    } catch (error) {
      if (options.signal?.aborted) throw error;
      throw new ApiError("The shop could not be reached. Please try again.", 0);
    }
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as {
        message?: string;
        requestId?: string;
      };
      throw new ApiError(
        body.message ?? "The shop could not complete this request.",
        response.status,
        body.requestId,
      );
    }
    return response.status === 204
      ? (undefined as T)
      : (response.json() as Promise<T>);
  }
  return {
    products: (
      search: string,
      category: string,
      sort: string,
      signal?: AbortSignal,
    ) =>
      request<{ items: Product[]; total: number }>(
        `/api/products?${new URLSearchParams({ search, category, sort })}`,
        { signal },
      ),
    cart: (id: string) => request<Cart>(`/api/carts/${encodeURIComponent(id)}`),
    createCart: () =>
      request<Cart>("/api/carts", { method: "POST", body: "{}" }),
    setQuantity: (id: string, productId: number, quantity: number) =>
      request<Cart>(`/api/carts/${id}/items/${productId}`, {
        method: "PUT",
        body: JSON.stringify({ quantity }),
      }),
    remove: (id: string, productId: number) =>
      request<void>(`/api/carts/${id}/items/${productId}`, {
        method: "DELETE",
      }),
  };
}
export const api = createClient();
export type Client = typeof api;
export const money = (minor: number) =>
  new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(
    minor / 100,
  );
