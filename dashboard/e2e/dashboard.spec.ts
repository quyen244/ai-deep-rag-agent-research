import { expect, test } from "@playwright/test";

test("submits a multi-ticker request against the FastAPI contract fixture", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel(/Research request/i).fill("Analyze AAPL and TSLA");
  await page.getByRole("button", { name: "Analyze" }).click();

  await expect(page.getByRole("heading", { name: "Research brief" })).toBeVisible();
  await page.getByRole("tab", { name: "Comparison" }).click();
  await expect(page.getByRole("table")).toContainText("Price to earnings");
  await expect(page.getByText("Preferred", { exact: true })).toBeVisible();
});

test("keeps navigation usable in a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByLabel(/Research request/i).fill("Analyze AAPL and TSLA");
  await page.getByRole("button", { name: "Analyze" }).click();

  await page.getByRole("tab", { name: "Technical" }).click();
  await expect(page.getByRole("heading", { name: "Technical", exact: true })).toBeVisible();
});
