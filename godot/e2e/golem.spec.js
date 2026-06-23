// Godot Web export E2E — 부팅·메뉴 탭(터치→상태변화)·자동전투 종료·콘솔오류를 WebKit/iPhone에서 검증하고 proof/에 증거 저장
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const PROOF = path.join(__dirname, 'proof');

// 헤드리스 WebKit(ANGLE) GL 백엔드의 양성 경고 — 게임/룰 오류가 아니라 드라이버 노이즈. 실 iPhone Safari(Metal)에선 안 나며 최종 검증은 사람 몫.
const BENIGN = [/glBlitFramebuffer/i, /No more validation messages will be reported/i];
function isBenign(t) { return BENIGN.some((r) => r.test(t)); }

// 게임 논리좌표(640x640, stretch aspect=keep)를 캔버스 클라이언트 좌표로 변환해 탭
async function gameTap(page, gx, gy) {
  const box = await page.locator('#canvas').boundingBox();
  const s = Math.min(box.width, box.height) / 640;
  const offX = box.x + (box.width - 640 * s) / 2;
  const offY = box.y + (box.height - 640 * s) / 2;
  await page.touchscreen.tap(offX + gx * s, offY + gy * s);
}

async function golemState(page) {
  return await page.evaluate(() => (typeof window.GOLEM_TEST !== 'undefined' ? window.GOLEM_TEST : null));
}

test('Godot web: 부팅→메뉴 탭→플레이→자동전투 종료, 콘솔오류 0', async ({ page }) => {
  fs.mkdirSync(PROOF, { recursive: true });
  const consoleErrors = [];   // 실제 오류(양성 GL 노이즈 제외)
  const benignWarnings = [];  // 걸러낸 GL 드라이버 경고(투명성 위해 기록)
  function note(t) { (isBenign(t) ? benignWarnings : consoleErrors).push(t); }
  page.on('console', (m) => { if (m.type() === 'error') note(m.text()); });
  page.on('pageerror', (e) => note('pageerror: ' + e.message));

  // 1) ?test=1 로 로드 → GOLEM_TEST 가 MENU 로 채워질 때까지 대기(WASM 부팅)
  await page.goto('/index.html?test=1');
  await expect.poll(async () => (await golemState(page))?.screen, { timeout: 120000 }).toBe('MENU');
  await page.screenshot({ path: path.join(PROOF, '01_menu.png') });

  // 2) 미션0 버튼 탭(게임좌표 320,175) → BRIEFING (터치→상태변화)
  await gameTap(page, 320, 175);
  await expect.poll(async () => (await golemState(page))?.screen).toBe('BRIEFING');
  await page.screenshot({ path: path.join(PROOF, '02_briefing.png') });

  // 3) 아무데나 탭 → PLAYING (터치→상태변화)
  await gameTap(page, 320, 300);
  await expect.poll(async () => (await golemState(page))?.screen).toBe('PLAYING');
  const playing = await golemState(page);
  await page.screenshot({ path: path.join(PROOF, '03_playing.png') });

  // 4) 자동전투(auto_mode) 진행 → turn 증가 + 종료(RESULT, VICTORY/DEFEAT)
  await expect.poll(async () => (await golemState(page))?.screen, { timeout: 90000 }).toBe('RESULT');
  const result = await golemState(page);
  await page.screenshot({ path: path.join(PROOF, '04_result.png') });

  // 자동 검증 항목과 인간 검토 항목을 분리해 기록(verdict)
  const verdict = {
    verified: [
      'Web export가 WebKit(iPhone)에서 정상 로드됨',
      '메뉴 탭 후 화면이 MENU→BRIEFING→PLAYING 으로 변경됨(터치→상태변화)',
      `자동전투가 진행되어 turn 이 ${result.turn} 까지 증가하고 ${result.status} 로 종료됨(screen=RESULT)`,
      `브라우저 실오류 ${consoleErrors.length}건(양성 GL 경고 ${benignWarnings.length}건 제외)`,
    ],
    not_verified: ['미관', '조작감', '재미'],
    human_review_required: true,
    detail: { playing_turn: playing?.turn, result_turn: result.turn, status: result.status, consoleErrors, benignWarningCount: benignWarnings.length },
  };
  fs.writeFileSync(path.join(PROOF, 'verdict.json'), JSON.stringify(verdict, null, 2));

  // 자동 검증은 "올바르게 실행/입력 후 상태 변경/웹 로드"만 책임진다 — 재미는 검증하지 않는다.
  expect(consoleErrors, 'browser console errors: ' + consoleErrors.join(' | ')).toEqual([]);
  expect(result.status === 'VICTORY' || result.status === 'DEFEAT').toBeTruthy();
  expect(result.turn).toBeGreaterThan(0);
});
