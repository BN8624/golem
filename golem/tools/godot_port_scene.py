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
PITFALLS = GODOT_DIR / "GDSCRIPT_PITFALLS.md"  # 모든 생성에 자동 주입하는 공통 GDScript 함정(omc skills auto-inject 차용)
RULES = GODOT_DIR / "scripts" / "rules.gd"
OUT = GODOT_DIR / "scripts" / "board.gd"
DEFAULT_GODOT = r"C:\Users\USER\godot-engine\Godot_v4.7-stable_win64_console.exe"

ERR_MARKERS = ("SCRIPT ERROR", "Parse Error", "Failed to instantiate", "Failed to load",
               "Nonexistent", "Invalid call", "Cannot call", "Invalid access",
               "Invalid get index", "Invalid set index", "Compile Error")

PROMPT = """You are writing a PLAYABLE Godot 4 scene script that drives a VERIFIED rules module (DO NOT modify or reimplement it).
Output ONLY the full content of `scripts/board.gd` — no prose, no markdown fences.
The first line MUST be a one-line Korean comment, then `extends Node2D`.

=== GDScript 공통 함정 (반드시 지켜라 — 어기면 스모크/렌더가 실패한다) ===
{pitfalls}

=== 이 씬의 사양 ===
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
    # 입력 프로브(미션0 통합) — 선택·이동·공격을 구조화 비교. 문자열이 아니라 종료코드로 PASS 판정(불일치 시 quit(1)).
    r = subprocess.run([godot, "--headless", "--path", str(GODOT_DIR),
                        "--script", "res://test/run_input_probe.gd"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0
    lines = "\n".join(l for l in out.splitlines()
                      if "PROBE" in l or any(m in l for m in ERR_MARKERS))
    return ok, lines


def run_fixture(godot):
    # fixture 프로브 — 미션0과 무관한 기능 단위 계약(select/move/attack/victory/defeat/edge). 종료코드로 판정.
    r = subprocess.run([godot, "--headless", "--path", str(GODOT_DIR),
                        "--script", "res://test/run_fixture_probe.gd"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0
    lines = "\n".join(l for l in out.splitlines()
                      if "FIXTURE" in l or any(m in l for m in ERR_MARKERS))
    return ok, lines


def run_auto(godot):
    # 자동 전투 프로브 — auto_step() 반복 호출이 결정적으로 종료(VICTORY/DEFEAT)하는지(v7)
    r = subprocess.run([godot, "--headless", "--path", str(GODOT_DIR),
                        "--script", "res://test/run_auto_probe.gd"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    ok = "자동 전투 동작함" in out
    lines = "\n".join(l for l in out.splitlines()
                      if "PROBE AUTO" in l or any(m in l for m in ERR_MARKERS))
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


def diagnose(text):
    """[omc UltraQA 차용 #3] 게이트 에러를 함정 시그니처로 분류해 위반한 규칙을 콕 집어 되먹인다.
    raw 에러만 던지면 골렘이 같은 실수를 반복하므로, 어떤 함정을 어겼는지 한 줄로 지목한다."""
    t = text or ""
    hints = []
    def hit(sig):
        return sig in t
    if hit("Expected end of statement after variable declaration") or ('found ","' in t and "variable" in t):
        hints.append("→ 함정#1 위반: `var a, b = ...` 다중선언 금지. 변수마다 `var` 한 줄씩.")
    if "PackedVector2Array" in t and "operator '+'" in t:
        hints.append("→ 함정#2 위반: PackedVector2Array에 Array를 `+`로 붙이지 마라. 닫힌 점배열을 직접 만들어라.")
    if hit("draw_set_transform"):
        hints.append("→ 함정#4 위반: draw_set_transform(pos:Vector2, rot, scale:Vector2). 색·인자수 틀림. 타원은 draw_colored_polygon 점계산으로.")
    if hit("draw_string"):
        hints.append("→ 함정#3 위반: draw_string(font, pos, text, align, width, size, color) 순서.")
    if "allies" in t and ("Invalid access" in t or "on a base object of type 'Dictionary'" in t):
        hints.append("→ 함정#7 위반: MENU에서 state는 {}. state.allies/enemies는 `screen=='PLAYING'` 가드 안에서만.")
    if hit("same name as a previously declared function"):
        hints.append("→ 함수 중복 선언. 같은 이름 함수는 하나만.")
    if hit("not declared in the current scope"):
        hints.append("→ 변수 스코프: 블록(if/for) 안에서 선언한 변수를 밖에서 쓰지 마라. 필요한 바깥 스코프에 var 선언.")
    return ("아래 함정을 어겼다 — GDScript 함정 규칙을 다시 보라:\n" + "\n".join(hints) + "\n\n") if hints else ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=3)
    ap.add_argument("--godot", default=os.environ.get("GODOT", DEFAULT_GODOT))
    ap.add_argument("--replay", default=None, help="board.gd 파일로 골렘 호출 없이 스모크만(키0)")
    args = ap.parse_args(argv)

    from config import force_utf8_stdout
    force_utf8_stdout()
    spec = SPEC.read_text(encoding="utf-8")
    pitfalls = PITFALLS.read_text(encoding="utf-8") if PITFALLS.exists() else "(없음)"
    rules = RULES.read_text(encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if args.replay:
        OUT.write_text(Path(args.replay).read_text(encoding="utf-8"), encoding="utf-8")
        ok, out, _ = run_smoke(args.godot)
        pok, plines = run_probe(args.godot) if ok else (False, "(스모크 실패로 프로브 생략)")
        fok, flines = run_fixture(args.godot) if (ok and pok) else (False, "(이전 단계 실패로 fixture 생략)")
        print(out.strip()[-1200:])
        print(plines)
        print(flines)
        print("스모크:", "OK" if ok else "FAIL", "| 입력프로브:", "OK" if pok else "FAIL",
              "| fixture:", "OK" if fok else "FAIL")
        return 0 if (ok and pok and fok) else 1

    from config import get_api_keys
    from llm import KeyPool, LLMClient
    os.environ["GENERATOR_MODEL"] = MODEL_31
    os.environ["CRITIC_MODEL"] = MODEL_31
    pool = KeyPool(get_api_keys(), models=[MODEL_31])

    feedback = ""
    for attempt in range(1, args.cap + 1):
        print(f"[SCENE] 시도 {attempt}/{args.cap} — 골렘 board.gd 생성 (★키)")
        prompt = PROMPT.format(spec=spec, pitfalls=pitfalls, rules=rules,
                               feedback=("\n=== PREVIOUS ATTEMPT had errors — fix and re-output FULL file ===\n"
                                         + feedback + "\n") if feedback else "")
        with pool.checkout() as key:
            raw = LLMClient(api_key=key).generate("generator", prompt)
        OUT.write_text(_strip_fences(raw) + "\n", encoding="utf-8")
        ok, out, errs = run_smoke(args.godot)
        if not ok:
            print("  ✗ 스모크 에러:\n" + "\n".join("    " + l for l in errs.splitlines()[:8]))
            feedback = diagnose(errs) + errs[:1800]
            continue
        pok, plines = run_probe(args.godot)
        if not pok:
            print("  ✗ 입력 프로브 실패(선택/이동/공격 계약 불일치):\n" + "\n".join("    " + l for l in plines.splitlines()[:10]))
            feedback = ("스모크는 통과했으나 입력 프로브 실패. load_mission(0) 후 선택·이동·공격 중 계약이 어긋났다. "
                        "PROBE_JSON 의 expected vs actual 을 보고 차이를 고쳐라. "
                        "자동 검증 계약(state/selected_unit_id/load_mission/_unhandled_input)과 "
                        "좌표 비교 함정(pos[0]==gx and pos[1]==gy)을 다시 확인하라. 프로브 출력:\n" + plines[:1500])
            continue
        fok, flines = run_fixture(args.godot)
        if not fok:
            print("  ✗ fixture 프로브 실패(기능 단위 계약 불일치):\n" + "\n".join("    " + l for l in flines.splitlines()[:12]))
            feedback = ("스모크·입력프로브는 통과했으나 fixture 계약 실패. test/fixtures/*.json 의 기능 하나가 어긋났다. "
                        "FIXTURE_JSON 의 mismatches(got/want)를 보고 board.gd 의 입력 처리를 고쳐라. fixture 출력:\n" + flines[:1500])
            continue
        aok, alines = run_auto(args.godot)
        if not aok:
            print("  ✗ 자동전투 프로브 실패:\n" + "\n".join("    " + l for l in alines.splitlines()[:10]))
            feedback = ("스모크·입력프로브는 통과했으나 자동 전투(auto_step) 실패. "
                        "SCENE_SPEC ★v7(auto_step·그리디 정책·결정성)을 확인하라. "
                        "auto_step()이 PLAYING에서 아군 액션 1개를 update_state로 적용하고, 끝나면 screen=RESULT가 돼야 한다. 자동 프로브 출력:\n"
                        + alines[:1500])
            continue
        rok, rinfo = run_render(args.godot)
        if rok:
            print(f"★ 스모크+입력프로브+자동전투+렌더캡처 통과 → {OUT}")
            print("  최종 미관/터치는 사용자가 캡처·F5로 확인.")
            return 0
        print("  ✗ 렌더 캡처 실패(_draw 에러):\n" + "\n".join("    " + l for l in rinfo.splitlines()[:10]))
        feedback = (diagnose(rinfo)
                    + "스모크·입력프로브는 통과했으나 _draw 렌더에서 실패. draw_string 시그니처 함정"
                    "(draw_string(font,pos,text,align,width,size,color))과 폰트/텍스처 load 경로를 확인하라. 렌더 에러:\n"
                    + rinfo[:1500])
    print(f"\n{args.cap}회 내 미통과 — --cap 늘리거나 SCENE_SPEC 보강.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
