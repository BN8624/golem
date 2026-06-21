# golem — 결정적 게임 룰엔진을 골렘(31B)이 설계·검증하는 스튜디오

LLM(gemma-4 31B)이 게임 규칙 엔진을 **설계→빌드→검증**하고, 사람은 "재미있나"만 판단한다. 검증은 모델 합의가 아니라 **모델 독립 Node 골든**(정확일치)이 정답 앵커다. 현재 본선은 **전술 SRPG(영걸전형)**.

## 정본 우선순위 (작업 시작 전 이 순서로 읽기)
1. `golem/CLAUDE.md` — 작업 규칙.
2. `golem/HANDOFF.md` — **현재 위치와 다음 액션(여기만 보면 됨).**
3. `golem/GolemStudioMode.md` — 설계 정본(§23=실현된 자율 파이프라인).
4. `golem/context-notes.md`(결정+왜) · `golem/checklist.md`(진행).

## 본선 = 전술 SRPG, 누적 9카드
- **stable baseline = `golem/studio/tactics_base_l8`** (검증·동결). **실험 = `tactics_base_l9`**.
- 카드 l1 마나방패·l2 사거리·l3 지형·l4 유닛·l5 루트맵·l6 상태이상·l7 밸런스·l8 흡혈·l9 처형. 전부 게이트·골든 diff 0.
- **새 카드는 stable(l8) 위에 patch로 누적**한다(아래 자율 파이프라인).

## 검증 정본 (수정 후 반드시 실행)
```
python golem/studio/verify_tactics.py     # 9카드 골든 회귀 + l8 strict 승격 + run_keyless(하네스 CI)
```
구성: `build_graded.py`(빌드·게이트·채점) + `contract_validator.py` + `static_gate.py` + keyless 스크립트. 후보=strict False, **base 승격=strict True**.

## 생성 산출물 (수정 금지 — source of truth 아님)
- `golem/studio/tactics_play/` = 외형(검증 엔진을 **읽기전용** require, 룰 복제 안 함). `index.html`(`gen_tactics_play.py`=턴 재생 뷰어) · **`play.html`(`gen_tactics_interactive.py`=직접 플레이, 픽셀 스프라이트 + 풀 타일링)** · `levels.json`(`propose_levels.py` 생성, 현재 18레벨) · `levelstory.json`(`gen_tactics_levelstory.py`=레벨팩 서사 B겹) · `assets/tile_sprites.json`(골렘 비전이 CC0 팩서 선택: 캐릭터=Kenney Tiny Dungeon, 바닥/벽=Kenney Roguelike RPG). 수정은 `tactics_base_*`/제너레이터에서만.
- `golem/studio/build_runs/` = 빌드/제안 산출물(gitignore).
- 아이폰 플레이: `node golem/studio/tactics_play/server.js` (테일스케일).

## 자율 파이프라인 (골렘이 완결 후보를 무인 생성)
`propose_cards.py`(다음 카드 제안·`--ref` 장르시드) → `card_delta.py`+`graft.py`(골렘 base-델타 설계·키0 검증·교차검산) → `build_graded --base tactics_base_lN --inject-modules src/game_logic.js --patch`(델타만 빌드) → `gen_tactics_story.py`(서사 B겹) → `gen_tactics_play.py`(렌더). **`driver_autocard.py` = 한 줄 아이디어→완결 후보 한 바퀴 무인.**
- **레벨 시스템**: `propose_levels.py`(골렘 레벨 생성, 메커니즘×난이도 변별 누적으로 임의 N까지) + `play_signals.py`(결정적 신호=풀이/최소턴/지배전략/카드영향, 키0 검증·"실노출" 칸) → 변별 커브 `levels.json`(현재 18). 서사 = `gen_tactics_levelstory.py`(골렘이 레벨별 적·메커니즘 반영 서사 저작 → `levelstory.json`, 구조검증 키0).
- **비주얼**: `gen_assets.py`(팩 무관: `--pack` 레지스트리·시트형 슬라이스·`--solid` 불투명도 필터·`--slots` 병합 → CC0 팩→컨택트시트→**골렘 비전 선택**→tile_sprites.json) / `sprites.py`(SVG 폴백). 인터랙티브 플레이 `gen_tactics_interactive.py`. **외형도 골렘이 고른다**(클로드는 하네스만). 주의: 퀄리티 천장은 파이프라인이 아니라 **에셋**(여기선 래스터 생성 불가 — 좋은 에셋 떨구면 골렘이 통합).
- 노브 몇 개로 조절(`--n/--min-turns/--ref/--scenario`), 손편집 없음 — "어디까지=완결 후보까지·선별에서 멈춤"(`§1.5`), "다 자동화·노브 몇 개" 운영원칙.

## 디렉토리 경계 (혼선 주의)
- **본선(정본)**: `studio/planning_packet_tactics_*` · `specqa_packet_tactics_*` · `gen_tactics_*_golden.py` · `tactics_base_*` · `tactics_kernel_base`.
- **과거 게임(참고·정본 아님)**: `studio/`의 `detective_base`·`sokoban_base`·`rocket_base`·`eterno_base`·`station_*`·`bridge_eterno` + 그 packet들. 전술 본선에 그대로 적용 금지.
- **핵심 도구(live)**: `studio/`의 `build_graded.py`(orchestration) + 분해 모듈 `build_prompt.py`(프롬프트 조립)·`gate_runner.py`(게이트)·`grading.py`(합의·골든)·`patch_apply.py`(패치) + 파이프라인 `graft.py`·`card_delta.py`·`propose_cards.py`·`driver_autocard.py`·`gen_tactics_story.py`·`gen_tactics_play.py`.
- **루트 `golem/` live(건드리지 말 것)**: `parse_write.py`(FILE 마커 헬퍼 — build_graded 등이 import)·`static_gate.py` + `oracle.py`+`grade.py`(`build_graded --reconcile` 진단 경로, lazy import). *(`driver.py`는 `parse_write.py`로 분리 후 `legacy/`로 이동됨.)*
- **과거 실험 = `golem/legacy/`(본선 무관·live 미참조, 아카이브)**: 옛 driver/worker_prompt·game-bank 흐름(`bank_*`·`game_bank`·`bank_init`)·oracle 설계/골든/승격 실험(`oracle_design*`·`make_golden`·`promote_solution`·`*_probe`·`demo_part`·`campaign`). `legacy/README.md` 참조. **새 작업은 여기서 시작 금지.**
- **공용 인프라(저장소 루트 `C:\Users\USER\golem`)**: `config.py`·`llm.py`·`observability.py`·`run_index.py`·`key_usage.py` + `.env`.

## 키 사용
`gemma-4-31b-it` 단독(31solo). 키는 사용자 명시 go 뒤에만. 키0 검증(`verify_tactics.py`)은 항상 가능.
