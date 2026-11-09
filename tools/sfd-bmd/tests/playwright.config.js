module.exports = {
  testDir: '.',
  testMatch: 'beam.spec.js',
  timeout: 30000,
  use: {
    headless: true,
    acceptDownloads: true,
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } },
  ],
  reporter: [['list']],
};
