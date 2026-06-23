# Godot 이식 컨텍스트 노트 (결정과 이유)

## 왜 Godot인가 (2026-06-22)
- 사용자가 "기존 엔진(Godot)이 낫다"며 ChatGPT+Godot·무코딩 게임제작 사례를 근거로 전환 결정.
- 골렘의 손코딩 HTML 뷰어로는 외형 천장(에셋·렌더)이 막힌다. Godot = 진짜 렌더/입력/애니/모바일 export.
- 단 검증 코어(결정적 골든)는 버리지 않는다 — 그게 바이브코딩에 없는 우위.

## 분업 (엔진 바꿔도 유지) [[godot-port-is-golems-job]]
- 골렘(★키): 룰 GDScript 포팅·씬·외형 선택.
- 클로드(키0): 하네스만 — 골든 추출기·러너·포팅 사양·배관. 룰 직접 안 씀.
- 사용자: Godot 설치·취향.

## 검증 = 골든 다리 (사용자 비평 반영)
- `--test`는 엔진 C++ 테스트(tests=yes 빌드)용이라 안 씀. 대신 **커스텀 러너** `run_rules_golden.gd`를
  `godot --headless --path godot --script ...`로 실행.
- 0-diff는 **룰 동치 검증**일 뿐 플레이 가능 검증 아님 → UI·입력·턴표시는 Phase 2에서 따로.
- 솔루션 trace만으론 부족 → 골든에 invalid(경계/점유/무사거리)·enemy_turn·win/loss·card(knockback/reflect/range/flank) 엣지 추가(총 14케이스·36스텝).
- `rules.gd`는 순수 모듈(Node 금지), 씬은 호출만 → 골든 검증이 유지됨.

## 고정 자산
- 룰 원본: `golem/tactics/bases/squad_base_l8/src/game_logic.js`.
- 미션: `golem/tactics/play/squad_levels.json`(에테르노 4미션, 사람이 재미 확인). 재미 평가도 전부 A(70~82).
- 골든 정답: `godot/test/rules_golden.json`(JS 엔진 생성, 재생성 = `python golem/tools/godot_export_golden.py`).

## Phase 2~3.5 — 플레이·서사·외형 (2026-06-23, G95)
- **아이폰 접속**: Godot Web은 보안 컨텍스트 필수 → 평문 HTTP(테일스케일 IP) 거부. `tailscale serve --https=443 → 127.0.0.1:8771`로
  실인증서 HTTPS. 접속 = `https://node.tail3e9e21.ts.net/`(IP 아님). 서버=`python godot/serve_web.py 8771`(재부팅 시 재실행, serve는 --bg라 유지).
- **웹 한글**: `ThemeDB.get_fallback_font()`는 데스크톱만 시스템 한글 대체, 웹엔 글리프 없어 □. → 나눔고딕(OFL) 임베드(`assets/fonts/`).
- **클릭 버그(반복된 GDScript 함정)**: JSON `pos`는 float `[0.0,0.0]`, 클릭 셀은 int. `[0.0,0.0]==[0,0]`은 false(배열은 원소 타입까지 엄격).
  → 원소별 `pos[0]==gx`. 또 아군·적 **id가 겹쳐서**(둘 다 1,2) dict 키로 id만 쓰면 엉뚱한 유닛 flash·데미지 오계산 → 진영+id 키.
- **검증 한계(핵심 교훈)**: 헤드리스 스모크/입력프로브는 `_draw`를 호출 안 해 렌더 버그(draw_string/draw_set_transform 시그니처, 폰트/텍스처)를
  못 잡는다. → `godot_port_scene.py` 채택 게이트에 **windowed 렌더 캡처**(`run_render`/`capture_attack.gd`) 추가. 단 게이트도 "에러 없이 그려지나"만 보지
  미관·미세버그(빨강 id충돌·고정cell·바닥 띠)는 못 잡음 → 클로드가 캡처 보고 SCENE_SPEC 보강·되먹임 루프가 필수(골렘 3회 되먹임으로 채택).
- **외형 분업 재확인([[godot-does-the-art-too]])**: 스프라이트·맵·이펙트·`_draw` 코드까지 **골렘이 저자**. 클로드는 에셋(Tiny Dungeon CC0·폰트) 다운로드·import,
  컨택트시트 식별, SCENE_SPEC 사양, 렌더 게이트만. 클로드가 _draw를 직접 짠 건 위반(사용자 G95 지적, G83 재발).

## Phase 3.6 — 아이소메트릭 2.5D 전환 (2026-06-24, 사용자 요청 B)
- **왜 진짜 아이소(B)인가**: 사용자가 가짜 2.5D(그림자·높이감) 대신 진짜 아이소메트릭을 택함. 이건 외형만이 아니라 **클릭→칸 좌표 계약**을 바꾸므로
  하네스(입력프로브·SCENE_SPEC 고정좌표)도 같이 움직인다 — 분업상 좌표 계약·프로브=클로드 하네스, 다이아몬드 렌더=골렘 ★키.
- **좌표 계약 재설계(핵심)**: 탑다운 `gx=int(x/cell)`을 버리고, board가 **`cell_to_screen(gx,gy)` 한 함수를 단일 진실원천**으로 노출.
  `_draw`(타일·유닛 배치)·`_unhandled_input`(클릭 히트=역투영)·하네스(프로브/캡처)가 전부 이걸 쓴다. 투영 = `origin + ((gx-gy)*TW/2, (gx+gy)*TH/2)`,
  역투영 = `gx=round((rx+ry)/2), gy=round((ry-rx)/2)`. **하네스가 TILE_W를 몰라도 되게 분리** → 골렘이 타일크기·origin을 바꿔도 프로브 불변(robust).
  검증 포인트 = `cell_to_screen(gx,gy)`에 클릭하면 정확히 (gx,gy)가 잡히는 왕복(round 역변환이 정확).
- **바닥 = 절차적 다이아몬드(타일 폐기)**: Tiny Dungeon 정사각 바닥 타일은 다이아몬드에 안 맞음 → `draw_colored_polygon`으로 마름모 fill+테두리(그리드).
  덤으로 v3에서 안 사라진 "갈색 가로띠 변주" 문제도 근본 소멸(타일 변주 자체를 안 씀). 유닛 스프라이트는 그대로 빌보드로 세움(+타원 그림자 = 2.5D 입체감).
- **깊이 정렬**: 유닛을 `gx+gy` 오름차순(화면 아래일수록 큰 값)으로 그려 앞 유닛이 뒤를 가림. v3 다듬기(HP바·데미지외곽선·트윈·죽은유닛·HUD띠)는 좌표만 cell_to_screen 기반으로 유지.
- **v3 결과(직전)**: 골렘이 강화 SCENE_SPEC을 1시도에 잘 따름(그리드라인·HP바·상단잘림 해소·데미지 외곽선 채택). 강화→재생성 루프가 작동함을 재확인 → 아이소도 같은 방식.

## omc 발상 이식 (2026-06-24) — 설치 X, 핵심 로직만 차용
- **배경**: omc(oh-my-claudecode, 36.8k★)는 Claude Code용 멀티에이전트 오케스트레이션. 설치 대신 패턴만 golem 루프에 흡수(2→1→3 순서).
- **#2 함정 자동주입(skills auto-inject)**: SCENE_SPEC에 흩어지던 공통 GDScript 함정을 `godot/GDSCRIPT_PITFALLS.md`로 추출 → `godot_port_scene.py`가 모든 생성 프롬프트에 자동 주입. board.gd 너머 재사용 자산. 새 함정은 여기에 쌓는다.
- **#1 증분 분해(team-plan/Ralph)**: 한 재생성=새 기능 1개. 3기능(사거리영역+화살표+자동전투) 동시는 12회 실패, 자동전투 하나로 줄이자 1시도 통과. 나머지는 "※ 다음 증분"으로 보류 표시. 메모리 [[golem-one-increment-per-regen]].
- **#3 진단→수정 피드백(UltraQA)**: 게이트 실패 에러를 분류해 위반 함정을 콕 집어 되먹임(다음 작업).
- **자동전투(v7) 채택**: 위 #1로 자동전투만 재생성 → 1시도 통과. auto_step() 그리디 정책으로 아군 자동 구동, update_state로 턴 진행, 결정적 종료(2회 재현 일치 프로브). 사거리영역(v5)·화살표(v6)는 다음 증분.

## 검증 하네스 강화 (2026-06-23, G97) — 외부 리뷰 수용, 클로드 하네스 키0
- **배경**: 외부 리뷰 = "룰 골든은 강하나 최종 산출물 Web/iPhone 경로가 자동 보호 안 됨, 입력 프로브가 느슨". 멀티에이전트 프레임워크는 도입 X(자체 하네스 유지), 검증·선별만 강화. 지적 6건 전부 코드와 대조해 일치 확인 후 처리.
- **Phase 1 — 입력 프로브 정밀화**: 옛 `run_input_probe.gd`는 `if selected_unit_id != null or turn != before_turn`이라 선택만 성공해도 통과했고, 실패해도 `quit()`=exit 0이라 non-zero 종료가 없었다. 하네스도 문자열("입력 로직 동작함")만 grep. → 선택·이동·공격을 각각 구조화 비교(PROBE_JSON expected vs actual), 불일치 시 quit(1). 기대값은 런타임 도출(atk/pos에서 계산)이라 미션 데이터 값 변화에 강함.
- **Phase 2 — fixture 분리**: 프로브가 미션0 배치(ally2 range2→enemy2 사거리쌍)에 의존하던 문제. `test/fixtures/*.json` 6종(기능 하나씩, 룰엔진 시뮬레이션으로 결정적 기대값). 핵심 설계 = **board.levels=[fixture] 주입 후 load_mission(0)** → board.gd(골렘 저작) 미수정으로 임의 상태 로드. 저자분리 유지. 적 AI가 아군 턴마다 도는 엔진이라 "다른 유닛 불변"은 불가 → expect에 명시한 필드만 검증(focused). 음성테스트(틀린 fixture→exit 1)로 게이트 실효성 확인.
- **게이트 배선**: `godot_port_scene.py`가 문자열 grep→**종료코드** 판정, run_fixture 단계 편입(스모크→입력프로브→fixture→자동→렌더). 실패 시 PROBE_JSON/FIXTURE_JSON의 got/want을 골렘에 되먹임.
- **Phase 3 — Godot CI**: keyless.yml은 Python·Node만, Godot 0건이라 rules.gd 파싱·board 런타임·Web export 고장이 main에 그대로 들어갈 수 있었다. `godot.yml` 분리 신설(godot/** 경로 게이트). windowed 렌더 캡처는 디스플레이 필요라 CI 제외(로컬 게이트 유지). Godot 4.7 linux URL은 첫 런에서 확정.
- **Phase 6 — 역할정의**: GolemStudioMode.md "아트·음악·UI 폼은 사람 몫"이 HANDOFF "외형도 골렘이"와 충돌 → 4자 분리(원본에셋=사람/Claude, 배치·화면·UI·이펙트 저작=GOLEM, 사양·계약·하네스·증거=Claude, 미관·조작감·재미 판정=사용자).
- **다음 갈림길(Phase 4)**: Playwright WebKit E2E. `window.GOLEM_TEST` 읽기전용 상태노출이 board.gd 변경을 요구 → 골렘 ★키(SCENE_SPEC 경유) vs JS 브리지. 저자분리상 클로드가 board.gd 직접 못 고치므로 사용자 결정 필요. npm 설치도 환경 액션이라 go 전제.

## Phase 4 — Playwright E2E + 상태 브리지 (2026-06-23, G97 후속)
- **사용자 선택**: "GOLEM_TEST 상태훅까지"(board.gd 변경=★키로 제시함). 하지만 더 안전한 길로 동일 목표 달성 — board.gd를 ★키로 통째 재생성하면 G96 아이소+자동전투를 잃을 리스크가 있어, **읽기전용 autoload `test_bridge.gd`로 분리**(board.gd 미변경·키0). 저자분리상 테스트 증거 수집은 Claude 몫이라 더 깨끗(board.gd=순수 게임, 브리지=증거). board에 골렘이 직접 박길 원하면 그때 ★키 전환.
- **브리지 안전장치**: ① `set_process(OS.has_feature("web"))` — 데스크톱/헤드리스 완전 비활성 ② 헤드리스 프로브는 `extends SceneTree`라 autoload 자체를 로드 안 함(이중 안전) ③ web에서도 `?test=1` 없으면 첫 프레임 후 영구 비활성 ④ board 상태를 읽기만(절대 수정X). → 골든·프로브·프로덕션에 0 영향(재확인 PASS).
- **E2E 설계**: auto_mode 기본 true라 미션 진입 시 자동전투가 돈다 → 메뉴 탭(MENU→BRIEFING→PLAYING)이 "터치→상태변화" 증거, 이후 자동전투 turn 증가·RESULT 종료를 GOLEM_TEST로 관찰. 수동 move/attack 정밀검증은 이미 헤드리스 프로브/ fixture가 결정적으로 담당 → E2E는 web/브라우저/터치변환/WASM 층만 책임(역할 분리).
- **좌표 변환**: 게임 논리 640x640(stretch aspect=keep)을 캔버스 boundingBox에 uniform scale·centered로 매핑해 탭. 헤드리스 WebKit(ANGLE) GL 경고(glBlitFramebuffer)는 양성 노이즈라 필터(실 iPhone Safari Metal에선 안 남, 최종은 사람 oracle). verdict.json이 verified(자동) vs human_review_required(미관·조작감·재미) 분리 — 자동이 재미를 통과했다 주장 안 함.
- **남음**: Phase 5 시각스냅샷(proof/ 인프라 있음)·Phase6-퍼징(fast-check, 카드 증가 후)·godot.yml 첫 CI 런에서 Godot 4.7 다운로드 URL·webkit deps 확정.

## G98 — 차등 퍼징 + 공격 화살표 증분 + 시각 스냅샷 (2026-06-23, "둘 먼저하고 페이즈5")
- **차등 퍼징(Phase 6)**: 36스텝 골든은 고정 시나리오뿐인데 rules.gd엔 7개+ 상호작용 메커닉이 있어 미검증 조합 공간이 실재. fast-check 대신 **시드 PRNG 파이썬 생성기**(npm·Math.random 없이 결정적 재현 — 프로젝트 ethos 정합)로 무작위 유효+엣지(존재않는 unit·경계·무사거리) 케이스 생성. JS 엔진(squad_base_l8/game_logic.js)이 정답, godot_export_golden의 TRACE_JS 재사용(DRY). run_fuzz_diff.gd가 _fuzz_cases.json(gitignore 스크래치)을 rules.gd로 재생 비교. 6000케이스 ALL MATCH로 포팅 동치 입증.
- **공격 화살표(G96 병행 증분, ★키)**: 한 재생성=한 기능. SCENE_SPEC v8만 활성, 사거리 영역은 보류 유지. 화살표는 effects 배열 표시 전용(state 0영향)이라 입력/fixture/자동/골든/퍼징 전부 불변 — 그래서 board 재생성이 안전했고 1시도 통과. 근접 draw_line·원거리 draw_polyline 포물선(PackedVector2Array append, '+' 금지 함정 준수). Phase 1-2의 fixture 게이트가 이 재생성을 더 안전하게 받쳐줌(입력 회귀 자동 차단).
- **시각 스냅샷(Phase 5) — 보수적 범위**: 자동전투·이펙트·트윈이 도는 PLAYING/RESULT는 프레임 비결정이라 픽셀 비교 부적합 → 정적 MENU·BRIEFING만 대상. 환경별 baseline 분리(Playwright 플랫폼 접미사 -win32/-linux). 로컬 win32만 커밋, CI linux는 비차단으로 생성·artifact → 사람이 채택(문서의 "동일환경 기준이미지·명시적 갱신" 원칙 정합). 하드게이트 전환은 linux baseline 커밋 + --update-snapshots 제거 한 줄.
- **판단**: 외부 리뷰 요청은 G97+G98로 사실상 완결(완료기준 섹션10 전부·CI green). 시각만 "비차단→채택 시 게이트"로 단계 남김(외형이 아직 증분 중이라 의도적).

## G99 — 시각 하드게이트 채택 + 사거리영역 v9 + 브리핑 회귀/게이트갭 (2026-06-23)
- **시각 하드게이트**: linux 기준이미지(CI artifact)를 커밋하고 godot.yml 시각 스텝에서 --update-snapshots 제거 → 픽셀 회귀 비교 게이트. 첫 CI 런에서 통과 확인.
- **사거리 영역 v9(★키)**: 선택 아군의 공격 reach 전체를 옅은 빨강 반투명 fill. 표시 전용(state 불변). 골렘 1시도 통과.
- **★ 브리핑 회귀 — 게이트 갭 발견**: 사거리영역 재생성이 BRIEFING을 메뉴로 그리는 회귀를 냈다. 로컬 게이트(스모크·입력프로브·fixture·자동·렌더캡처)는 **브리핑을 안 봤다** — load_mission(0)이 메뉴/브리핑을 우회하고, capture_attack.gd도 MENU+공격만 캡처. 그래서 회귀가 게이트를 통과해 커밋·푸시됐고, **시각 CI 게이트(briefing 12% diff)만 잡았다**. 채택한 첫 하드게이트가 바로 값을 했다.
- **수습(게이트 갭 영구 차단)**: capture_attack.gd가 MENU→탭→BRIEFING을 캡처하고 두 화면 픽셀 차이율(BRIEFING_DIFF_RATIO)을 출력. godot_port_scene.run_render가 ratio<0.03이면(브리핑이 메뉴와 거의 동일=브리핑 안 그림) 게이트 실패. 개선 게이트로 재롤 → 브리핑 복원(diff 0.32, 반투명 박스+본문+탭하여 시작)·CI 완전 green.
- **교훈**: ① GOLEM 풀 재생성은 명시 안 한 화면도 바꿀 수 있다 → 게이트는 모든 화면(_draw)을 봐야 한다(헤드리스 프로브는 load_mission 우회라 메뉴/브리핑 _draw를 영영 못 본다 — 렌더 캡처가 유일한 눈). ② 시각 하드게이트는 board가 자주 재생성되는 동안 의도적 외형 변경 시 기준이미지 갱신을 요구하지만(menu/briefing이 톨러런스 내면 통과), 그 대가로 _draw 회귀를 잡아준다 — 이번처럼.

## G100 — 덱 편성 단계 SQUAD_SELECT 착수 (2026-06-23, 클로드 키0 증분 ①②)
- **왜 지금**: 자동전투 절반은 됐으나 플레이어 결정이 0(관전 데모). 빠진 절반 = 전투 전 유닛 선택·배치(G96 사용자 본진). 이게 들어가야 "선택→자동전투" 루프가 닫히고 재미게이트·밸런스가 관전이 아닌 플레이어 결정을 평가한다.
- **증분 ① roster.json(키0)**: 보유 유닛 풀 6명. 필드는 rules.gd가 이미 읽는 카드필드(range/knockback/reflect_dmg/flank_bonus/aura_shield/phalanx_defense) 그대로 재사용 — 새 룰 0, 데이터만. id는 문자열(kael 등)이나 전투 진입 시 정수로 재부여(아래).
- **증분 ② SCENE_SPEC ★v10(키0)**: BRIEFING→SQUAD_SELECT→PLAYING. BRIEFING 클릭이 load_mission 직행 대신 SQUAD_SELECT로 간다(사람 진입 경로에만 편성 단계 삽입).
- **★ 핵심 불변 결정**: `load_mission(idx)`는 동작·시그니처 절대 불변(미션 고정 allies로 PLAYING 직행). 입력프로브·fixture·test_bridge가 전부 이 계약에 의존 — 프로브는 메뉴/브리핑을 우회하고 load_mission을 직접 부르므로 SQUAD_SELECT 추가가 프로브를 안 건드린다. 덱 편성은 `start_battle_with(ids)`라는 **새 진입 경로**로만 얹는다.
- **★ 정수 id 재부여 결정**: 적 AI 타이브레이크가 `a["id"] < b["id"]`다. 로스터 문자열 id를 그대로 넣으면 미션 골든(정수 id)과 의미가 갈린다. start_battle_with가 고른 순서대로 id=1..N 정수로 재부여 + pos=[0,i] 0열 배치 → 적 AI 타이브레이크가 기존 미션과 동일하게 동작. 카드필드는 보존.
- **squad_size**: levels[pending_idx].initialState.allies.size()(현재 전부 2)만큼 정확히 고르게. 밸런스를 미션이 기대한 아군 수에 맞춤.
- **공통 마감 헬퍼 제안**: load_mission과 start_battle_with가 state 마감(turn=0/status/selected null/auto 리셋/screen=PLAYING)을 공유하므로 `_enter_battle(init)` 헬퍼로 빼되 load_mission 외부 동작은 불변.
- **남은 것(다음)**: ③ board.gd ★키 재생성(SQUAD_SELECT 화면 추가) → ④ 검증(골든·프로브·fixture·퍼징 전부 그대로 통과 확인)·SQUAD_SELECT 화면 캡처 게이트·시각 기준이미지 갱신·커밋.

## G101 — SQUAD_SELECT 코스트 예산 + 씬 증분 모드(--incr) (2026-06-23, 클로드 키0 사양/하네스 + 골렘 ★키 board)
- **코스트 메커니즘**: 유닛 cost(roster.json) + 미션 공통 cost_budget(7). 편성 = squad_size명 + cost합 ≤ budget. 강한 유닛이 비싸 트레이드오프(kael4+ria4=8 막힘, 협공 vire2가 인에이블러). cost는 편성 메타라 룰·골든 불변.
- **★ 핵심 교훈 — 풀 scratch 재생성의 회귀**: cost를 풀 scratch(`--cap`)로 두 번 시도(cap4, cap5) 했더니 9시도 중 대부분이 cost와 무관한 PLAYING 로직(선택null·이동 후 선택해제·VICTORY/DEFEAT→RESULT 전환 누락·pos!=Vector2 함정)을 회귀시켰다. 골렘이 board 전체를 매번 새로 쓰니 이미 통과한 부분이 흔들린다(G99 브리핑 회귀와 동형, 더 심함).
- **수습 = `--incr` 증분 모드(godot_port_scene.py)**: 검증된 현재 board.gd를 프롬프트에 base로 넣고 "새 기능만 최소 변경, 나머지(선택/이동/execute_action/load_mission/start_battle_with/RESULT 전환) byte-identical 유지" 지시. 실측: incr 4/4가 PLAYING 보존하고 cost만 추가. omc 증분분해를 코드화한 것. **규칙: board에 기능 더할 땐 git restore로 검증본 두고 --incr.**
- **diagnose 함정 2개 추가**: "already declared in this scope"(변수 중복, tw/th 같은 임시변수 충돌) · "Invalid operands Array Vector2"(pos를 Vector2와 직접 비교).
- **캡처 SQUAD_BATTLE_OK 수정**: 로스터 앞 2개(kael+ria=8>budget)를 쓰면, 모델이 start_battle_with 안에 예산검사를 넣은 경우 거부당해 false-fail. cost 오름차순 2명(예산 내)으로 바꿔 어느 구현이든 통과하게.
- **★ 윈도 렌더 게이트 플레이키(미해결)**: run_render(windowed) 배치 실행이 SQUAD_BATTLE_OK를 false로 잘못 냄 — 같은 board 단독 수동 실행은 통과. G100·G101 둘 다. 1회 재시도 넣었지만 배치 경합 여전. board 채택은 개별 수동 게이트로 판정(이번에도 그렇게 확정·채택).
- **시각 기준 갱신 불필요**: cost 텍스트 추가분이 시각 임계(maxDiffPixelRatio 0.02) 안 → win32 비교게이트 3/3 통과, squad-win32.png 무변경. linux도 CI 하드게이트로 확인.

## G102 — SQUAD_SELECT 스프라이트 카드 + --incr echo 차단 (2026-06-23)
- **외형**: 유닛 카드 왼쪽에 스프라이트 썸네일(range>1 tex_mage/else tex_knight, 32x32 draw_texture_rect), 텍스트 우측 이동. PLAYING과 동일 스프라이트 규칙. 룰·골든·PLAYING 좌표 불변.
- **★ --incr echo 함정**: --incr로 두 번(스프라이트) 돌렸더니 모델이 base를 byte-identical로 그대로 반환 — 새 기능 0줄. "최소 변경/byte-identical 유지" 지시가 너무 강해 "아무것도 안 바꿈"으로 흘렀다. 게이트는 통과(SQUAD diff는 BRIEFING 대비라 squad-vs-이전-squad는 안 봄)라 안 걸림.
- **수습 3종(키0)**: ① 하네스가 생성물.strip()==base면 게이트 전에 거부·되먹임("동일 파일=실패"). ② BASE_BLOCK을 "반드시 새 기능 추가, 무관 로직만 보존"으로 재균형. ③ 사양에 draw_texture_rect 구체 코드 힌트. → 3번째 시도에서 스프라이트 실제 추가됨.
- **부수 변경(수용)**: 모델이 죽은 변수 TILE_W/origin 제거(project가 인라인 600/gridSize 계산이라 무영향) + 메뉴 제목 x 220→320 재중앙. 둘 다 시각 임계(2%) 안이라 기준이미지 무변경.
- **시각 기준 갱신 불필요**: 스프라이트(6장 32x32)+메뉴 제목 이동이 maxDiffPixelRatio 0.02 안. win32 비교게이트 3/3·git 기준 무변경. CI 하드게이트로 linux 확인.
