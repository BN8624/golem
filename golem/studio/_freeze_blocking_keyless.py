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


checks = [
    ("BLOCKING 0 → FROZEN", freeze(0)["frozen"] is True),
    ("BLOCKING 3·결정 1 → OPEN(핵심 버그)", freeze(3, decisions=1)["frozen"] is False),
    ("BLOCKING 3·흡수 3(1+1+1) → FROZEN", freeze(3, decisions=1, assumed=1, deferred=1)["frozen"] is True),
    ("BLOCKING 2·결정 1 → 미해소 1 보고", freeze(2, decisions=1)["blocking_open"] == 1),
    ("BLOCKING 3·흡수 3 → 미해소 0", freeze(3, decisions=3)["blocking_open"] == 0),
]

print("=== 검증 ===")
allok = True
for name, res in checks:
    print(f"  [{'OK' if res else 'FAIL'}] {name}")
    allok = allok and res
print("\nRESULT:", "ALL PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
