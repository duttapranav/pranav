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

async function inspectAt(page, x) {
  const slider = page.locator('#inspectX');
  await slider.evaluate((el, value) => {
    el.step = 'any';
    el.value = String(value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, x);
  const values = page.locator('#inspectValues .metric strong');
  await expect(values).toHaveCount(5);
  return {
    position: Number.parseFloat(await values.nth(0).innerText()),
    shear: Number.parseFloat(await values.nth(1).innerText()),
    moment: Number.parseFloat(await values.nth(2).innerText()),
    deflection: Number.parseFloat(await values.nth(4).innerText()),
  };
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


test('point-load SFD jump and BMD continuity match section equilibrium', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('simply');
  await page.locator('#length').fill('6');
  await clearLoads(page);
  await addPoint(page, 20, 3);
  await analyse(page);

  const left = await inspectAt(page, 2.99);
  const atLoad = await inspectAt(page, 3);
  const right = await inspectAt(page, 3.01);
  expect(left.shear).toBeCloseTo(10, 2);
  expect(right.shear).toBeCloseTo(-10, 2);
  expect(atLoad.moment).toBeCloseTo(30, 2);
  expect(left.moment).toBeCloseTo(29.9, 1);
  expect(right.moment).toBeCloseTo(29.9, 1);
});

test('partial UDL shear slope and maximum sagging moment match analytical values', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('simply');
  await page.locator('#length').fill('6');
  await clearLoads(page);
  await addUdl(page, 5, 1, 4);
  await analyse(page);

  const before = await inspectAt(page, 1);
  const peak = await inspectAt(page, 2.75);
  const after = await inspectAt(page, 4);
  expect(before.shear).toBeCloseTo(8.75, 2);
  expect(peak.shear).toBeCloseTo(0, 1);
  expect(peak.moment).toBeCloseTo(16.40625, 2);
  expect(after.shear).toBeCloseTo(-6.25, 2);
  expect(after.moment).toBeCloseTo(12.5, 2);
  await expect(page.locator('#metrics')).toContainText('16.41');
});

test('cantilever end point load gives the correct hogging moment diagram', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('cantilever');
  await page.locator('#length').fill('6');
  await page.locator('#length').press('Tab');
  await clearLoads(page);
  await addPoint(page, 20, 6);
  await analyse(page);

  const fixed = await inspectAt(page, 0);
  const middle = await inspectAt(page, 3);
  const free = await inspectAt(page, 6);
  expect(fixed.moment).toBeCloseTo(-120, 2);
  expect(middle.moment).toBeCloseTo(-60, 2);
  expect(free.moment).toBeCloseTo(0, 2);
});

test('two-span continuous beam has a continuous hogging moment at its interior support', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('simply');
  await page.locator('#length').fill('10');
  await page.locator('#length').press('Tab');
  await setSupports(page, [
    { x: 0, type: 'pin' },
    { x: 5, type: 'roller' },
    { x: 10, type: 'roller' },
  ]);
  await clearLoads(page);
  await addUdl(page, 1, 0, 10);
  await analyse(page);

  const left = await inspectAt(page, 4.99);
  const support = await inspectAt(page, 5);
  const right = await inspectAt(page, 5.01);
  expect(support.moment).toBeCloseTo(-3.125, 2);
  expect(left.moment).toBeCloseTo(-3.12, 1);
  expect(right.moment).toBeCloseTo(-3.12, 1);
  expect(Number(left.shear)).toBeCloseTo(-3.115, 1);
  expect(Number(right.shear)).toBeCloseTo(3.115, 1);
});


test('simply supported central point-load deflection matches Euler-Bernoulli solution', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('simply');
  await page.locator('#length').fill('6');
  await clearLoads(page);
  await addPoint(page, 20, 3);
  await page.locator('#elasticModulus').fill('200');
  await page.locator('#secondMoment').fill('0.0008');
  await analyse(page);
  await expect(page.locator('#deflection svg')).toBeVisible();
  await expect(page.locator('#metrics')).toContainText('0.5625');
  const mid = await inspectAt(page, 3);
  expect(mid.deflection).toBeCloseTo(0.5625, 3);
});

test('cantilever free-end deflection matches closed-form point-load solution', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('cantilever');
  await page.locator('#length').fill('6');
  await page.locator('#length').press('Tab');
  await clearLoads(page);
  await addPoint(page, 20, 6);
  await page.locator('#elasticModulus').fill('200');
  await page.locator('#secondMoment').fill('0.0008');
  await analyse(page);
  const tip = await inspectAt(page, 6);
  expect(tip.deflection).toBeCloseTo(9, 3);
  await expect(page.locator('#metrics')).toContainText('9');
});

test('simply supported full-span UDL deflection matches closed-form solution', async ({ page }) => {
  await openApp(page);
  await page.locator('#beamType').selectOption('simply');
  await page.locator('#length').fill('6');
  await clearLoads(page);
  await addUdl(page, 10, 0, 6);
  await page.locator('#elasticModulus').fill('200');
  await page.locator('#secondMoment').fill('0.0008');
  await analyse(page);
  const mid = await inspectAt(page, 3);
  expect(mid.deflection).toBeCloseTo(1.0546875, 3);
});

test('rejects zero or negative flexural stiffness inputs', async ({ page }) => {
  await openApp(page);
  await page.locator('#elasticModulus').fill('0');
  await page.locator('#analyse').click();
  await expect(page.locator('#error')).toContainText('positive');
  await page.locator('#elasticModulus').fill('200');
  await page.locator('#secondMoment').fill('-0.1');
  await page.locator('#analyse').click();
  await expect(page.locator('#error')).toContainText('positive');
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

test('PNG export produces diagram downloads supported by the browser', async ({ page, browserName }) => {
  await openApp(page);
  await page.locator('#analyse').click();
  await expect(page.locator('#error')).toBeHidden();
  const downloads = [];
  page.on('download', download => downloads.push(download));
  await page.locator('#png').click();
  // WebKit's browser automation environment exposes only the first
  // programmatic download from a single gesture; Chromium and Firefox expose
  // all four. The complete four-file export is asserted in those engines.
  const expectedCount = browserName === 'webkit' ? 1 : 4;
  await expect.poll(() => downloads.length, { timeout: 10000 }).toBe(expectedCount);
  const names = downloads.map(download => download.suggestedFilename()).sort();
  if (browserName === 'webkit') {
    expect(names).toHaveLength(1);
    expect(['beam.png', 'sfd.png', 'bmd.png', 'deflection.png']).toContain(names[0]);
  } else {
    expect(names).toEqual(['beam.png', 'bmd.png', 'deflection.png', 'sfd.png']);
  }
});

test('print action invokes print and Chromium can render an A4 PDF', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'page.pdf is supported by Chromium only');
  await page.addInitScript(() => {
    window.__printInvoked = false;
    window.print = () => { window.__printInvoked = true; };
  });
  await openApp(page);
  await page.locator('#analyse').click();
  await page.locator('#pdf').click();
  await expect.poll(() => page.evaluate(() => window.__printInvoked)).toBe(true);
  await page.emulateMedia({ media: 'print' });
  const pdf = await page.pdf({ format: 'A4', printBackground: true });
  expect(pdf.byteLength).toBeGreaterThan(1000);
});

test('layout fits a narrow mobile viewport without horizontal page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openApp(page);
  await page.locator('#analyse').click();
  await expect(page.locator('#sfd svg')).toBeVisible();
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport + 1);
});

