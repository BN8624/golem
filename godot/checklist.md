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
- [ ] (골렘) `scenes/main.tscn` + 보드 렌더(도형)·유닛 선택→이동/공격 입력·턴 진행(rules.gd 호출)·승패 표시
- [ ] (클로드) 씬 로딩·헤드리스 스모크
- [ ] (사용자) F5로 미션1 플레이·피드백

## Phase 3 — 4미션 + 외형
- [ ] 미션 선택 UI → 4미션 플레이
- [ ] 에셋(도형→그림): 골렘 CC0 선택 + 클로드 import 배관
- [ ] 서사 한 겹

## Phase 4 — 확장(선택)
- [ ] 고도+골렘 루프로 카드/레벨 확장, 재미 게이트 적용 검토
