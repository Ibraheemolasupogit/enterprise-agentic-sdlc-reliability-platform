import type { Store } from "./database.js";

type Result<K extends keyof Store> = Store[K] extends (
  ...args: never[]
) => infer R
  ? R
  : never;
type Maybe<T> = T | Promise<T>;
export type Cart = Result<"cart">;
export interface Repository {
  ready(): Maybe<boolean>;
  products(
    search: string,
    category: string,
    sort: "name" | "price",
    limit: number,
    offset: number,
  ): Maybe<Result<"products">>;
  product(id: number): Maybe<Result<"product">>;
  createCart(owner?: string): Maybe<Cart>;
  cart(id: string, owner?: string): Maybe<Cart>;
  setQuantity(
    cartId: string,
    productId: number,
    quantity: number,
    owner?: string,
  ): Maybe<Cart>;
  removeItem(cartId: string, productId: number, owner?: string): Maybe<void>;
  deleteCart(id: string, owner?: string): Maybe<void>;
  close(): Maybe<void>;
}
