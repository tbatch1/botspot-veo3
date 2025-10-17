import { test, expect } from '@playwright/test';

test.describe('Video Generation Flow', () => {
  test('should load homepage with hero section', async ({ page }) => {
    await page.goto('/');

    // Check hero section
    await expect(page.getByText('Botspot')).toBeVisible();
    await expect(page.getByText('AI Trading Bot')).toBeVisible();
    await expect(page.getByText('Demo Videos')).toBeVisible();

    // Check stats are visible
    await expect(page.getByText(/Videos Generated/i)).toBeVisible();
    await expect(page.getByText(/Active Bots/i)).toBeVisible();
  });

  test('should show video generation studio', async ({ page }) => {
    await page.goto('/');

    // Check studio panels
    await expect(page.getByText('Prompt Builder')).toBeVisible();
    await expect(page.getByText('Preview Canvas')).toBeVisible();
    await expect(page.getByText('Configuration')).toBeVisible();
  });

  test('should allow template selection', async ({ page }) => {
    await page.goto('/');

    // Click a template
    const template = page.getByText('Bull Market Breakout').first();
    await template.click();

    // Check prompt is populated
    const promptInput = page.getByPlaceholder(/Describe the trading bot/i);
    await expect(promptInput).not.toBeEmpty();
  });

  test('should show cost calculator', async ({ page }) => {
    await page.goto('/');

    // Check cost estimate is visible
    await expect(page.getByText(/Estimated Cost/i)).toBeVisible();
    await expect(page.getByText(/\$/)).toBeVisible();
  });

  test('should adjust duration with slider', async ({ page }) => {
    await page.goto('/');

    // Find duration slider
    const slider = page.locator('input[type="range"]');
    await slider.fill('8');

    // Check duration badge updates
    await expect(page.getByText('8 seconds')).toBeVisible();
  });

  test('should show gallery section', async ({ page }) => {
    await page.goto('/');

    // Scroll to gallery
    await page.getByText('Video Gallery').scrollIntoViewIfNeeded();
    await expect(page.getByText('Video Gallery')).toBeVisible();
    await expect(page.getByPlaceholderText(/Search videos/i)).toBeVisible();
  });

  test('should filter gallery by category', async ({ page }) => {
    await page.goto('/');

    // Scroll to gallery
    await page.getByText('Video Gallery').scrollIntoViewIfNeeded();

    // Click Bull Market filter
    const filterButton = page.getByText('Bull Market').nth(1); // Second one is in gallery
    await filterButton.click();

    // Check filter is active
    await expect(filterButton).toHaveClass(/bg-blue-600/);
  });

  test('should search videos in gallery', async ({ page }) => {
    await page.goto('/');

    // Scroll to gallery
    await page.getByText('Video Gallery').scrollIntoViewIfNeeded();

    // Type in search
    const searchInput = page.getByPlaceholderText(/Search videos/i);
    await searchInput.fill('Risk');

    // Check search value
    await expect(searchInput).toHaveValue('Risk');
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Hero should be visible
    await expect(page.getByText('Botspot')).toBeVisible();

    // Studio should stack vertically
    await expect(page.getByText('Prompt Builder')).toBeVisible();
  });

  test('should work on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    // All sections should be visible
    await expect(page.getByText('Botspot')).toBeVisible();
    await expect(page.getByText('Prompt Builder')).toBeVisible();
    await expect(page.getByText('Video Gallery')).toBeVisible();
  });

  test('should work on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    // Full layout should be visible
    await expect(page.getByText('Botspot')).toBeVisible();
    await expect(page.getByText('Video Generation Studio')).toBeVisible();
  });
});
