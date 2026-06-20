# 빌드 게이트가 첫 시나리오뿐 아니라 모든 시나리오의 비정상 종료를 잡는지 키0으로 검증한다(외부리뷰 #2 회귀잠금)
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_graded as bg
from parse_write import write_candidate

try:
    from config import force_utf8_stdout
    force_utf8_stdout()
except Exception:  # noqa: BLE001
    pass

BASE = HERE / "rocket_base"
contract, concept, manifest, sysd, scenarios, risk = bg.load_all(
    HERE / "planning_packet_rocket", BASE, HERE / "specqa_packet_rocket")
manifest_v = {"schema_version": "0.1", "module_format": "commonjs", **manifest}
grading_keys = {"id", "expected", "oracle_risk", "covers_reqs"}
scen_inputs = [{k: v for k, v in s.items() if k not in grading_keys} for s in scenarios]


def make_ws(crash_scn=None):
    """rocket_base를 워크스페이스로 쓰되, crash_scn이 주어지면 그 시나리오 번호에서 main.js가 비정상 종료하도록 주입한다."""
    ws = HERE / "build_runs" / "_gate_test" / "workspace"
    if ws.parent.exists():
        shutil.rmtree(ws.parent)
    ws.mkdir(parents=True)
    files = {p.relative_to(BASE).as_posix(): p.read_text(encoding="utf-8")
             for p in sorted(BASE.glob("**/*.js"))}
    if crash_scn is not None:
        inj = (f"const _i=process.argv.indexOf('--scenario');"
               f"if(_i>=0 && process.argv[_i+1]==='{crash_scn}')"
               f"{{throw new Error('injected crash SCN{crash_scn}');}}\n")
        files["main.js"] = inj + files["main.js"]
    write_candidate(ws, files)
    (ws / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")
    return ws


checks = []
ok1, reason1, _ = bg.gate_and_run(make_ws(), manifest_v, scenarios)
checks.append(("정상 빌드 게이트 통과", ok1))

# 중간(SCN2) 크래시 — 픽스 전엔 i==1만 검사해 통과했음. 이제 거부해야 함.
ok2, reason2, _ = bg.gate_and_run(make_ws(crash_scn="2"), manifest_v, scenarios)
checks.append(("SCN2 크래시 → 게이트 거부", (not ok2) and "SCN2" in reason2))

print(f"정상: ok={ok1} ({reason1})")
print(f"SCN2 주입: ok={ok2} ({reason2})")
print("\n=== 검증 ===")
allok = True
for name, res in checks:
    print(f"  [{'OK' if res else 'FAIL'}] {name}")
    allok = allok and res
print("\nRESULT:", "ALL PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
