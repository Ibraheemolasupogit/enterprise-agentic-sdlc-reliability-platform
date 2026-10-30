import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { ApiError, type Cart, type Client } from "../src/api";

const product = {
  id: 1,
  name: "Demo Feeder",
  unitPriceMinor: 12999,
  category: "feeding",
  currency: "GBP" as const,
};
const empty: Cart = {
  id: "c18eb8c7-276c-4330-83fe-e842c7e5fb2e",
  items: [],
  subtotalMinor: 0,
  discountMinor: 0,
  totalMinor: 0,
  currency: "GBP",
  discountLabel: null,
};
function client(overrides: Partial<Client> = {}): Client {
  return {
    products: vi.fn().mockResolvedValue({ items: [product], total: 1 }),
    cart: vi.fn().mockResolvedValue(empty),
    createCart: vi.fn().mockResolvedValue(empty),
    setQuantity: vi.fn().mockResolvedValue({
      ...empty,
      items: [
        {
          productId: 1,
          name: product.name,
          quantity: 1,
          unitPriceMinor: 12999,
          lineTotalMinor: 12999,
        },
      ],
      subtotalMinor: 12999,
      totalMinor: 12999,
    }),
    remove: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

describe("collection and accessible basket states", () => {
  it("preserves the saved basket during an outage and retries without creating a replacement", async () => {
    localStorage.setItem("morrow-demo-cart", empty.id);
    const service = client({
      cart: vi
        .fn()
        .mockRejectedValueOnce(new ApiError("Unavailable", 503))
        .mockResolvedValue(empty),
    });
    render(<App client={service} />);
    await screen.findByRole("button", { name: "Retry saved basket" });
    expect(
      screen.getByRole("button", { name: "Add Demo Feeder" }),
    ).toBeDisabled();
    expect(localStorage.getItem("morrow-demo-cart")).toBe(empty.id);
    await userEvent.click(
      screen.getByRole("button", { name: "Retry saved basket" }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Add Demo Feeder" }),
      ).toBeEnabled(),
    );
    expect(service.createCart).not.toHaveBeenCalled();
  });
  it("announces loading and renders a keyboard-operable search/category flow", async () => {
    let resolve: (value: {
      items: (typeof product)[];
      total: number;
    }) => void = () => {};
    const products = vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise((done) => {
            resolve = done;
          }),
      )
      .mockResolvedValue({ items: [], total: 0 });
    render(<App client={client({ products })} />);
    expect(screen.getByText("Gathering the collection…")).toBeInTheDocument();
    resolve({ items: [product], total: 1 });
    await screen.findByRole("button", { name: "Add Demo Feeder" });
    const user = userEvent.setup();
    const search = screen.getByRole("searchbox", { name: "Search products" });
    await user.click(search);
    await user.keyboard("missing");
    await screen.findByText(/No matches yet/);
    await user.click(screen.getByRole("button", { name: "Play" }));
    expect(products).toHaveBeenLastCalledWith(
      "missing",
      "play",
      "name",
      expect.any(AbortSignal),
    );
  });
  it("shows an API error and can retry without reloading the page", async () => {
    const products = vi
      .fn()
      .mockRejectedValueOnce(new Error("The shop is temporarily unavailable."))
      .mockResolvedValue({ items: [product], total: 1 });
    render(<App client={client({ products })} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "temporarily unavailable",
    );
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByRole("button", { name: "Add Demo Feeder" }),
    ).toBeEnabled();
  });
  it("uses canonical server totals, validates quantity, updates/removes and remembers the cart", async () => {
    const service = client();
    render(<App client={service} />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Add Demo Feeder" }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("total")).toHaveTextContent("£129.99"),
    );
    expect(localStorage.getItem("morrow-demo-cart")).toBe(empty.id);
    const quantity = screen.getByRole("spinbutton", {
      name: "Quantity for Demo Feeder",
    });
    fireEvent.change(quantity, { target: { value: "0" } });
    await userEvent.click(
      screen.getByRole("button", { name: "Update Demo Feeder" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "whole quantity",
    );
    expect(service.setQuantity).toHaveBeenCalledTimes(1);
    fireEvent.change(quantity, { target: { value: "2" } });
    await userEvent.click(
      screen.getByRole("button", { name: "Update Demo Feeder" }),
    );
    expect(service.setQuantity).toHaveBeenLastCalledWith(empty.id, 1, 2);
    await userEvent.click(
      screen.getByRole("button", { name: "Remove Demo Feeder" }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("total")).toHaveTextContent("£0.00"),
    );
  });
  it("restores an existing basket and requires explicit recovery from a reset/stale cart", async () => {
    localStorage.setItem("morrow-demo-cart", empty.id);
    render(
      <App
        client={client({
          cart: vi.fn().mockRejectedValue(new ApiError("Missing.", 404)),
        })}
      />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "saved basket was reset",
    );
    expect(
      screen.getByRole("button", { name: "Add Demo Feeder" }),
    ).toBeDisabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Start a new basket" }),
    );
    expect(
      screen.getByRole("button", { name: "Add Demo Feeder" }),
    ).toBeEnabled();
    expect(localStorage.getItem("morrow-demo-cart")).toBeNull();
  });
  it("ignores out-of-order aborted catalogue results", async () => {
    let old: (value: {
      items: (typeof product)[];
      total: number;
    }) => void = () => {};
    const products = vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise((done) => {
            old = done;
          }),
      )
      .mockResolvedValue({ items: [], total: 0 });
    render(<App client={client({ products })} />);
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "new" },
    });
    await screen.findByText(/No matches yet/);
    old({ items: [product], total: 1 });
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Add Demo Feeder" }),
      ).not.toBeInTheDocument(),
    );
  });
});
