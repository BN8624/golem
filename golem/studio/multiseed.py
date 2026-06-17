# Golem Studio 정량 판정 Step1 — 한 카드 multi-seed로 빌드 합의 분포(평균·표준편차) 측정
"""build_graded.main을 같은 패킷으로 N회 재실행한다(온도 기본 = 샘플링 분산이 곧 시드).
각 런의 overall_agreement·게이트통과를 모아 분포를 낸다 — "0.762가 우연이냐, 재현되느냐"의
첫 정량 답. golden(오염 specqa) 무관한 빌드-간 합의만 보므로 --reconcile/--apply 안 쓴다(계약 불변).

사용:
  python golem/studio/multiseed.py --n 6 --cap 11        # ★키
"""

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_graded  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6, help="시드(재실행) 수")
    ap.add_argument("--cap", type=int, default=11)
    ap.add_argument("--packet", default=str(HERE / "planning_packet_combat"))
    ap.add_argument("--design", default=str(HERE / "design_packet_combat"))
    ap.add_argument("--specqa", default=str(HERE / "specqa_packet_combat"))
    args = ap.parse_args(argv)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "build_runs" / f"multiseed-{stamp}"
    base.mkdir(parents=True, exist_ok=True)
    print(f"[MULTISEED] N={args.n} cap={args.cap} card={Path(args.packet).name} → {base}\n")

    seeds = []
    for i in range(1, args.n + 1):
        out = base / f"seed{i:02d}"
        print(f"=== seed {i}/{args.n} ===")
        build_graded.main(["--packet", args.packet, "--design", args.design,
                           "--specqa", args.specqa, "--cap", str(args.cap),
                           "--out", str(out)])
        c = json.loads((out / "consensus.json").read_text(encoding="utf-8"))
        seeds.append({"seed": i, "overall_agreement": c["overall_agreement"],
                      "gate_passed": c["gate_passed"], "per_scenario": c["per_scenario"],
                      "failure_classes": c.get("failure_classes", {})})
        print(f"  → 합의 {c['overall_agreement']}, 게이트 {c['gate_passed']}/{args.cap}\n")

    agrees = [s["overall_agreement"] for s in seeds]
    gates = [s["gate_passed"] for s in seeds]
    summary = {
        "n": args.n, "cap": args.cap, "card": Path(args.packet).name,
        "agreement": {
            "mean": round(statistics.mean(agrees), 4),
            "stdev": round(statistics.stdev(agrees), 4) if len(agrees) > 1 else 0.0,
            "min": min(agrees), "max": max(agrees), "values": agrees},
        "gate_passed": {
            "mean": round(statistics.mean(gates), 2),
            "min": min(gates), "max": max(gates), "values": gates},
        "seeds": seeds}
    (base / "multiseed_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    a = summary["agreement"]
    print("=" * 56)
    print(f"[MULTISEED 결과] 합의 평균 {a['mean']} ± {a['stdev']} "
          f"(min {a['min']}, max {a['max']}, N={args.n})")
    print(f"  값: {agrees}")
    print(f"  게이트통과 {summary['gate_passed']['mean']} "
          f"(min {summary['gate_passed']['min']}, max {summary['gate_passed']['max']})")
    print(f"  B의 0.762는 이 분포의 {'안' if a['min'] <= 0.762 <= a['max'] else '밖'}.")
    print(f"[MULTISEED] → {base / 'multiseed_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
