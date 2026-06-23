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
