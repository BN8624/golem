// Godot Web 시각 스냅샷 — 정적 화면(MENU·BRIEFING)의 레이아웃·폰트·에셋 회귀를 픽셀 비교로 잡는다(자동전투·이펙트가 도는 PLAYING/RESULT는 비결정적이라 제외)
const { test, expect } = require('@playwright/test');

async function golemState(page) {
  return await page.evaluate(() => (typeof window.GOLEM_TEST !== 'undefined' ? window.GOLEM_TEST : null));
}

async function gameTap(page, gx, gy) {
  const box = await page.locator('#canvas').boundingBox();
  const s = Math.min(box.width, box.height) / 640;
  const offX = box.x + (box.width - 640 * s) / 2;
  const offY = box.y + (box.height - 640 * s) / 2;
  await page.touchscreen.tap(offX + gx * s, offY + gy * s);
}

// 기준 이미지는 환경(OS/GPU)마다 다르다 — Playwright가 플랫폼 접미사로 분리 저장(menu-webkit-<platform>.png).
// GOLEM이 외형을 의도적으로 재생성하면 `npx playwright test visual.spec.js --update-snapshots`로 명시적 갱신 후 커밋한다.
test.describe('시각 스냅샷(정적 화면만)', () => {
  test('MENU 화면', async ({ page }) => {
    await page.goto('/index.html?test=1');
    await expect.poll(async () => (await golemState(page))?.screen, { timeout: 120000 }).toBe('MENU');
    await page.waitForTimeout(500); // 캔버스 정착
    await expect(page).toHaveScreenshot('menu.png', { maxDiffPixelRatio: 0.02 });
  });

  test('BRIEFING 화면', async ({ page }) => {
    await page.goto('/index.html?test=1');
    await expect.poll(async () => (await golemState(page))?.screen, { timeout: 120000 }).toBe('MENU');
    await gameTap(page, 320, 175); // 미션0 버튼
    await expect.poll(async () => (await golemState(page))?.screen).toBe('BRIEFING');
    await page.waitForTimeout(300);
    await expect(page).toHaveScreenshot('briefing.png', { maxDiffPixelRatio: 0.02 });
  });
});
