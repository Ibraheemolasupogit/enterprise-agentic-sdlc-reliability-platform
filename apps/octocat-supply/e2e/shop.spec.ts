import { expect, test } from "@playwright/test";

test("catalogue → search/filter → cart → discount → refresh → update/remove", async ({
  page,
  request,
}) => {
  const unexpected: string[] = [];
  page.on("request", (req) => {
    if (
      !req.url().startsWith(test.info().project.use.baseURL as string) &&
      !req.url().startsWith("data:")
    )
      unexpected.push(req.url());
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Demo Feeder", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(12);
  await page.screenshot({
    path: "test-results/morrow-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("searchbox", { name: "Search products" })
    .fill(" FEEDER ");
  await expect(page.getByRole("article")).toHaveCount(1);
  await page.getByRole("button", { name: "Add Demo Feeder" }).click();
  await expect(page.getByTestId("total")).toHaveText("£129.99");
  await page
    .getByRole("spinbutton", { name: "Quantity for Demo Feeder" })
    .fill("2");
  await page.getByRole("button", { name: "Update Demo Feeder" }).click();
  await expect(page.getByTestId("subtotal")).toHaveText("£259.98");
  await page.getByRole("searchbox").fill("");
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await expect(page.getByRole("article")).toHaveCount(1);
  await page.getByRole("button", { name: "Add Demo Toy" }).click();
  await page
    .getByRole("spinbutton", { name: "Quantity for Demo Toy" })
    .fill("3");
  await page.getByRole("button", { name: "Update Demo Toy" }).click();
  await expect(page.getByTestId("subtotal")).toHaveText("£319.95");
  await expect(page.getByTestId("discount")).toHaveText("−£31.99");
  await expect(page.getByTestId("total")).toHaveText("£287.96");
  await page.reload();
  await expect(page.getByTestId("total")).toHaveText("£287.96");
  await page.getByRole("button", { name: "Remove Demo Feeder" }).click();
  await expect(page.getByTestId("total")).toHaveText("£59.97");
  await page.getByRole("button", { name: "Remove Demo Toy" }).click();
  await expect(page.getByTestId("total")).toHaveText("£0.00");
  await page.getByRole("searchbox").fill("nothing matches");
  await expect(page.getByText(/No matches yet/)).toBeVisible();
  expect(unexpected).toEqual([]);
  const id = await page.evaluate(() =>
    localStorage.getItem("morrow-demo-cart"),
  );
  expect((await request.delete(`/api/carts/${id}`)).status()).toBe(204);
});

test("shows a dependency error and recovers on retry", async ({ page }) => {
  await page.route("**/api/products?*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "The shop is temporarily unavailable." }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await page.unroute("**/api/products?*");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByRole("article")).toHaveCount(12);
});

test("keeps the collection and basket usable on a narrow screen", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("article")).toHaveCount(12);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("searchbox").focus();
  await page.keyboard.type("Feeder");
  await expect(page.getByRole("article")).toHaveCount(1);
  await expect(
    page.getByRole("heading", { name: "Your basket" }),
  ).toBeAttached();
  await page.screenshot({
    path: "test-results/morrow-mobile.png",
    fullPage: true,
  });
});
