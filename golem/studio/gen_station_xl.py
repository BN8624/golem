# 대량 sensor 모듈을 찍어 station_xl(시그니처 다수) 카드·XL 패킷·골든을 생성한다 — B 입력 lost-in-the-middle 측정용(키0)
"""레버4 B(선택주입)는 held-out를 시그니처만 보내므로, 입력 천장을 치려면 모듈을 대량으로 늘려야 한다.
station_base(46모듈)를 복사하고 결정적 sensor 모듈 N개를 추가해 시그니처 블록을 크게 만든다.

sensor 모듈은 측정용 더미다(사용자 합의): 본문은 turn 스케줄 PING 로그 한 줄뿐 — 결정적·배선됨·live
(각 sensor는 turn==(idx%3)+1에 로그 → SCN-001이 turn1~3을 PLAYING으로 다 틱해 전부 최소 1회 발화 =
죽은코드 아님. 시나리오들이 WON/LOST로 turn8 이전 조기종료하므로 T는 모든 시나리오가 도달하는 1~3로 좁힘).

산출(전부 gitignore):
  station_xl/                         = station_base + sensorNNN.js N개, systems/manifest/contract ORDER 배선
  planning_packet_station_xl/         = station_l 계약 + RULE-02 ORDER를 XL용으로 교체
  specqa_packet_station_xl/           = 골든(참조 engine node 역산, station_l과 동일 시나리오10)

사용: python gen_station_xl.py [N]   (기본 N=500)
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import gen_station_l_golden as G  # REF_ENGINE·SCENARIOS·REGRESSION·parse_expected 재사용

HERE = Path(__file__).resolve().parent
BASE = HERE / "station_base"
XL = HERE / "station_xl"
PKG_PLAN_L = HERE / "planning_packet_station_l"
PKG_PLAN_XL = HERE / "planning_packet_station_xl"
SPECQA_XL = HERE / "specqa_packet_station_xl"

SENSOR_TMPL = """// 정거장 센서{n:03d} — 결정적 ping 로그(스케일 측정용 더미, turn 스케줄)
exports.step = (state, c) => {{
  if (state.turn === {t}) state.log.push('PING{n:03d}');
  return state;
}};
"""


def build_xl(count):
    if XL.exists():
        shutil.rmtree(XL)
    shutil.copytree(BASE, XL)

    names = [f"sensor{i:03d}" for i in range(count)]
    for i, nm in enumerate(names):
        (XL / "src" / f"{nm}.js").write_text(
            SENSOR_TMPL.format(n=i, t=(i % 3) + 1), encoding="utf-8")

    # systems.js: require + ORDER에 sensor 삽입(derive 앞).
    sysf = XL / "src" / "systems.js"
    s = sysf.read_text(encoding="utf-8")
    req_block = "".join(f"const {nm} = require('./{nm}');\n" for nm in names)
    s = s.replace("const derive = require('./derive');",
                  req_block + "const derive = require('./derive');", 1)
    order_block = "".join(f"  {nm},\n" for nm in names)
    s = s.replace("  derive,\n  report,\n];",
                  order_block + "  derive,\n  report,\n];", 1)
    sysf.write_text(s, encoding="utf-8")

    # manifest: files에 sensor 항목 + systems imports에 sensor 추가.
    manf = XL / "module_manifest.json"
    man = json.loads(manf.read_text(encoding="utf-8"))
    for f in man["files"]:
        if f["path"] == "src/systems.js":
            idx = f["imports"].index("src/derive.js")
            f["imports"][idx:idx] = [f"src/{nm}.js" for nm in names]
    insert_at = next(i for i, f in enumerate(man["files"]) if f["path"] == "src/derive.js")
    man["files"][insert_at:insert_at] = [
        {"path": f"src/{nm}.js", "exports": ["step"], "imports": []} for nm in names]
    manf.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    return names


def build_packet(names):
    if PKG_PLAN_XL.exists():
        shutil.rmtree(PKG_PLAN_XL)
    shutil.copytree(PKG_PLAN_L, PKG_PLAN_XL)
    cf = PKG_PLAN_XL / "contract.json"
    c = cf.read_text(encoding="utf-8")
    # RULE-02 ORDER 열거에 sensor를 derive 앞에 끼운다(계약 일관).
    sensors = ", ".join(names)
    c = c.replace("habitat, airlock, coolant, attitude, waste, derive, report)",
                  f"habitat, airlock, coolant, attitude, waste, {sensors}, derive, report)", 1)
    cf.write_text(c, encoding="utf-8")


def build_golden():
    ref = HERE / "_station_xl_ref_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(XL, ref)
    (ref / "src" / "engine.js").write_text(G.REF_ENGINE, encoding="utf-8")

    inputs = [{"input": s["input"]} for s in G.SCENARIOS]
    (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    (XL / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    for i, s in enumerate(G.SCENARIOS, 1):
        ref_out = G.run(ref, i)
        expected = G.parse_expected(ref_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        if s["id"] in G.REGRESSION:
            base_out = G.run(XL, i)
            regression_ok = regression_ok and (base_out == ref_out)

    SPECQA_XL.mkdir(parents=True, exist_ok=True)
    (SPECQA_XL / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA_XL / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False, "reason": "XL 스케일 프로브 — 골든 node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    (XL / "scenarios.json").unlink(missing_ok=True)
    shutil.rmtree(ref)
    return regression_ok, out


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    names = build_xl(count)
    build_packet(names)
    regression_ok, out = build_golden()

    total_modules = len(list((XL / "src").glob("*.js"))) + 1
    statuses = {s["id"]: s["expected"]["gameStatus"] for s in out}
    print(f"sensor {count}개 추가 → 총 {total_modules}모듈")
    print(f"회귀 무결(base==ref): {regression_ok}")
    print("gameStatus:", {k: v for k, v in statuses.items()})
    return 0 if regression_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
