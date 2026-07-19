import { expect, test } from "@playwright/test"

// Happy path: sign up, add an HTTP monitor, see it on the dashboard.
test("signup then add a monitor", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`

  await page.goto("/signup")
  await page.getByPlaceholder("Email").fill(email)
  await page.getByPlaceholder(/Password/).fill("password123")
  await page.getByRole("button", { name: /create account/i }).click()

  await expect(page.getByRole("heading", { name: "Monitors" })).toBeVisible()

  await page.getByPlaceholder("Name").fill("My Site")
  await page.getByPlaceholder("https://example.com").fill("https://example.com")
  await page.getByRole("button", { name: /add monitor/i }).click()

  await expect(page.getByText("My Site")).toBeVisible()
})
