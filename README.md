# golem — 결정적 게임 룰엔진을 골렘(31B)이 설계·검증하는 스튜디오

LLM(gemma-4 31B)이 게임 규칙 엔진을 **설계→빌드→검증**하고, 사람은 "재미있나"만 판단한다. 검증은 모델 합의가 아니라 **모델 독립 Node 골든**(정확일치)이 정답 앵커다. 본선은 **전술 SRPG(영걸전형)**, 트랙은 **squad(부대+능동 적 AI)**다. tactics(영웅 1명)는 **회귀 기준/안정 baseline**으로 동결 유지(verify_tactics가 지킴). 검증된 squad 룰은 **Godot 4.7로 이식돼 실제 플레이 가능한 모바일 게임**이 된다(최근 활성 산출물 계층 — 아래 [Godot 트랙](#godot-트랙-검증된-룰--실제-플레이-가능한-게임-최근-활성)).

## 작업 시작 — 이 3개만 보면 움직인다
1. **`golem/HANDOFF.md`** — 현재 위치와 다음 액션(★첫 동작). **여기만 보면 됨.**
2. **검증 명령** — `python golem/validators/verify_tactics.py`(ALL PASS여야 함, 키0).
3. **금지** — Gemini/Gemma 키 런은 사용자 명시 go 뒤에만(아래 "키 사용").

참고(깊이 파거나 이유 추적할 때만): `golem/CLAUDE.md`(작업 규칙) · `golem/GolemStudioMode.md`(설계 정본 §23) · `golem/context-notes.md`(결정+왜) · `golem/checklist.md`(진행).

## 레이아웃 (2026-06-21 재설계 — core/tools/tactics/validators 패키지)
```
golem/                  # 패키지 루트
  paths.py              # 경로 정본(코드/데이터 디렉토리 한 곳 해석)
  core/                 # 엔진·하네스: build_graded·gate_runner·grading·contract_validator·static_gate·patch_apply·parse_write·build_prompt(+oracle·grade)
  tools/                # 골렘 설계·선별·드라이버: planning·design·specqa·reconcile·propose_*·graft·card_delta·driver_autocard·play_signals
  tactics/              # 전술 게임: gen_tactics_*·gen_assets·sprites
    bases/              #   tactics_kernel_base·tactics_base_l7/l8/l9
    packets/            #   planning/design/specqa_packet_tactics_*
    play/               #   플레이 산출물(index/play.html·levels·서사·assets)
  validators/           # 검증·CI: verify_tactics·run_keyless·replay·_validate_harness_keyless·_freeze_blocking_keyless
    fixtures/ schemas/  #   replay 계약 픽스처·스키마
  build_runs/           # 빌드/검증 워크스페이스(gitignore)
  legacy/               # 아카이브(본선 무관)
```
코드는 4개 서브패키지로 물리 분할하되, 각 파일 상단 부트스트랩이 코드 디렉토리 전부를 sys.path에 올려 bare import·동적 import·직접 실행(`python golem/<sub>/x.py`)이 그대로 동작한다(평면 네임스페이스). 데이터 경로는 `paths.py` 상수(BASES·PACKETS·PLAY·BUILD_RUNS 등)로 중앙화.

## 본선 = 전술 SRPG (활성 트랙 = squad)
- **두 트랙(패밀리)**: ① **squad**(부대 다중 아군 + 능동적 적 AI, **본선·활성 트랙**) = `squad_base`·`squad_base_l1~l8`. 신규 카드·레벨·서사는 여기서 누적한다. ② **tactics**(영웅 1명, 적 정지) = `tactics_base_l1~l9` — **원조이자 회귀 기준/안정 baseline으로 동결**(verify_tactics가 골든 회귀로 지킴, 새 기능은 안 얹음). 카드 도구가 `--family`로 양쪽 지원.
- tactics 카드: l1 마나방패·l2 사거리·l3 지형·l4 유닛·l5 루트맵·l6 상태이상·l7 밸런스·l8 흡혈·l9 처형. squad 카드: 사거리·충격파·협공·가시갑옷·aura_shield + 에테르노 phalanx_defense/asymmetric_strike. 전부 게이트·골든 diff 0.
- **새 카드는 stable base 위에 patch로 누적**(자율 파이프라인). 무인 한 줄: `python golem/tools/driver_autocard.py --family squad --setting "<세계관>"`.
- **소설→게임 브리지**: `forge_ingest.py`가 forge 소설 백업을 `eterno_outline.json`(전제·인물·이벤트 미션·카드씨앗)으로 압축 → 서사(levelstory `--setting`)·카드(propose_cards `--ref`)·레벨(propose_levels `--missions`) 모두 소설에서 무인 생성. 소설=스킨/씨앗, 골렘=검증된 룰.
- **현재 위치·다음 액션은 `golem/HANDOFF.md`만 본다.**

## Godot 트랙 (검증된 룰 → 실제 플레이 가능한 게임, 최근 활성)
검증된 squad 룰을 Godot 4.7로 이식해 아이폰에서 플레이한다. **분업**: 룰 포팅(`rules.gd`)·씬·외형(`board.gd` `_draw`)·자동전투 정책 전부 **골렘 ★키 저작**, 클로드는 사양(`godot/SCENE_SPEC.md`)·하네스·검증·증거 수집만, 최종 미관·조작감·재미 판정은 **사용자**. 자세한 현재 위치는 `golem/HANDOFF.md`.
- **`godot/`** = Godot 4 프로젝트. `scripts/rules.gd`(JS 룰 GDScript 포팅) · `scripts/board.gd`(아이소 2.5D·자동전투·공격 화살표, 골렘 저작) · `data/squad_levels.json` · `test/`(검증) · `e2e/`(Playwright) · `build_web/`(Web export, gitignore).
- **검증 계층(전부 키0)**: rules 골든(`test/run_rules_golden.gd`, JS↔GDScript 36/36 0-diff) · 입력 프로브(`run_input_probe.gd`, 선택·이동·공격 구조화·종료코드) · fixture 프로브(`run_fixture_probe.gd`, 미션0 비의존 `test/fixtures/*.json`) · 자동전투 프로브(`run_auto_probe.gd`, 결정적 종료) · **차등 퍼징**(`golem/tools/godot_fuzz_diff.py`, 시드 PRNG로 JS↔GDScript 무작위 케이스 0-diff) · **Playwright E2E**(`e2e/`, iPhone WebKit 부팅·터치→상태변화·자동전투 종료) · 시각 스냅샷(정적 MENU·BRIEFING).
- **테스트 상태 노출**: `test/test_bridge.gd`(읽기전용 autoload, web `?test=1`에서만 `window.GOLEM_TEST`). board.gd 미변경(증거 수집=Claude).
- **CI**: `.github/workflows/godot.yml`(keyless.yml과 분리, godot/** 경로 게이트) — import→골든→프로브→fixture→퍼징→Web export→E2E→시각.
- 자동 검증은 "올바르게 실행/룰 일치/입력 후 상태 변경/웹 로드"만 책임지고 **재미는 검증하지 않는다**(사람 oracle).

## 검증 정본 (수정 후 반드시 실행)
```
python golem/validators/verify_tactics.py     # (엔진) 9카드 골든 회귀 + l8 strict 승격 + run_keyless(하네스 CI)
python golem/tools/godot_fuzz_diff.py          # (Godot) JS↔GDScript 차등 퍼징 ALL MATCH (node+godot 필요)
```
구성: `core/build_graded.py`(빌드·게이트·채점) + `core/contract_validator.py` + `core/static_gate.py` + `validators/` keyless 스크립트. 후보=strict False, **base 승격=strict True**. Godot 트랙 전체 게이트는 `.github/workflows/godot.yml`(또는 로컬 `golem/tools/godot_port_scene.py --replay godot/scripts/board.gd`).

## 생성 산출물 (수정 금지 — source of truth 아님)
- `golem/tactics/play/` = 외형(검증 엔진을 **읽기전용** require, 룰 복제 안 함). tactics: `index.html`(`gen_tactics_play.py`=턴 재생) · **`play.html`(`gen_tactics_interactive.py`=직접 플레이)** · `levels.json`·`levelstory.json`·`assets/tile_sprites.json`(골렘 비전이 CC0 팩서 선택). **squad: `squad.html`(`gen_squad_play.py`=부대 턴재생 뷰어) · `squad_levels.json`(미션 레벨) · `squad_levelstory.json`(에테르노 서사).** 수정은 `tactics/bases/`/제너레이터에서만.
- `golem/build_runs/` = 빌드/제안 산출물(gitignore).
- 아이폰 플레이: `node golem/tactics/play/server.js` (테일스케일).

## 자율 파이프라인 (골렘이 완결 후보를 무인 생성)
`propose_cards.py`(다음 카드 제안·`--ref` 장르시드) → **`critique_ideas`(★키 의미 비평가 선별기: 기존 카드 대비 역할겹침·얕음·실현불가를 골렘이 strict 평가해 약한 후보 자동 탈락, 빌드 전)** → `card_delta.py`+`graft.py`(골렘 base-델타 설계·키0 검증·교차검산) → `build_graded --base <family>_base_lN --inject-modules src/game_logic.js --patch`(델타만 빌드) → `gen_tactics_story.py`(서사 B겹) → 렌더. **`driver_autocard.py` = 한 줄 아이디어→선별→완결 후보 한 바퀴 무인(`--no-select`로 선별기 끔).**
- **레벨 시스템**: `propose_levels.py`(골렘 레벨 생성, 메커니즘×난이도 변별 누적으로 임의 N까지) + `play_signals.py`(결정적 신호, 키0·"실노출" 칸): 풀이/최소턴/지배전략/카드영향 + **재미 신호(선택지 수=최단해 첫 수 가짓수·전략 다양성=최단해 개수·치사율=즉사 간선 비율)** → 변별 커브 `levels.json`. 서사 = `gen_tactics_levelstory.py`(골렘이 레벨별 적·메커니즘 반영 서사 저작 → `levelstory.json`, 구조검증 키0).
- **비주얼**: `gen_assets.py`(팩 무관: `--pack` 레지스트리·시트형 슬라이스·`--solid` 불투명도 필터·`--slots` 병합 → CC0 팩→컨택트시트→**골렘 비전 선택**→tile_sprites.json) / `sprites.py`(SVG 폴백). 인터랙티브 플레이 `gen_tactics_interactive.py`. **외형도 골렘이 고른다**(클로드는 하네스만). 주의: 퀄리티 천장은 파이프라인이 아니라 **에셋**(여기선 래스터 생성 불가 — 좋은 에셋 떨구면 골렘이 통합).
- 노브 몇 개로 조절(`--n/--min-turns/--ref/--scenario`), 손편집 없음 — "어디까지=완결 후보까지·선별에서 멈춤"(`§1.5`), "다 자동화·노브 몇 개" 운영원칙.

## 디렉토리 경계 (혼선 주의)
- **`core/`(엔진·하네스 — 신중히 수정)**: `build_graded.py`(orchestration) + 분해 모듈 `build_prompt.py`(프롬프트)·`gate_runner.py`(게이트)·`grading.py`(합의·골든)·`patch_apply.py`(패치)·`contract_validator.py`·`static_gate.py`·`parse_write.py`(FILE 마커 헬퍼)·`build.py` + `oracle.py`·`grade.py`(`--reconcile` 진단 경로, lazy import).
- **`tools/`(설계·선별·드라이버)**: `planning`·`design`·`specqa`·`reconcile`·`auto_oracle` + `propose_cards`·`propose_levels`·`play_signals` + `graft`·`card_delta`·`driver_autocard`.
- **`tactics/`(본선 게임)**: `gen_tactics_*_golden.py`(골든 참조)·`gen_tactics_{play,interactive,story,levelstory}.py`(렌더·서사)·`gen_assets`·`sprites` + `bases/`(`tactics_kernel_base`·`tactics_base_l7/l8/l9`)·`packets/`(`planning/specqa_packet_tactics_*`)·`play/`(산출물).
- **`validators/`(검증·CI)**: `verify_tactics.py`(정본)·`run_keyless.py`(CI)·`replay.py`·`_validate_harness_keyless.py`(레버4 하네스 회귀, tactics 픽스처)·`_freeze_blocking_keyless.py` + `fixtures/`·`schemas/`.
- **과거 실험 = `golem/legacy/`(본선 무관·live 미참조, 아카이브)**: 옛 driver/worker_prompt·game-bank 흐름(`bank_*`·`game_bank`·`bank_init`)·oracle 설계/골든/승격 실험. `legacy/README.md` 참조. **새 작업은 여기서 시작 금지.**
- **공용 인프라(저장소 루트 `C:\Users\USER\golem`)**: `config.py`·`llm.py`·`observability.py`·`run_index.py`·`key_usage.py` + `.env`. 패키지 내 경로 정본 = `golem/paths.py`.

## 키 사용
`gemma-4-31b-it` 단독(31solo). 키는 사용자 명시 go 뒤에만. 키0 검증(`verify_tactics.py`)은 항상 가능.
