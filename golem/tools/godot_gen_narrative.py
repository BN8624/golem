# 서사 생성 드라이버 — 골렘이 4미션에 브리핑/승리/패배 문구를 쓰고, 검증 후 godot/data/squad_levels.json에 병합(★키)
"""분업: 서사(설계)는 골렘. 클로드는 이 하네스(배관)만 — 미션 메타(name/desc/teaches/배치 요약)를 주고
미션별 story={briefing,victory,defeat} JSON을 받아, 4미션 전부 채워졌는지 검증한 뒤 godot 복사본에 병합한다.
story는 rules가 안 읽으므로 골든 동치(0-diff)는 그대로다. 병합 후 골든 러너로 재확인한다.

사용: python golem/tools/godot_gen_narrative.py [--dry] [--replay <json>]   (★키, 사용자 go 뒤)
  --dry    : 병합 안 하고 생성 결과만 출력
  --replay : 골렘 호출 없이 주어진 story JSON으로 병합만(키0)
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import REPO_ROOT  # noqa: E402

import argparse
import json
import os
from pathlib import Path

MODEL_31 = "gemma-4-31b-it"
LEVELS = REPO_ROOT / "godot" / "data" / "squad_levels.json"

PROMPT = """너는 전술 SRPG '에테르노 부대'의 시나리오 작가다.
아래 4개 미션 각각에 짧은 한국어 서사를 붙여라. 톤은 비장하고 간결한 중세 판타지 군사물.

각 미션에 대해:
- "briefing": 미션 진입 전 브리핑. 2~3문장. 상황과 목표를 분위기 있게. (각 문장은 마침표로 끝낸다. 콜론 금지.)
- "victory": 승리 직후 한 문장.
- "defeat": 패배 직후 한 문장.

규칙:
- 게임 용어(knockback/range 등 영어)나 수치는 쓰지 마라. 서사 문장만.
- 출력은 JSON 배열만. 마크다운/설명/코드펜스 금지.
- 배열 길이는 정확히 {n}이고, i번째 원소는 i번째 미션에 대응한다.
- 각 원소 형식: {{"briefing": "...", "victory": "...", "defeat": "..."}}

미션 목록:
{missions}

이제 JSON 배열만 출력하라."""


def _strip_to_json(t):
    t = t.strip()
    if "```" in t:
        parts = t.split("```")
        blocks = parts[1::2] if len(parts) >= 3 else parts
        t = max(blocks, key=len)
        lines = t.splitlines()
        if lines and lines[0].strip().lower() in ("json", "gdscript", "python"):
            lines = lines[1:]
        t = "\n".join(lines)
    a, b = t.find("["), t.rfind("]")
    if a >= 0 and b > a:
        t = t[a:b + 1]
    return t.strip()


def _mission_summaries(levels):
    out = []
    for i, m in enumerate(levels):
        s = m["initialState"]
        out.append(f'미션 {i}: 제목="{m.get("name")}" / 개요="{m.get("desc")}" '
                   f'/ 아군 {len(s["allies"])}명 vs 적 {len(s["enemies"])}명 / 격자 {s["gridSize"]}x{s["gridSize"]}')
    return "\n".join(out)


def _validate(stories, n):
    if not isinstance(stories, list) or len(stories) != n:
        return f"배열 길이 {len(stories) if isinstance(stories, list) else '?'} ≠ {n}"
    for i, st in enumerate(stories):
        for k in ("briefing", "victory", "defeat"):
            if not isinstance(st.get(k), str) or not st[k].strip():
                return f"미션 {i} '{k}' 비어있음/문자열 아님"
    return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--replay", default=None)
    args = ap.parse_args(argv)

    from config import force_utf8_stdout
    force_utf8_stdout()

    levels = json.loads(LEVELS.read_text(encoding="utf-8"))
    n = len(levels)

    if args.replay:
        stories = json.loads(Path(args.replay).read_text(encoding="utf-8"))
    else:
        from config import get_api_keys
        from llm import KeyPool, LLMClient
        os.environ["GENERATOR_MODEL"] = MODEL_31
        pool = KeyPool(get_api_keys(), models=[MODEL_31])
        prompt = PROMPT.format(n=n, missions=_mission_summaries(levels))
        print(f"[서사] 골렘({MODEL_31})에 4미션 서사 생성 요청 (★키)")
        with pool.checkout() as key:
            raw = LLMClient(api_key=key).generate("generator", prompt)
        stories = json.loads(_strip_to_json(raw))

    err = _validate(stories, n)
    if err:
        print("✗ 검증 실패:", err)
        return 1

    for i, m in enumerate(levels):
        m["story"] = {k: stories[i][k].strip() for k in ("briefing", "victory", "defeat")}
        print(f"  [{i}] {m.get('name')}")
        print(f"      briefing: {m['story']['briefing']}")

    if args.dry:
        print("\n--dry: 병합 안 함.")
        return 0

    LEVELS.write_text(json.dumps(levels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n★ 4미션 story 병합 완료 → {LEVELS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
