# Godot 룰 포팅 드라이버 — 골렘이 squad game_logic.js를 GDScript(rules.gd)로 포팅 → 골든 러너로 0-diff 검증 → 실패 되먹임 재시도
"""분업: 룰 GDScript는 골렘(★키)이 쓴다. 클로드는 이 하네스(배관)만 — 골렘 호출·파일 쓰기·골든 검증·피드백 루프.
PORTING_SPEC.md + game_logic.js를 골렘에 주고 rules.gd를 받아 godot/scripts/rules.gd에 쓴 뒤,
`godot --headless --path godot --script res://test/run_rules_golden.gd`로 rules_golden.json과 0-diff 대조.
불일치 FAIL 라인을 다음 프롬프트에 되먹여 cap회까지 자가수정. 36/36 통과 시 채택.

사용: python golem/tools/godot_port_rules.py [--cap 3] [--godot <exe>] [--replay <gd파일>]   (★키, 사용자 go 뒤)
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import REPO_ROOT, BASES  # noqa: E402

import argparse
import os
import subprocess
from pathlib import Path

MODEL_31 = "gemma-4-31b-it"
GODOT_DIR = REPO_ROOT / "godot"
SPEC = GODOT_DIR / "PORTING_SPEC.md"
SOURCE = BASES / "squad_base_l8" / "src" / "game_logic.js"
OUT = GODOT_DIR / "scripts" / "rules.gd"
RUNNER = "res://test/run_rules_golden.gd"
DEFAULT_GODOT = r"C:\Users\USER\godot-engine\Godot_v4.7-stable_win64_console.exe"

PROMPT = """You are porting a VERIFIED deterministic game-rules module from JavaScript to Godot 4 GDScript.
Output ONLY the full content of `scripts/rules.gd` — no prose, no markdown code fences.
The first line MUST be a one-line Korean comment describing the file's role, then `extends RefCounted`.

{spec}

=== SOURCE TO PORT (game_logic.js) — port this faithfully, same logic & tie-breaks ===
{source}
{feedback}
Now output the COMPLETE GDScript file content (and nothing else)."""


def _strip_fences(t):
    t = t.strip()
    if "```" in t:
        parts = t.split("```")
        # 가장 긴 펜스 블록을 코드로 취함(언어 태그 줄 제거)
        blocks = parts[1::2] if len(parts) >= 3 else parts
        code = max(blocks, key=len)
        lines = code.splitlines()
        if lines and lines[0].strip().lower() in ("gdscript", "gd", "python"):
            lines = lines[1:]
        return "\n".join(lines).strip()
    return t


def run_runner(godot):
    r = subprocess.run([godot, "--headless", "--path", str(GODOT_DIR), "--script", RUNNER],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    out = (r.stdout or "") + (r.stderr or "")
    passed = "0 실패" in out
    fails = "\n".join(l for l in out.splitlines() if l.startswith("FAIL") or "SCRIPT ERROR" in l or "Parse Error" in l)
    return passed, out, fails


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=3, help="포팅 재시도 횟수")
    ap.add_argument("--godot", default=os.environ.get("GODOT", DEFAULT_GODOT), help="Godot 실행파일(console)")
    ap.add_argument("--replay", default=None, help="GDScript 파일로 골렘 호출 없이 검증만(키0 디버그)")
    args = ap.parse_args(argv)

    from config import force_utf8_stdout
    force_utf8_stdout()

    spec = SPEC.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # replay: 골렘 호출 없이 주어진 .gd로 검증만(하네스 디버그·키0)
    if args.replay:
        OUT.write_text(Path(args.replay).read_text(encoding="utf-8"), encoding="utf-8")
        passed, out, _ = run_runner(args.godot)
        print(out.strip())
        return 0 if passed else 1

    from config import get_api_keys
    from llm import KeyPool, LLMClient
    os.environ["GENERATOR_MODEL"] = MODEL_31
    os.environ["CRITIC_MODEL"] = MODEL_31
    pool = KeyPool(get_api_keys(), models=[MODEL_31])

    feedback = ""
    for attempt in range(1, args.cap + 1):
        print(f"[PORT] 시도 {attempt}/{args.cap} — 골렘 GDScript 포팅 (★키)")
        prompt = PROMPT.format(spec=spec, source=source,
                               feedback=("\n=== PREVIOUS ATTEMPT FAILED — fix these and re-output the FULL file ===\n"
                                         + feedback + "\n") if feedback else "")
        with pool.checkout() as key:
            raw = LLMClient(api_key=key).generate("generator", prompt)
        OUT.write_text(_strip_fences(raw) + "\n", encoding="utf-8")
        passed, out, fails = run_runner(args.godot)
        print(out.strip()[-1500:])
        if passed:
            print(f"\n★ 포팅 채택 — 골든 0-diff 통과 → {OUT}")
            return 0
        feedback = fails[:1800] or "골든 불일치(상세 없음). 인터페이스·불변식 재확인."
        print(f"  ✗ 비통과 — 다음 시도에 FAIL 되먹임")
    print(f"\n{args.cap}회 내 미통과 — --cap 늘리거나 PORTING_SPEC 보강.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
