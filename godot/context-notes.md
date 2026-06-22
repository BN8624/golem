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
