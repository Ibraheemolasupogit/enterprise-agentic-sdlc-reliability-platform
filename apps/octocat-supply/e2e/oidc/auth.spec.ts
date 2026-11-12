import { test, expect, appOrigin } from "./fixtures";

test("P01/P11: code and PKCE reach authoritative cart pricing without persisted tokens", async ({
  page,
  simulated,
}) => {
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText("Signed in", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(appOrigin + "/");
  await page.getByRole("button", { name: "Add Demo Feeder" }).click();
  const qty = page.getByRole("spinbutton", {
    name: "Quantity for Demo Feeder",
  });
  await qty.fill("2");
  await page.getByRole("button", { name: "Update Demo Feeder" }).click();
  await page.getByRole("button", { name: "Add Demo Toy" }).click();
  await page
    .getByRole("spinbutton", { name: "Quantity for Demo Toy" })
    .fill("3");
  await page.getByRole("button", { name: "Update Demo Toy" }).click();
  await expect(page.getByTestId("total")).toHaveText("£287.96");
  expect((await simulated.stats()).proof).toEqual({
    s256: true,
    nonce: true,
    publicClient: true,
    verifier: true,
  });
  const storage = await page.evaluate(() => ({
    session: sessionStorage.length,
    keys: Object.keys(localStorage),
    values: Object.values(localStorage),
  }));
  expect(storage.session).toBe(0);
  expect(
    storage.keys.every((k) => /^morrow-oidc-cart:v2:[a-f0-9]{64}$/.test(k)),
  ).toBe(true);
  expect(storage.values.every((v) => /^[a-f0-9-]{36}$/.test(v))).toBe(true);
  expect((await simulated.stats()).statuses.some((s) => s.cookie)).toBe(false);
});

test("P03/P04/P05: denial and callback replay stay closed and leave clean URLs", async ({
  page,
  simulated,
}) => {
  await simulated.reset({ denial: "access_denied" });
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Sign-in could not be verified",
  );
  await expect(page).toHaveURL(appOrigin + "/");
  expect((await simulated.stats()).counts.token).toBe(0);
  await simulated.reset();
  let callback = "";
  page.on("request", (r) => {
    if (r.isNavigationRequest() && r.url().includes("/auth/callback?"))
      callback = r.url();
  });
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText("Signed in", { exact: true })).toBeVisible();
  await page.goto(callback);
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page).toHaveURL(appOrigin + "/");
  expect((await simulated.stats()).counts.token).toBe(1);
});

test("P11/P12: two independent tabs keep distinct owners and deny every cross-owner cart method", async ({
  page,
  browser,
  simulated,
}) => {
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("button", { name: "Add Demo Feeder" }).click();
  await expect(page.getByTestId("total")).toHaveText("£129.99");
  const cart = await page.evaluate(() => Object.values(localStorage)[0]);
  await simulated.options({ actor: "bob" });
  const other = await browser.newContext({ serviceWorkers: "block" });
  await simulated.route(other);
  const bob = await other.newPage();
  try {
    await bob.goto(appOrigin);
    await bob.getByRole("button", { name: "Sign in", exact: true }).click();
    await bob.getByRole("button", { name: "Add Demo Toy" }).click();
    await expect(bob.getByTestId("total")).toHaveText("£19.99");
    expect(await simulated.ownership(cart)).toEqual([404, 404, 404, 404]);
    const bobCart = await bob.evaluate(() => Object.values(localStorage)[0]);
    expect(await simulated.ownership(bobCart, "alice")).toEqual([
      404, 404, 404, 404,
    ]);
    await expect(page.getByTestId("total")).toHaveText("£129.99");
    await page.getByRole("button", { name: "Sign out locally" }).click();
    await expect(bob.getByText("Signed in", { exact: true })).toBeVisible();
  } finally {
    await other.close();
  }
});

test("P10: over-age API token requires explicit reauthentication without replaying a write", async ({
  page,
  simulated,
}) => {
  await simulated.reset({
    accessClaims: {
      iat: Math.floor(Date.now() / 1000) - 3606,
      exp: Math.floor(Date.now() / 1000) + 1800,
    },
  });
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("session expired");
  expect((await simulated.stats()).statuses.some((s) => s.status === 401)).toBe(
    true,
  );
  expect((await simulated.stats()).counts.token).toBe(1);
  await simulated.reset();
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("button", { name: "Add Demo Feeder" }).click();
  await expect(page.getByTestId("total")).toHaveText("£129.99");
});

test("P12: local logout and reload discard authority, then reauthentication restores only its owned basket", async ({
  page,
  simulated,
}) => {
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("button", { name: "Add Demo Feeder" }).click();
  await expect(page.getByTestId("total")).toHaveText("£129.99");
  await page.getByRole("button", { name: "Sign out locally" }).click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByTestId("total")).toHaveText("£129.99");
  expect((await simulated.stats()).counts.token).toBe(2);
});

test("P02/P06: hostile metadata and a signed wrong-audience ID token cannot open the shop", async ({
  page,
  simulated,
}) => {
  await simulated.reset({
    metadata: { token_endpoint: "https://foreign.example.test/token" },
  });
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  expect((await simulated.stats()).counts.token).toBe(0);
  for (const options of [
    { idClaims: { aud: "wrong-audience" } },
    { idClaims: { nonce: "wrong-nonce" } },
    { idClaims: { iss: "https://foreign.example.test" } },
    { badSignature: true },
  ]) {
    await simulated.reset(options);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    expect((await simulated.stats()).counts.token).toBe(1);
    expect((await simulated.stats()).statuses.length).toBe(0);
    await expect(
      page.getByRole("button", { name: "Add Demo Feeder" }),
    ).toHaveCount(0);
  }
});

test("P13: protected API redirects cannot dispatch a bearer to another origin", async ({
  page,
}) => {
  let foreign = 0;
  page.on("request", (r) => {
    if (new URL(r.url()).origin === "https://foreign.example.test") foreign++;
  });
  await page.goto(appOrigin);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Add Demo Feeder" }),
  ).toBeVisible();
  await page.route(appOrigin + "/api/products?**", (route) =>
    route.fulfill({
      status: 302,
      headers: { location: "https://foreign.example.test/api/products" },
    }),
  );
  await page.getByRole("searchbox", { name: "Search products" }).fill("feeder");
  await expect(page.getByRole("alert")).toContainText("could not be reached");
  expect(foreign).toBe(0);
  await expect(page.getByText("Signed in", { exact: true })).toBeVisible();
});
