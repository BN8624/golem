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
