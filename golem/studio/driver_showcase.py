# 탐정 IF 쇼케이스 무인 드라이버 — 카드를 순서대로 패치빌드(31B)·검증·누적하고 리포트를 남긴다(밤샘 자동 실행용)
"""각 카드에 대해:
  1) build_graded --patch 로 31B가 base에 카드 패치를 적용(★키).
  2) consensus.json 으로 그린 판정(gate_passed>=1 · overall_agreement==1.0 · golden_diffs==[]).
  3) 그린이면 통과한 attempt 워크스페이스(모델 실출력)를 다음 카드의 base로 누적. 실패면 1회 재시도 후 중단.
  4) showcase/REPORT.md · REPORT.json 에 카드별 결과 + 최종 게임 위치 + 샘플 플레이스루를 남긴다.
무인 안전: 첫 카드부터 막히면 마지막 그린 base 보존하고 멈춘다(키 낭비 방지). 시간 상한 가드 포함.
"""

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # studio
ROOT = HERE.parent.parent                        # config·.env 있는 루트
MAX_SECONDS = int(3.7 * 3600)                    # 시간 상한(여유 두고 ~3.7h)

# 게임 레지스트리 — (base 디렉토리, 카드 목록). 카드=(레벨, 패킷, specqa, 빌드 inject-modules).
# inject는 그 카드가 실제 touched하는 모듈만. 새 게임은 여기 한 줄 추가하면 무인 빌드 가능.
GAMES = {
    "detective": {
        "base": "detective_base",
        "cards": [
            ("l1", "planning_packet_detective_l1", "specqa_packet_detective_l1", "src/scenes.js,src/beats.js"),
            ("l2", "planning_packet_detective_l2", "specqa_packet_detective_l2", "src/scenes.js,src/beats.js"),
            ("l3", "planning_packet_detective_l3", "specqa_packet_detective_l3", "src/beats.js"),
        ],
    },
    "sokoban": {
        "base": "sokoban_base",
        "cards": [
            ("l1", "planning_packet_sokoban_l1", "specqa_packet_sokoban_l1", "src/move_logic.js"),
            ("l2", "planning_packet_sokoban_l2", "specqa_packet_sokoban_l2", "src/move_logic.js"),
            ("l3", "planning_packet_sokoban_l3", "specqa_packet_sokoban_l3", "src/move_logic.js"),
        ],
    },
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_out(stdout):
    d = {}
    for line in stdout.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        d[k.strip()] = v.strip()
    return d


def canon(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except (ValueError, TypeError):
            return v
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def run_node(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 else None


def find_winner(out_dir, scenarios, output_keys):
    """게이트 통과+골든일치하는 attempt 워크스페이스(모델 실출력)를 찾아 경로 반환."""
    for ws in sorted(out_dir.glob("attempt*/workspace")):
        if not (ws / "main.js").exists() or not (ws / "scenarios.json").exists():
            continue
        ok = True
        for i, s in enumerate(scenarios, 1):
            so = run_node(ws, i)
            if so is None:
                ok = False
                break
            got = parse_out(so)
            for k in output_keys:
                if k in s["expected"] and canon(got.get(k)) != canon(s["expected"][k]):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return ws
    return None


def build_card(showcase, level, packet, specqa, inject, base_dir, attempt_tag):
    out_dir = showcase / f"{level}{attempt_tag}"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    cmd = [sys.executable, str(HERE / "build_graded.py"),
           "--packet", str(HERE / packet),
           "--specqa", str(HERE / specqa),
           "--base", str(base_dir),
           "--inject-modules", inject,
           "--patch", "--cap", "11",
           "--out", str(out_dir)]
    env = {"PYTHONUTF8": "1"}
    import os
    env = {**os.environ, **env}
    log(f"  build {level}{attempt_tag}: base={base_dir.name} inject={inject}")
    subprocess.run(cmd, cwd=str(ROOT), env=env, timeout=MAX_SECONDS)
    cons_path = out_dir / "consensus.json"
    if not cons_path.exists():
        return out_dir, None
    return out_dir, json.loads(cons_path.read_text(encoding="utf-8"))


def main():
    sys.path.insert(0, str(ROOT))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    game = sys.argv[1] if len(sys.argv) > 1 else "detective"
    if game not in GAMES:
        log(f"알 수 없는 게임: {game} (가능: {list(GAMES)})")
        return 2
    cards = GAMES[game]["cards"]
    showcase = HERE / "build_runs" / f"showcase_{game}"
    showcase.mkdir(parents=True, exist_ok=True)
    log(f"게임={game} 카드 {len(cards)}장 → {showcase}")

    started = time.time()
    base_dir = HERE / GAMES[game]["base"]
    manifest_src = base_dir / "module_manifest.json"
    results = []
    stopped_reason = None
    last_green_specqa = None

    for level, packet, specqa, inject in cards:
        if time.time() - started > MAX_SECONDS:
            stopped_reason = "시간 상한 도달"
            break
        scenarios = json.loads((HERE / specqa / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
        output_keys = [k for k, v in
                       json.loads((HERE / packet / "contract.json").read_text(encoding="utf-8"))
                       ["data_contract"]["state_shape"].items() if not isinstance(v, dict)]

        green = False
        cons = None
        out_dir = None
        for tag in ("", "_retry"):
            out_dir, cons = build_card(showcase, level, packet, specqa, inject, base_dir, tag)
            if cons is None:
                log(f"  {level}{tag}: consensus.json 없음(빌드 크래시?)")
                continue
            gp = cons.get("gate_passed", 0)
            agree = cons.get("overall_agreement")
            gdiffs = cons.get("golden_diffs", [])
            log(f"  {level}{tag}: gate_passed={gp} agreement={agree} golden_diffs={len(gdiffs)}")
            if gp >= 1 and agree == 1.0 and not gdiffs:
                green = True
                break

        rec = {"level": level, "green": green,
               "gate_passed": (cons or {}).get("gate_passed", 0),
               "agreement": (cons or {}).get("overall_agreement"),
               "golden_diffs": len((cons or {}).get("golden_diffs", [])),
               "scenarios": len(scenarios)}

        if not green:
            stopped_reason = f"{level} 그린 실패(재시도 후에도) — 마지막 그린 base 보존하고 중단"
            results.append(rec)
            break

        winner = find_winner(out_dir, scenarios, output_keys)
        if winner is None:
            stopped_reason = f"{level} 그린이나 통과 워크스페이스 탐색 실패 — 중단"
            rec["green"] = False
            results.append(rec)
            break

        built = showcase / f"{level}_built"
        if built.exists():
            shutil.rmtree(built)
        shutil.copytree(winner, built)
        shutil.copy2(manifest_src, built / "module_manifest.json")
        rec["built_base"] = str(built)
        results.append(rec)
        base_dir = built
        last_green_specqa = specqa
        log(f"  {level} GREEN — 누적 base 갱신 → {built.name}")

    # 최종 게임 샘플 플레이스루(마지막 그린 base) — 대표 시나리오 몇 개의 node 출력.
    final_playthrough = []
    last_built = base_dir if (base_dir.name.endswith("_built") and last_green_specqa) else None
    if last_built:
        demo = json.loads((HERE / last_green_specqa
                           / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
        (last_built / "scenarios.json").write_text(
            json.dumps([{"input": s["input"]} for s in demo], ensure_ascii=False), encoding="utf-8")
        for i, s in enumerate(demo, 1):
            so = run_node(last_built, i)
            if so:
                final_playthrough.append({"id": s["id"], "output": so})

    elapsed = round(time.time() - started, 1)
    green_n = sum(1 for r in results if r["green"])
    report = {"game": game,
              "started": datetime.fromtimestamp(started).isoformat(timespec="seconds"),
              "elapsed_seconds": elapsed, "cards_total": len(cards), "cards_green": green_n,
              "stopped_reason": stopped_reason, "results": results,
              "final_base": str(base_dir), "final_playthrough_count": len(final_playthrough)}
    (showcase / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# {game} 쇼케이스 — 무인 빌드 리포트",
        "",
        f"- 시작: {report['started']}  /  소요: {elapsed}s",
        f"- 카드: {green_n}/{len(cards)} 그린",
        f"- 중단 사유: {stopped_reason or '없음(전 카드 완주)'}",
        f"- 최종 게임 base: `{base_dir}`",
        "",
        "## 카드별 결과",
        "",
        "| 카드 | 그린 | 게이트통과 | 합의 | 골든diff | 시나리오 |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['level']} | {'✅' if r['green'] else '❌'} | {r['gate_passed']}/11 | "
                     f"{r['agreement']} | {r['golden_diffs']} | {r['scenarios']} |")
    lines += ["", "## 최종 게임 샘플 플레이스루", ""]
    for p in final_playthrough:
        lines += [f"### {p['id']}", "```", p["output"].rstrip(), "```", ""]
    (showcase / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    log(f"완료: {green_n}/{len(cards)} 그린, {elapsed}s, 리포트 → {showcase / 'REPORT.md'}")
    return 0 if green_n == len(cards) else 1


if __name__ == "__main__":
    raise SystemExit(main())
