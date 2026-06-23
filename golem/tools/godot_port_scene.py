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
{base}{feedback}
Now output the COMPLETE board.gd content (and nothing else)."""

# 증분 모드: 검증된 현재 board를 base로 주고 "새 기능만 최소 변경"을 지시 → 풀 scratch 재생성이 이미 통과한 로직(선택/이동/RESULT)을 흔드는 회귀를 막는다(omc 증분분해).
BASE_BLOCK = """=== CURRENT VERIFIED board.gd (this ALREADY PASSES every gate — smoke/probe/fixture/auto/render) ===
{current}

=== YOUR TASK (INCREMENTAL — critical) ===
You MUST ADD the newly-specified feature in the 사양 (the latest ★v section) — the file MUST change to implement it (do NOT output the file unchanged; an identical file is a FAILURE). Make the change focused: touch only the code the new feature needs.
KEEP all UNRELATED logic byte-identical — especially `_unhandled_input` PLAYING selection/move/attack, `execute_action`, `load_mission`/`start_battle_with`/`_enter_battle`, the VICTORY/DEFEAT → screen="RESULT" transition, and every input hit-rect. Do NOT rewrite working logic and do NOT change behavior outside the new feature.
Output the COMPLETE modified file (base + your feature addition), nothing else.
"""


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
    # 윈도 렌더는 4연속 실행 시 GPU/윈도 컨텍스트 경합으로 드물게 false-negative가 난다(2026-06-23 실측: 동일 board가
    # 배치에선 실패, 단독 실행은 통과). 실패 시 1회 재시도해 플레이키를 흡수한다(진짜 결함이면 둘 다 실패).
    ok, info = _render_once(godot)
    if ok:
        return ok, info
    ok2, info2 = _render_once(godot)
    return ok2, info2


def _render_once(godot):
    # 렌더 캡처(windowed) — _draw 를 실제로 그려 헤드리스가 못 잡는 draw_string 시그니처/폰트/텍스처 에러를 잡는다.
    # + BRIEFING/SQUAD_SELECT가 서로 다른 화면인지 검사(회귀 차단 — 헤드리스 프로브가 못 잡는 갭).
    win = godot.replace("_console.exe", ".exe")  # 콘솔판→윈도판(실제 렌더 컨텍스트 필요)
    caps = [GODOT_DIR / "test" / "cap_menu.png", GODOT_DIR / "test" / "cap_briefing.png",
            GODOT_DIR / "test" / "cap_squad.png", GODOT_DIR / "test" / "cap_after.png"]
    for p in caps:
        if p.exists():
            p.unlink()
    r = subprocess.run([win, "--path", str(GODOT_DIR), "--script", "res://test/capture_attack.gd"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    errs = "\n".join(l for l in out.splitlines() if any(m in l for m in ERR_MARKERS))
    made = all(p.exists() for p in caps)
    if errs != "" or not made:
        return False, (errs if errs else "캡처 PNG 미생성(_draw 가 안 그려짐)")
    # BRIEFING_DIFF_RATIO 파싱 — 브리핑이 메뉴와 거의 동일하면(브리핑 박스·본문 안 그림) 회귀로 차단
    ratio = None
    for line in out.splitlines():
        if "BRIEFING_DIFF_RATIO=" in line:
            try:
                ratio = float(line.split("BRIEFING_DIFF_RATIO=")[1].split()[0])
            except (ValueError, IndexError):
                pass
    if ratio is not None and ratio < 0.03:
        return False, (f"BRIEFING이 MENU와 거의 동일(diff={ratio:.3f}<0.03) — BRIEFING 화면은 반투명 박스+"
                       "briefing 본문+'탭하여 시작'을 그려야 한다. 메뉴를 그대로 그리지 마라(SCENE_SPEC BRIEFING).")
    # SQUAD_SELECT 화면별 검사(v10) — 브리핑 클릭이 SQUAD_SELECT로 가고, 그 화면이 BRIEFING과 다르게 그려지는지 + start_battle_with 기능
    sratio = None
    sbattle = None
    for line in out.splitlines():
        if "SQUAD_DIFF_RATIO=" in line:
            try:
                sratio = float(line.split("SQUAD_DIFF_RATIO=")[1].split()[0])
            except (ValueError, IndexError):
                pass
        if "SQUAD_BATTLE_OK=" in line:
            sbattle = "SQUAD_BATTLE_OK=true" in line.lower().replace(" ", "")
    if sratio is not None and sratio < 0.03:
        return False, (f"SQUAD_SELECT가 BRIEFING과 거의 동일(diff={sratio:.3f}<0.03) — BRIEFING 클릭은 "
                       "SQUAD_SELECT(덱 편성)로 가야 하고, 그 화면은 로스터 유닛 목록+'출전' 버튼을 그려야 한다(SCENE_SPEC ★v10).")
    if sbattle is False:
        return False, ("start_battle_with([로스터 앞 2개 id]) 후 PLAYING·allies 2명·status PLAYING이 아니다. "
                       "start_battle_with는 고른 유닛을 id 1..N 정수로 재부여·0열 배치해 state.allies로 넣고 PLAYING으로 가야 한다(SCENE_SPEC ★v10).")
    return True, ""


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
    if hit("already") and "declared in this scope" in t:
        hints.append("→ 변수 중복 선언: 같은 스코프(같은 함수/블록)에서 같은 이름을 `var`로 두 번 선언 마라. 임시변수(tw/th 등)는 이름을 다르게.")
    if hit("not declared in the current scope"):
        hints.append("→ 변수 스코프: 블록(if/for) 안에서 선언한 변수를 밖에서 쓰지 마라. 필요한 바깥 스코프에 var 선언.")
    if "Invalid operands" in t and "Array" in t and "Vector2" in t:
        hints.append("→ pos 비교 함정: `pos`(Array) 와 Vector2 를 `!=`/`==` 로 직접 비교 마라. 원소별 `pos[0]==gx and pos[1]==gy` 로.")
    return ("아래 함정을 어겼다 — GDScript 함정 규칙을 다시 보라:\n" + "\n".join(hints) + "\n\n") if hints else ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=3)
    ap.add_argument("--godot", default=os.environ.get("GODOT", DEFAULT_GODOT))
    ap.add_argument("--replay", default=None, help="board.gd 파일로 골렘 호출 없이 스모크만(키0)")
    ap.add_argument("--incr", action="store_true",
                    help="증분 모드: 현재 검증된 board.gd를 base로 주고 새 기능만 최소 변경(풀 scratch 회귀 방지)")
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

    # 증분 모드: 루프 전에 현재 검증된 board를 base로 고정(각 시도의 실패 출력이 아니라 항상 같은 통과본을 base로 준다).
    base = ""
    base_board = None
    if args.incr:
        if not OUT.exists():
            print("--incr: 현재 board.gd 가 없다. 검증된 board를 먼저 두라(git restore 등).")
            return 1
        base_board = OUT.read_text(encoding="utf-8").strip()
        base = BASE_BLOCK.format(current=OUT.read_text(encoding="utf-8"))
        print("[SCENE] 증분 모드 — 검증된 board를 base로 최소 변경 지시")

    feedback = ""
    for attempt in range(1, args.cap + 1):
        print(f"[SCENE] 시도 {attempt}/{args.cap} — 골렘 board.gd 생성 (★키)")
        prompt = PROMPT.format(spec=spec, pitfalls=pitfalls, rules=rules, base=base,
                               feedback=("\n=== PREVIOUS ATTEMPT had errors — fix and re-output FULL file ===\n"
                                         + feedback + "\n") if feedback else "")
        with pool.checkout() as key:
            raw = LLMClient(api_key=key).generate("generator", prompt)
        gen = _strip_fences(raw)
        # 증분 echo 차단: 생성물이 base와 사실상 동일하면(새 기능 미구현) 게이트 돌리기 전에 거부·되먹임.
        if base_board is not None and gen.strip() == base_board:
            print("  ✗ 증분 미구현: base를 그대로 반환(새 기능 0줄). 되먹임 후 재시도.")
            feedback = ("너는 파일을 변경 없이 그대로 반환했다 — 이는 실패다. 사양(최신 ★v 섹션)의 새 기능을 "
                        "반드시 구현하라. 무관한 로직은 그대로 두되, 새 기능의 _draw/입력 코드는 반드시 추가해서 "
                        "파일이 base와 달라져야 한다.")
            continue
        OUT.write_text(gen + "\n", encoding="utf-8")
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
