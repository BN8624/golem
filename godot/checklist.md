# Godot 이식 체크리스트 (squad 전술 → Godot)

## Phase 0 — 준비 (클로드 키0, 고도 불필요)
- [x] `golem/tools/godot_export_golden.py` — JS 엔진으로 골든 추출기
- [x] `godot/test/rules_golden.json` — 솔루션 4미션 + 엣지 10케이스(36스텝), node 생성·검증
- [x] `godot/project.godot` — Godot 4 프로젝트 골격
- [x] `godot/data/squad_levels.json` — 미션 복사(res://)
- [x] `godot/test/run_rules_golden.gd` — 커스텀 골든 대조 러너(미검증, 고도 설치 후 실행)
- [x] `godot/PORTING_SPEC.md` — 골렘 포팅 사양(인터페이스·불변식·검증)

## Phase 1 — 룰 포팅 (골렘 ★키 → 클로드 검증 키0, 고도 필요)
- [x] (클로드) Godot 4.7 설치(C:/Users/USER/godot-engine) + 포팅 하네스 godot_port_rules.py
- [x] (골렘 ★키) `godot/scripts/rules.gd` 포팅 — 1시도 채택
- [x] (클로드 키0) 헤드리스 골든 러너 → **36/36 통과, 0 실패**(독립 재실행도 동일)
- [x] 검증된 JS와 0-diff 동치 증명

## Phase 2 — 플레이 가능한 씬 (골렘 ★키 + 클로드 배관, 고도 필요)
- [x] (클로드) scenes/main.tscn 래퍼 + SCENE_SPEC + 스모크 하네스 godot_port_scene.py
- [x] (골렘 ★키) `scripts/board.gd` — 렌더·선택→이동/공격·턴 진행(rules.gd 호출)·승패. 2시도 채택(1시도 get_default_font 에러→되먹임 수정)
- [x] (클로드) 헤드리스 스모크 통과(SCRIPT ERROR 없음)
- [x] (클로드) 웹 export + 테일스케일 HTTPS(`tailscale serve --https=443`)로 아이폰 보안 컨텍스트 충족
- [x] (클로드) **클릭 무반응 버그 수정** — JSON float `pos`와 int `[gx,gy]` 배열 비교가 항상 false라 클릭이 전부 죽어 있던 것. 원소별 비교로 수정. 헤드리스 입력 프로브(`run_input_probe.gd`)로 선택+이동 결정적 검증. project.godot에 stretch/viewport 640·터치에뮬 추가.
- [ ] (사용자) 아이폰에서 유닛 탭·이동·공격 확인 ← 지금 여기

## Phase 3 — 미션선택 + 서사 (사용자 선택, 골렘 ★키)  ✅
- [x] (클로드 키0) 서사 하네스 godot_gen_narrative.py — 미션 메타 주고 story JSON 받아 검증·병합
- [x] (골렘 ★키) 4미션 story(briefing/victory/defeat) 생성 → squad_levels.json 병합, 골든 36/36 유지
- [x] (클로드 키0) SCENE_SPEC v2 + 입력프로브 채택 게이트(load_mission/state/_unhandled_input 계약)
- [x] (골렘 ★키) board.gd 재생성 → 스모크 + 입력프로브 통과(get_default_font→fallback, draw_string 시그니처는 클로드가 실렌더 캡처로 바로잡음)
- [x] (클로드) 캡처로 메뉴·브리핑·플레이 실렌더 확인 + 웹 export

## Phase 3.5 — 그림 에셋 + 맵·이펙트 (외형은 골렘이 저자, 클로드는 에셋·검증)  ✅
- [x] (클로드 배관) Tiny Dungeon(Kenney, CC0)·나눔고딕(OFL) 다운로드·import, contact sheet로 타일 식별
- [x] (클로드 배관) 웹 한글 깨짐 → 나눔고딕 임베드. 분업 교정 — 클로드가 _draw 직접 짠 건 위반(사용자 지적)
- [x] (클로드 하네스) SCENE_SPEC v3 에셋 사양 + 맵/이펙트 요구 + 함정(좌표계·draw_string·draw_set_transform·id충돌) + **렌더 캡처 채택 게이트**
- [x] (골렘 ★키) board.gd 외형 재생성 — 스프라이트·미션별 맵 톤·데미지텍스트·플래시·하이라이트. 게이트가 미관 못 잡는 미세버그(draw_set_transform 색오용·고정cell·id충돌 빨강)를 캡처로 잡아 사양 보강·되먹임 3회 → 채택
- [x] (클로드 하네스+골렘 ★키) v3 다듬기 — SCENE_SPEC에 사양화 후 골렘 1시도 게이트 통과 재생성. 상단 hp라벨 잘림 제거(셀 안 HP바)·그리드라인·데미지 외곽선 채택. 바닥 변주 갈색띠는 일부만 줄어듦. 커밋 cbad05b

## Phase 3.6 — 아이소메트릭 2.5D 전환 (사용자 요청 B, 2026-06-24)
- [x] (클로드 하네스) 좌표 계약을 탑다운→아이소로 교체 — board가 `cell_to_screen(gx,gy)` 단일 진실원천 노출, 클릭은 역투영. SCENE_SPEC v4 섹션(절차적 다이아몬드 바닥·깊이정렬·빌보드+그림자·다이아 하이라이트) 추가
- [x] (클로드 하네스) 입력프로브·캡처 스크립트를 `board.cell_to_screen` 호출로 분리(하네스가 TILE_W 모르게)
- [x] (골렘 ★키) board.gd 아이소 재생성 → 게이트 통과(시도2). 그림자 draw_set_transform 함정 교정·납작타원·세로중앙정렬·정수데미지 되먹임(d82cdc6→8b87178)
- [x] (클로드) 아이소 캡처 확인·되먹임. 유닛 겹침은 레벨 클러스터링(데이터)이라 외형 밖 — opposing-sides는 별도

## Phase 3.7 — 자동 전투(AUTO) + omc 패턴 이식 (사용자 방향, 2026-06-24)
- [x] (클로드 하네스) SCENE_SPEC v7 AUTO 사양(auto_step·그리디 정책·결정성) + auto_step 계약 + run_auto_probe.gd + 게이트 배선
- [x] (골렘 ★키) board.gd 자동전투 재생성 → 1시도 통과(증분=자동전투만). 채택 ec9b661
- [x] (클로드) [omc#2] 함정 자동주입 — GDSCRIPT_PITFALLS.md + port 프롬프트 주입(b7c0465)
- [x] (클로드) [omc#1] 증분분해 규칙(메모리+노트) · [omc#3] diagnose 진단피드백(41a4a08)
- [ ] (다음 증분, 하나씩) 공격 화살표 v6 / 사거리 영역 v5 / 자동전투 아이폰 export / opposing-sides 레이아웃(+골든 재추출·프로브 move-then-attack 보강)
- [ ] (큰 그림) 덱 편성 단계 — 브라운더스트2/트릭컬식. 자동전투 위에 전투 전 유닛 선택·배치

## Phase 3.8 — 검증 하네스 강화 (외부 리뷰 수용, 2026-06-23, 클로드 하네스 키0)
- [x] (대조) 외부 리뷰 5.1/5.2/5.3/5.4/5.5/6 지적이 전부 현재 코드와 일치 확인
- [x] (Phase 1) `run_input_probe.gd` 정밀화 — 선택·이동·공격 구조화 비교(expected vs actual JSON), 불일치 시 quit(1). 느슨한 OR 조건·문자열 grep 제거. 미션0 통합 테스트로 유지
- [x] (Phase 2) `run_fixture_probe.gd` + `test/fixtures/{select,move,attack,victory,defeat,edge_cases}.json` — 미션0 비의존 기능 단위 계약. board.levels 주입이라 board.gd(골렘) 미수정
- [x] (Phase 1/2 게이트) `godot_port_scene.py`가 종료코드로 PASS 판정 + fixture 단계 편입. 음성테스트(틀린 fixture→exit 1) 확인. replay 게이트·keyless ALL PASS
- [x] (Phase 3) `.github/workflows/godot.yml` — Godot 4.7 import→골든→입력프로브→fixture→Web export→필수파일 검증. keyless.yml과 분리, godot/** 경로 게이트
- [x] (Phase 6) GolemStudioMode.md 외형 저작 역할 정의를 Godot 트랙과 정합(충돌 해소)
- [ ] (Phase 4, 갈림길) Playwright WebKit/iPhone E2E — npm 설치 필요. `window.GOLEM_TEST` 읽기전용 상태노출은 board.gd 변경=골렘 ★키 SCENE_SPEC 경유 vs JS 브리지 결정 필요(저자분리)
- [ ] (Phase 5) 시각 스냅샷(화면 구조 안정 후, 동일 환경 기준이미지)
- [ ] (Phase 6-퍼징) fast-check JS↔GDScript 차등 퍼징(카드·룰 증가 후)

## Phase 4 — 확장(선택)
- [ ] 고도+골렘 루프로 카드/레벨 확장, 재미 게이트 적용 검토
