// Godot Web export를 iPhone WebKit으로 띄워 콘솔오류·터치→상태변화를 검증하는 Playwright 설정
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: '.',
  timeout: 150000,
  expect: { timeout: 30000 },
  outputDir: path.join(__dirname, 'proof', 'artifacts'),
  reporter: [['list']],
  use: {
    ...devices['iPhone 13'], // WebKit 엔진 + iPhone 뷰포트 + 터치
    baseURL: 'http://127.0.0.1:8799',
    trace: 'on',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'python ' + path.join(__dirname, '..', 'serve_web.py') + ' 8799',
    url: 'http://127.0.0.1:8799/index.html',
    reuseExistingServer: true,
    timeout: 60000,
  },
});
