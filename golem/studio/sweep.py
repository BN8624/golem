# Golem Studio 정량 Step3 — 같은 카드를 계약 타이트 단계별로 multi-seed 측정해 합의 곡선을 그린다
"""계약 빡빡함(축)을 한 칸씩 박으며 빌드 합의 분포를 잰다. 결합도가 아니라 계약 타이트가
합의를 정한다는 thesis(G55)를 같은 combat 카드 위에서 직접 증명하려는 것.

럽(loose→tight, design/specqa는 고정 = 1변수):
  L0 baseline  : RULE-10 종료조항 없음(planning_packet_combat_baseline)
  L1 terminate : +RULE-10 종료조항(planning_packet_combat)
  L2 phased    : +RULE-11 틱 PHASE 순서 명시(planning_packet_combat_phased, eco가 수렴한 그 장치)

각 럽 N회 재실행(온도 기본=시드) → 평균·표준편차. 인접 럽 간 Welch t·Cohen d로 상승/분포분리 판정.
multiseed.py와 같은 채점(빌드-간 합의, golden 무관, --reconcile 안 씀).

사용:
  python golem/studio/sweep.py --n 6 --cap 11        # ★키
"""

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_graded  # noqa: E402

# 럽 정의: (라벨, planning packet). design/specqa는 전 럽 공통(combat 원본) = 1변수.
RUNGS = [
    ("L0_baseline", "planning_packet_combat_baseline"),
    ("L1_terminate", "planning_packet_combat"),
    ("L2_phased", "planning_packet_combat_phased"),
]
DESIGN = "design_packet_combat"
SPECQA = "specqa_packet_combat"


def run_rung(label, packet, n, cap, base):
    """한 럽을 N시드 빌드해 채점 가능한 합의 분포를 모은다(multiseed와 동일 로직)."""
    seeds = []
    for i in range(1, n + 1):
        out = base / label / f"seed{i:02d}"
        print(f"  === {label} seed {i}/{n} ===")
        build_graded.main(["--packet", str(HERE / packet), "--design", str(HERE / DESIGN),
                           "--specqa", str(HERE / SPECQA), "--cap", str(cap), "--out", str(out)])
        c = json.loads((out / "consensus.json").read_text(encoding="utf-8"))
        seeds.append({"seed": i, "overall_agreement": c["overall_agreement"],
                      "gate_passed": c["gate_passed"], "voters": c.get("voters", {})})
        print(f"    → 합의 {c['overall_agreement']}, 게이트 {c['gate_passed']}/{cap}, "
              f"평균 {c.get('voters', {}).get('mean_voters', '?')}표")

    scorable = [s for s in seeds if s["overall_agreement"] is not None]
    agrees = [s["overall_agreement"] for s in scorable]
    voters = [s["voters"].get("mean_voters", 0) for s in scorable]
    gates = [s["gate_passed"] for s in seeds]
    return {
        "label": label, "packet": packet,
        "scorable_seeds": len(scorable),
        "agreement_mean": round(statistics.mean(agrees), 4) if agrees else None,
        "agreement_stdev": round(statistics.stdev(agrees), 4) if len(agrees) > 1 else 0.0,
        "agreement_min": min(agrees) if agrees else None,
        "agreement_max": max(agrees) if agrees else None,
        "agreement_values": agrees,
        "mean_voters": round(statistics.mean(voters), 2) if voters else 0,
        "gate_mean": round(statistics.mean(gates), 2), "gate_min": min(gates), "gate_max": max(gates),
        "seeds": seeds}


def welch(a, b):
    """인접 럽 b(tighter) vs a(looser) Welch t·df·p·Cohen d·분포겹침."""
    if len(a) < 2 or len(b) < 2:
        return {"note": "표본부족(한쪽 <2)"}
    t, p = stats.ttest_ind(b, a, equal_var=False)
    # pooled sd 기준 Cohen d
    na, nb = len(a), len(b)
    sa, sb = statistics.stdev(a), statistics.stdev(b)
    pooled = (((na - 1) * sa**2 + (nb - 1) * sb**2) / (na + nb - 2)) ** 0.5
    d = (statistics.mean(b) - statistics.mean(a)) / pooled if pooled else None
    overlap = max(a) >= min(b) and max(b) >= min(a)
    return {"delta_mean": round(statistics.mean(b) - statistics.mean(a), 4),
            "t": round(float(t), 3), "p": round(float(p), 5),
            "cohen_d": round(d, 3) if d is not None else None,
            "distributions_overlap": overlap}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6, help="럽당 시드 수")
    ap.add_argument("--cap", type=int, default=11)
    args = ap.parse_args(argv)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "build_runs" / f"sweep-{stamp}"
    base.mkdir(parents=True, exist_ok=True)
    print(f"[SWEEP] 계약타이트 곡선 N={args.n} cap={args.cap} → {base}\n")

    rungs = []
    for label, packet in RUNGS:
        print(f"=== RUNG {label} ({packet}) ===")
        rungs.append(run_rung(label, packet, args.n, args.cap, base))
        r = rungs[-1]
        print(f"  >>> {label}: 합의 {r['agreement_mean']} ± {r['agreement_stdev']} "
              f"(채점 {r['scorable_seeds']}/{args.n}, 평균 {r['mean_voters']}표)\n")

    # 인접 럽 간 통계
    steps = []
    for lo, hi in zip(rungs, rungs[1:]):
        a, b = lo["agreement_values"], hi["agreement_values"]
        steps.append({"from": lo["label"], "to": hi["label"], **welch(a, b)})

    summary = {"n": args.n, "cap": args.cap, "design": DESIGN, "specqa": SPECQA,
               "rungs": rungs, "steps": steps}
    (base / "sweep_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print("[SWEEP 결과] 합의 곡선 (계약 loose→tight)")
    for r in rungs:
        print(f"  {r['label']:14s}: {r['agreement_mean']} ± {r['agreement_stdev']} "
              f"  [{r['agreement_min']}, {r['agreement_max']}]  "
              f"(채점 {r['scorable_seeds']}/{args.n}, {r['mean_voters']}표)")
    print("  인접 럽 상승:")
    for s in steps:
        if "note" in s:
            print(f"    {s['from']} → {s['to']}: {s['note']}")
        else:
            sep = "분포분리" if not s["distributions_overlap"] else "겹침"
            print(f"    {s['from']} → {s['to']}: Δ{s['delta_mean']:+}, "
                  f"t={s['t']}, p={s['p']}, d={s['cohen_d']} ({sep})")
    print(f"[SWEEP] → {base / 'sweep_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
