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
export type SessionRequest = {
  token: string;
  signal: AbortSignal;
  check(): void;
  unauthorized(): void;
};

export function protectedApiPath(path: string) {
  if (
    !path.startsWith("/api/") ||
    !new URL(path, location.origin).pathname.startsWith("/api/")
  )
    throw new ApiError("The API destination is not allowed.", 0);
  return path;
}

export function createClient(
  tokenProvider: () => Promise<string | undefined> = async () => undefined,
  session?: () => SessionRequest,
) {
  async function request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    if (session) protectedApiPath(path);
    const lease = session?.();
    const token = lease ? lease.token : await tokenProvider();
    lease?.check();
    const signal = lease
      ? AbortSignal.any([
          lease.signal,
          AbortSignal.timeout(6000),
          ...(options.signal ? [options.signal] : []),
        ])
      : (options.signal ?? AbortSignal.timeout(6000));
    let response: Response;
    try {
      response = await fetch(path, {
        ...options,
        signal,
        ...(lease
          ? { redirect: "error" as const, credentials: "omit" as const }
          : {}),
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      lease?.check();
    } catch (error) {
      lease?.check();
      if (options.signal?.aborted) throw error;
      throw new ApiError("The shop could not be reached. Please try again.", 0);
    }
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as {
        message?: string;
        requestId?: string;
      };
      lease?.check();
      if (response.status === 401) lease?.unauthorized();
      throw new ApiError(
        lease
          ? response.status === 401
            ? "Your session expired. Sign in again."
            : response.status === 403
              ? "Your account does not have permission."
              : "The shop could not complete this request. Please try again."
          : (body.message ?? "The shop could not complete this request."),
        response.status,
        lease && !/^[a-f0-9-]{36}$/i.test(body.requestId ?? "")
          ? undefined
          : body.requestId,
      );
    }
    const result = response.status === 204 ? undefined : await response.json();
    lease?.check();
    return result as T;
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
      request<Cart>(`/api/carts/${encodeURIComponent(id)}/items/${productId}`, {
        method: "PUT",
        body: JSON.stringify({ quantity }),
      }),
    remove: (id: string, productId: number) =>
      request<void>(`/api/carts/${encodeURIComponent(id)}/items/${productId}`, {
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
