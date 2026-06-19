# FROZEN 판정이 BLOCKING 질문 수만큼 흡수됐는지 검사하는지 키0으로 검증한다(외부리뷰 #1 회귀잠금)
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import planning

try:
    from config import force_utf8_stdout
    force_utf8_stdout()
except Exception:  # noqa: BLE001
    pass


def freeze(n_block, decisions=0, assumed=0, deferred=0):
    """최소 입력으로 _write_packet을 돌려 frozen 판정만 뽑는다."""
    issues = {"BLOCKING_questions": [f"q{i}" for i in range(n_block)]}
    packet = {"decisions": [f"d{i}" for i in range(decisions)],
              "assumed": [f"a{i}" for i in range(assumed)],
              "deferred": [f"f{i}" for i in range(deferred)],
              "data_contract": {}, "interface_contract": {"files": []}, "acceptance_tests": []}
    out = Path(tempfile.mkdtemp())
    try:
        return planning._write_packet("t", "", [], issues, packet, out)
    finally:
        shutil.rmtree(out, ignore_errors=True)


def freeze_explicit(blocking, decisions=0, assumed=0, deferred=0):
    """BLOCKING 질문 문자열을 명시 지정해 _write_packet 판정을 뽑는다(중복 dedup 검증용)."""
    issues = {"BLOCKING_questions": list(blocking)}
    packet = {"decisions": [f"d{i}" for i in range(decisions)],
              "assumed": [f"a{i}" for i in range(assumed)],
              "deferred": [f"f{i}" for i in range(deferred)],
              "data_contract": {}, "interface_contract": {"files": []}, "acceptance_tests": []}
    out = Path(tempfile.mkdtemp())
    try:
        return planning._write_packet("t", "", [], issues, packet, out)
    finally:
        shutil.rmtree(out, ignore_errors=True)


# 리뷰어 10명이 같은 BLOCKING을 각자 제기한 실제 케이스(G81): 같은 개념 5+2 = 원본 7, distinct 2.
_DUP_BLOCKING = (["target selection multiple enemies adjacent attack command"] * 5
                 + ["enemy movement deterministic priority axis tiebreak"] * 2)

checks = [
    ("BLOCKING 0 → FROZEN", freeze(0)["frozen"] is True),
    ("BLOCKING 3·결정 1 → OPEN(핵심 버그)", freeze(3, decisions=1)["frozen"] is False),
    ("BLOCKING 3·흡수 3(1+1+1) → FROZEN", freeze(3, decisions=1, assumed=1, deferred=1)["frozen"] is True),
    ("BLOCKING 2·결정 1 → 미해소 1 보고", freeze(2, decisions=1)["blocking_open"] == 1),
    ("BLOCKING 3·흡수 3 → 미해소 0", freeze(3, decisions=3)["blocking_open"] == 0),
    # G81: 중복 BLOCKING은 distinct로 접어 센다(중복이 분모를 부풀려 FROZEN 막던 결함)
    ("중복 7개 → distinct 2(dedup)", freeze_explicit(_DUP_BLOCKING)["blocking_distinct"] == 2),
    ("중복 7개·원본 보존 7", freeze_explicit(_DUP_BLOCKING)["blocking_raw"] == 7),
    ("중복 7개·흡수 2 → FROZEN(원본7이면 OPEN될 것)",
     freeze_explicit(_DUP_BLOCKING, decisions=2)["frozen"] is True),
    ("진짜 다른 2개·흡수 1 → OPEN(과대접힘 방지)",
     freeze_explicit(["alpha beta gamma delta", "epsilon zeta eta theta"], decisions=1)["frozen"] is False),
]

print("=== 검증 ===")
allok = True
for name, res in checks:
    print(f"  [{'OK' if res else 'FAIL'}] {name}")
    allok = allok and res
print("\nRESULT:", "ALL PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
