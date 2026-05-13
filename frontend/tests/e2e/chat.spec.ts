import { test, expect } from "@playwright/test";
import { makeDailyBars, makeSnapshot, ssePayload } from "./fixtures";

test("happy path: chat streams a reply and chart loads with mocked APIs", async ({ page }) => {
  // --- Suppress the live WebSocket so the test is hermetic. ---
  await page.route("**/ws/**", (route) => route.abort());
  await page.route("**/ws", (route) => route.abort());

  // --- Market clock (the backend route is /api/v1/market/clock; ** matches both). ---
  await page.route("**/api/v1/**clock", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        is_open: true,
        next_open: "2026-05-14T13:30:00Z",
        next_close: "2026-05-13T20:00:00Z",
      }),
    });
  });

  // --- Watchlists ---
  await page.route("**/api/v1/watchlists", async (route) => {
    if (route.request().method() !== "GET") return route.continue();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        watchlists: [{ name: "Default", symbols: ["AAPL", "MSFT"] }],
      }),
    });
  });

  // --- Bars ---
  await page.route("**/api/v1/market/bars*", async (route) => {
    const url = new URL(route.request().url());
    const symbol = url.searchParams.get("symbol") ?? "AAPL";
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(makeDailyBars(symbol, 30)),
    });
  });

  // --- Snapshot (AAPL specifically, plus any other symbol just in case) ---
  await page.route("**/api/v1/market/snapshot/*", async (route) => {
    const parts = route.request().url().split("/");
    const symbol = parts[parts.length - 1] ?? "AAPL";
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(makeSnapshot(symbol)),
    });
  });

  // --- Reports ---
  await page.route("**/api/v1/reports", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reports: [] }),
    });
  });

  // --- SSE chat stream ---
  // Playwright's fulfill() doesn't actually stream chunks, but the frontend
  // SSE parser reads from the response body and splits on `\n\n` frames, so
  // delivering the full body at once with content-type: text/event-stream
  // is sufficient for the parser to emit each frame as an event.
  await page.route("**/api/v1/chat", async (route) => {
    const body = ssePayload([
      { type: "token", text: "Hello " },
      { type: "token", text: "world." },
      { type: "done" },
    ]);
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: {
        "cache-control": "no-cache",
        connection: "keep-alive",
      },
      body,
    });
  });

  await page.goto("/");

  await expect(page.getByText("grok-alpaca")).toBeVisible();

  const input = page.getByPlaceholder(/Ask Grok/i);
  await input.fill("say hi");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText(/Hello world/i)).toBeVisible({ timeout: 10_000 });
});
