// Captures README screenshots against the running app (frontend :5173 + backend :8000, seeded).
// Run from frontend/:  node scripts/screenshots.mjs
import { mkdirSync } from "node:fs"

import { chromium } from "@playwright/test"

const BASE = "http://localhost:5173"
const OUT = "../docs/screenshots"
mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch()
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
})
const page = await ctx.newPage()

async function shot(name, opts = {}) {
  await page.waitForTimeout(1200)
  await page.screenshot({ path: `${OUT}/${name}.png`, ...opts })
  console.log("saved", name)
}

await page.goto(`${BASE}/login`)
await shot("login")

await page.getByPlaceholder("Email").fill("owner@pulsedemo.com")
await page.getByPlaceholder(/Password/).fill("password123")
await page.getByRole("button", { name: /^sign in$/i }).click()
await page.getByRole("heading", { name: "Monitors" }).waitFor({ timeout: 15000 })
await shot("dashboard", { fullPage: true })

await page.getByText("API", { exact: true }).first().click()
await page.getByRole("heading", { level: 1 }).waitFor()
await shot("monitor-detail", { fullPage: true })

await page.getByRole("link", { name: "Incidents" }).click()
await page.getByRole("heading", { name: "Incidents" }).waitFor()
await shot("incidents", { fullPage: true })

await page.getByRole("link", { name: "Billing" }).click()
await page.getByRole("heading", { name: "Billing" }).waitFor()
await shot("billing", { fullPage: true })

await page.goto(`${BASE}/status/demo`)
await shot("status", { fullPage: true })

await browser.close()
console.log("done")
