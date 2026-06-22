# Godot 씬 드라이버 — 골렘이 검증된 rules.gd를 호출하는 플레이 씬(board.gd)을 생성 → 헤드리스 스모크 → 에러 되먹임 재시도
"""분업: 씬(외형·입력)은 골렘(★키). 클로드는 이 하네스(배관)만 — SCENE_SPEC+rules.gd를 주고 board.gd를 받아
godot/scripts/board.gd에 쓴 뒤 `godot --headless --quit-after 30`으로 SCRIPT ERROR/Parse Error 없이 뜨는지 스모크.
실패 에러를 다음 프롬프트에 되먹여 cap회 자가수정. 플레이 가능·UI 정확성은 사용자가 F5로(0-diff 밖).

사용: python golem/tools/godot_port_scene.py [--cap 3] [--godot <exe>] [--replay <gd>]   (★키, 사용자 go 뒤)
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
import os
import subprocess
from pathlib import Path

MODEL_31 = "gemma-4-31b-it"
GODOT_DIR = REPO_ROOT / "godot"
SPEC = GODOT_DIR / "SCENE_SPEC.md"
RULES = GODOT_DIR / "scripts" / "rules.gd"
OUT = GODOT_DIR / "scripts" / "board.gd"
DEFAULT_GODOT = r"C:\Users\USER\godot-engine\Godot_v4.7-stable_win64_console.exe"

ERR_MARKERS = ("SCRIPT ERROR", "Parse Error", "Failed to instantiate", "Failed to load",
               "Nonexistent", "Invalid call", "Cannot call", "Invalid access",
               "Invalid get index", "Invalid set index", "Compile Error")

PROMPT = """You are writing a PLAYABLE Godot 4 scene script that drives a VERIFIED rules module (DO NOT modify or reimplement it).
Output ONLY the full content of `scripts/board.gd` — no prose, no markdown fences.
The first line MUST be a one-line Korean comment, then `extends Node2D`.

{spec}

=== rules.gd (already exists at res://scripts/rules.gd — CALL it, do NOT reimplement) ===
{rules}
{feedback}
Now output the COMPLETE board.gd content (and nothing else)."""


def _strip_fences(t):
    t = t.strip()
    if "```" in t:
        parts = t.split("```")
        blocks = parts[1::2] if len(parts) >= 3 else parts
        code = max(blocks, key=len)
        lines = code.splitlines()
        if lines and lines[0].strip().lower() in ("gdscript", "gd", "python"):
            lines = lines[1:]
        return "\n".join(lines).strip()
    return t


def run_smoke(godot):
    r = subprocess.run([godot, "--headless", "--path", str(GODOT_DIR), "--quit-after", "30"],
                       capture_output=True, text=True, encoding="utf-8", timeout=180)
    out = (r.stdout or "") + (r.stderr or "")
    errs = "\n".join(l for l in out.splitlines() if any(m in l for m in ERR_MARKERS))
    return errs == "", out, errs


def run_probe(godot):
    # 입력 프로브 — load_mission(0)으로 메뉴 우회 후 선택·이동·공격을 결정적 검증(스모크가 못 잡는 무반응 잡기)
    r = subprocess.run([godot, "--headless", "--path", str(GODOT_DIR),
                        "--script", "res://test/run_input_probe.gd"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    ok = ("입력 로직 동작함" in out) and ("공격 동작함" in out)
    lines = "\n".join(l for l in out.splitlines()
                      if "PROBE" in l or any(m in l for m in ERR_MARKERS))
    return ok, lines


def run_render(godot):
    # 렌더 캡처(windowed) — _draw 를 실제로 그려 헤드리스가 못 잡는 draw_string 시그니처/폰트/텍스처 에러를 잡는다.
    win = godot.replace("_console.exe", ".exe")  # 콘솔판→윈도판(실제 렌더 컨텍스트 필요)
    caps = [GODOT_DIR / "test" / "cap_menu.png", GODOT_DIR / "test" / "cap_after.png"]
    for p in caps:
        if p.exists():
            p.unlink()
    r = subprocess.run([win, "--path", str(GODOT_DIR), "--script", "res://test/capture_attack.gd"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    errs = "\n".join(l for l in out.splitlines() if any(m in l for m in ERR_MARKERS))
    made = all(p.exists() for p in caps)
    ok = errs == "" and made
    info = errs if errs else ("" if made else "캡처 PNG 미생성(_draw 가 안 그려짐)")
    return ok, info


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=3)
    ap.add_argument("--godot", default=os.environ.get("GODOT", DEFAULT_GODOT))
    ap.add_argument("--replay", default=None, help="board.gd 파일로 골렘 호출 없이 스모크만(키0)")
    args = ap.parse_args(argv)

    from config import force_utf8_stdout
    force_utf8_stdout()
    spec = SPEC.read_text(encoding="utf-8")
    rules = RULES.read_text(encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if args.replay:
        OUT.write_text(Path(args.replay).read_text(encoding="utf-8"), encoding="utf-8")
        ok, out, _ = run_smoke(args.godot)
        pok, plines = run_probe(args.godot) if ok else (False, "(스모크 실패로 프로브 생략)")
        print(out.strip()[-1200:])
        print(plines)
        print("스모크:", "OK" if ok else "FAIL", "| 프로브:", "OK" if pok else "FAIL")
        return 0 if (ok and pok) else 1

    from config import get_api_keys
    from llm import KeyPool, LLMClient
    os.environ["GENERATOR_MODEL"] = MODEL_31
    os.environ["CRITIC_MODEL"] = MODEL_31
    pool = KeyPool(get_api_keys(), models=[MODEL_31])

    feedback = ""
    for attempt in range(1, args.cap + 1):
        print(f"[SCENE] 시도 {attempt}/{args.cap} — 골렘 board.gd 생성 (★키)")
        prompt = PROMPT.format(spec=spec, rules=rules,
                               feedback=("\n=== PREVIOUS ATTEMPT had errors — fix and re-output FULL file ===\n"
                                         + feedback + "\n") if feedback else "")
        with pool.checkout() as key:
            raw = LLMClient(api_key=key).generate("generator", prompt)
        OUT.write_text(_strip_fences(raw) + "\n", encoding="utf-8")
        ok, out, errs = run_smoke(args.godot)
        if not ok:
            print("  ✗ 스모크 에러:\n" + "\n".join("    " + l for l in errs.splitlines()[:8]))
            feedback = errs[:1800]
            continue
        pok, plines = run_probe(args.godot)
        if not pok:
            print("  ✗ 입력 프로브 실패(클릭/공격 무반응):\n" + "\n".join("    " + l for l in plines.splitlines()[:10]))
            feedback = ("스모크는 통과했으나 입력 프로브 실패. load_mission(0) 후 클릭이 무반응이다. "
                        "자동 검증 계약(state/selected_unit_id/load_mission/_unhandled_input)과 "
                        "좌표 비교 함정(pos[0]==gx and pos[1]==gy)을 다시 확인하라. 프로브 출력:\n" + plines[:1500])
            continue
        rok, rinfo = run_render(args.godot)
        if rok:
            print(f"★ 스모크+입력프로브+렌더캡처 통과 → {OUT}")
            print("  최종 미관/터치는 사용자가 캡처·F5로 확인.")
            return 0
        print("  ✗ 렌더 캡처 실패(_draw 에러):\n" + "\n".join("    " + l for l in rinfo.splitlines()[:10]))
        feedback = ("스모크·입력프로브는 통과했으나 _draw 렌더에서 실패. draw_string 시그니처 함정"
                    "(draw_string(font,pos,text,align,width,size,color))과 폰트/텍스처 load 경로를 확인하라. 렌더 에러:\n"
                    + rinfo[:1500])
    print(f"\n{args.cap}회 내 미통과 — --cap 늘리거나 SCENE_SPEC 보강.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
