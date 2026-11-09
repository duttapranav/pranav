const { test, expect } = require('@playwright/test');
const path = require('path');
const { pathToFileURL } = require('url');

const appUrl = pathToFileURL(path.resolve(__dirname, '../index.html')).href;

async function openApp(page) {
  await page.goto(appUrl);
  await expect(page.locator('#analyse')).toBeVisible();
}

async function clearLoads(page) {
  for (const selector of ['[data-remove-point]', '[data-remove-udl]']) {
    while (await page.locator(selector).count()) {
      await page.locator(selector).first().click();
    }
  }
}

async function setSupports(page, supports) {
  // Change the beam preset first so its default rows are created.
  await page.locator('#supports .support-row').first().waitFor();
  while (await page.locator('#supports .support-row').count() < supports.length) {
    await page.locator('#addSupport').click();
  }
  while (await page.locator('#supports .support-row').count() > supports.length) {
    await page.locator('[data-remove-support]').last().click();
  }
  for (let i = 0; i < supports.length; i++) {
    const row = page.locator('#supports .support-row').nth(i);
    await row.locator('[data-k="x"]').fill(String(supports[i].x));
    const typeSelect = row.locator('[data-k="type"]');
    await typeSelect.selectOption(supports[i].type);
    // Explicit bubbling change event also exercises the delegated support
    // state handler consistently across browser engines.
    await typeSelect.dispatchEvent('change');
    await expect(typeSelect).toHaveValue(supports[i].type);
  }
}

async function addPoint(page, p, x) {
  await page.locator('#addPoint').click();
  const row = page.locator('#points .load-row').last();
  await row.locator('[data-k="p"]').fill(String(p));
  await row.locator('[data-k="x"]').fill(String(x));
}

async function addUdl(page, q, a, b) {
  await page.locator('#addUdl').click();
  const row = page.locator('#udls .load-row').last();
  await row.locator('[data-k="q"]').fill(String(q));
  await row.locator('[data-k="a"]').fill(String(a));
  await row.locator('[data-k="b"]').fill(String(b));
}

async function analyse(page) {
  await page.locator('#analyse').click();
  await expect(page.locator('#error')).toBeHidden();
  await expect(page.locator('#sfd svg')).toBeVisible();
  await expect(page.locator('#bmd svg')).toBeVisible();
}

test('simply supported central point load gives correct reactions and BMD', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('simply');
  await page.locator('#length').fill('6');
  await clearLoads(page);
  await addPoint(page, 20, 3);
  await analyse(page);
  await expect(page.locator('#reactionTable')).toContainText('10');
  await expect(page.locator('#metrics')).toContainText('30');
});

test('SI switch preserves load magnitudes and converts positions and point loads', async ({ page }) => {
  await openApp(page);
  await page.locator('#unit').selectOption('si');
  await expect(page.locator('#length')).toHaveValue('6000');
  await expect(page.locator('#points [data-k="p"]').first()).toHaveValue('20000');
  // The UDL is entered as N/mm in SI; its numeric value remains unchanged.
  await expect(page.locator('#udls [data-k="q"]').first()).toHaveValue('10');
  await analyse(page);
  await expect(page.locator('#beamView')).toContainText('6000');
});

test('fixed-pinned UDL produces a stable indeterminate solution', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('fixed');
  await page.locator('#length').fill('2');
  // Blur the length field so its change handler finishes regenerating defaults.
  await page.locator('#length').press('Tab');
  await expect(page.locator('#supports .support-row').first().locator('[data-k="type"]')).toHaveValue('fixed');
  await setSupports(page, [{ x: 0, type: 'pin' }, { x: 2, type: 'fixed' }]);
  await clearLoads(page);
  await addUdl(page, 1, 0, 2);
  await analyse(page);
  await expect(page.locator('#reactionTable')).toContainText('0.75');
  await expect(page.locator('#reactionTable')).toContainText('1.25');
});

test('rejects duplicate supports at the same location', async ({ page }) => {
  await openApp(page);
  await page.locator('#addSupport').click();
  await page.locator('#supports .support-row').nth(1).locator('[data-k="x"]').fill('0');
  await page.locator('#analyse').click();
  await expect(page.locator('#error')).toContainText('Two supports cannot occupy the same position');
});

test('CSV export downloads a results file after analysis', async ({ page }) => {
  await openApp(page);
  await page.locator('#analyse').click();
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#csv').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('beam-analysis-results.csv');
});
