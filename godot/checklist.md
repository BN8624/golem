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
- [ ] (다음 다듬기) 0행 hp라벨 화면밖 잘림, 바닥 변주 가로띠, 이동/넉백 트윈, hp 바

## Phase 4 — 확장(선택)
- [ ] 고도+골렘 루프로 카드/레벨 확장, 재미 게이트 적용 검토
