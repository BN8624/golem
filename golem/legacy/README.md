# legacy/ — 과거 실험 아카이브 (본선 아님·정본 아님)

여기 파일들은 옛 game-bank / 오라클 설계 / 카드뱅크 흐름의 실험 코드다. **현재 본선(전술 SRPG)과 무관**하고 live 코드가 import하지 않는다(분리 검증: `verify_tactics.py` 통과). 참고용으로만 둔다 — 새 작업은 여기서 시작하지 말 것.

- `driver.py`·`worker_prompt.py` — 옛 단발 빌드 흐름(순수 헬퍼는 `../parse_write.py`로 분리됨).
- `game_bank.py`·`bank_init.py`·`bank_add_*.py`·`bank_remodularize_p3.py` — 게임뱅크 적재 실험.
- `oracle_design*.py`·`make_golden.py`·`promote_solution.py`·`design_probe.py`·`key_probe.py`·`demo_part.py`·`campaign.py` — 옛 설계/골든/승격 실험.

루트에 남은 live: `parse_write.py`(FILE 마커 헬퍼)·`static_gate.py`·`oracle.py`+`grade.py`(--reconcile 경로, lazy). 정본은 저장소 루트 `../../README.md` 참조.
