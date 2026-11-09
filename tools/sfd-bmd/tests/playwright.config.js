module.exports = {
  testDir: '.',
  testMatch: 'beam.spec.js',
  timeout: 30000,
  use: {
    browserName: 'chromium',
    headless: true,
    acceptDownloads: true,
  },
  reporter: [['list']],
};
