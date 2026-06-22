# forge 소설 백업(구조화 서사)을 게임 캠페인 아웃라인으로 압축 — 전제·인물·이벤트(미션)·element(카드 씨앗) 추출(키0)
"""forge runs/world-backups/<ts>/ 의 story/series.json + story/events/*.json 을 읽어
golem이 쓸 단일 아웃라인(eterno_outline.json)으로 정리한다. 엔진/메커니즘은 안 만들고, 서사·테마·미션
목표·메커니즘 씨앗만 뽑는다(소설=스킨/방향, 골렘=검증된 룰). 산출을 levelstory --setting,
propose_levels 미션 테마, propose_cards --ref 씨앗으로 연결한다.

사용: python forge_ingest.py --src "C:/Users/USER/forge/runs/world-backups/<ts>"   (키0)
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

import argparse
import json
import re
from pathlib import Path

DEFAULT_SRC = "C:/Users/USER/forge/runs/world-backups/20260621T020758.714624Z"


def ingest(src: Path):
    series = json.loads((src / "story" / "series.json").read_text(encoding="utf-8"))
    events = []
    for p in sorted((src / "story" / "events").glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        events.append({
            "id": e["id"], "volume": e.get("volume_id"), "seq": e.get("sequence"),
            "objective": e.get("objective", ""),
            "danger": (e.get("start_state") or {}).get("danger", ""),
            "end": (e.get("end_state") or {}).get("status") or (e.get("end_state") or {}),
        })
    # element = 카드/메커니즘 씨앗. setup·payoff 위주(change=서사 아크).
    seeds = [{"id": el["id"], "kind": el.get("kind"), "idea": el.get("description", ""),
              "resolves": el.get("resolves")}
             for el in series.get("elements", []) if el.get("kind") in ("setup", "payoff")]
    # 인물 휴리스틱: 전제에서 작은따옴표로 묶인 이름.
    chars = list(dict.fromkeys(re.findall(r"'([^']{1,12})'", series.get("premise", ""))))
    return {
        "title": series.get("title", ""),
        "premise": series.get("premise", ""),
        "theme": series.get("theme", ""),
        "ending": series.get("ending", ""),
        "setting_line": series.get("premise", ""),   # --setting용(세계관 한 묶음)
        "characters": chars,
        "events": events,                              # 20 미션
        "card_seeds": seeds,                           # 메커니즘 씨앗
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC, help="forge world-backup 디렉토리")
    ap.add_argument("--out", default=None, help="아웃라인 출력 경로(기본 build_runs/proposals/eterno_outline.json)")
    args = ap.parse_args(argv)

    src = Path(args.src)
    if not (src / "story" / "series.json").exists():
        ap.error(f"series.json 없음: {src}/story/series.json — --src 경로 확인")
    outline = ingest(src)
    out = Path(args.out) if args.out else (BUILD_RUNS / "proposals" / "eterno_outline.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  '{outline['title']}' — 이벤트 {len(outline['events'])}개·씨앗 {len(outline['card_seeds'])}개·인물 {outline['characters']}")
    print(f"  → {out}")
    print(f"  setting_line: {outline['setting_line'][:90]}…")
    print("  연결: levelstory --setting(전제) / propose_levels(이벤트 미션 테마) / propose_cards --ref(씨앗)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
