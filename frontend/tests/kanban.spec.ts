import { expect, test, type Page } from "@playwright/test";

// Board fixture matching initialData from kanban.ts
const INITIAL_BOARD = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": { id: "card-1", title: "Align roadmap themes", details: "Draft quarterly themes with impact statements and metrics." },
    "card-2": { id: "card-2", title: "Gather customer signals", details: "Review support tags, sales notes, and churn feedback." },
    "card-3": { id: "card-3", title: "Prototype analytics view", details: "Sketch initial dashboard layout and key drill-downs." },
    "card-4": { id: "card-4", title: "Refine status language", details: "Standardize column labels and tone across the board." },
    "card-5": { id: "card-5", title: "Design card layout", details: "Add hierarchy and spacing for scanning dense lists." },
    "card-6": { id: "card-6", title: "QA micro-interactions", details: "Verify hover, focus, and loading states." },
    "card-7": { id: "card-7", title: "Ship marketing page", details: "Final copy approved and asset pack delivered." },
    "card-8": { id: "card-8", title: "Close onboarding sprint", details: "Document release notes and share internally." },
  },
};

async function mockApi(page: Page) {
  let board = structuredClone(INITIAL_BOARD);

  await page.route("/api/auth/me", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ username: "user" }) })
  );

  await page.route("/api/auth/login", (route) => {
    const req = route.request();
    if (req.method() === "POST") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
    } else {
      route.continue();
    }
  });

  await page.route("/api/auth/logout", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) })
  );

  await page.route("/api/board", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(board) });
    } else if (route.request().method() === "PUT") {
      const data = route.request().postDataJSON() as typeof board;
      board = data;
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
    } else {
      route.continue();
    }
  });
}

test("loads the kanban board", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("adds a card to the Discovery column", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  const discoveryColumn = page.getByTestId("column-col-discovery");
  await discoveryColumn.getByRole("button", { name: /add a card/i }).click();
  await discoveryColumn.getByPlaceholder("Card title").fill("Discovery test card");
  await discoveryColumn.getByRole("button", { name: /add card/i }).click();
  await expect(discoveryColumn.getByText("Discovery test card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("auth: unauthenticated user is redirected to login", async ({ page }) => {
  await page.route("/api/auth/me", (route) =>
    route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Not authenticated" }) })
  );

  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
});

test("auth: login form signs in and redirects to board", async ({ page }) => {
  // First visit to / redirects to login (not authenticated yet)
  let authenticated = false;
  await page.route("/api/auth/me", (route) => {
    route.fulfill({
      status: authenticated ? 200 : 401,
      contentType: "application/json",
      body: JSON.stringify(authenticated ? { username: "user" } : { detail: "Not authenticated" }),
    });
  });
  await page.route("/api/auth/login", (route) => {
    authenticated = true;
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });
  await page.route("/api/board", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(INITIAL_BOARD) })
  );

  await page.goto("/login");
  await page.fill('[name="username"]', "user");
  await page.fill('[name="password"]', "password");
  await page.click('[type="submit"]');

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
});
