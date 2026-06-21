# build_graded 하네스 메커닉(레버4 selective·patch·gate 전시나리오)을 tactics 픽스처로 키0 검증한다
"""rocket 픽스처를 걷어내고 본선 tactics(커널 base + l1 카드 참조)로 같은 하네스 회귀를 잠근다.

검증 대상은 게임 콘텐츠가 아니라 build_graded의 배선이다.
  1) selective: 건드리는 모듈만 본문 주입·나머지 동결 시그니처(_iface_stub) + verbatim 병합 + 골든 재현.
  2) patch: FIND/REPLACE 파싱·적용·에러 단위 + 패치 프롬프트 shape + base→참조 라운드트립 골든 재현.
  3) gate 전 시나리오: 첫 시나리오뿐 아니라 임의 시나리오의 비정상 종료를 게이트가 잡는지(외부리뷰 #2).
모델출력 자리에는 검증된 참조(gen_tactics_l1_golden.REF_GAME_LOGIC)를 쓴다 — API 콜 0.
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

import shutil
import sys
from importlib import import_module
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))
try:
    from config import force_utf8_stdout
    force_utf8_stdout()
except Exception:  # noqa: BLE001
    pass

import build_graded as bg
import patch_apply
from parse_write import parse_files, write_candidate

BASE = BASES / "tactics_kernel_base"
PKT = PACKETS / "planning_packet_tactics_l1"
SPQ = PACKETS / "specqa_packet_tactics_l1"
REF = import_module("gen_tactics_l1_golden").REF_GAME_LOGIC  # 모델출력 자리(검증된 l1 참조 로직)

contract, concept, manifest, sysd, scenarios, risk = bg.load_all(PKT, BASE, SPQ)
manifest_v = {"schema_version": "0.1", "module_format": "commonjs", **manifest}
grading_keys = {"id", "expected", "oracle_risk", "covers_reqs"}
scen_inputs = [{k: v for k, v in s.items() if k not in grading_keys} for s in scenarios]
scenario_data = contract["data_contract"]["scenario_data"]
injected_scenarios = bg._gen_scenarios_module(scenario_data)  # 계약 고정 세계(src/scenarios.js)
OUTPUT_KEYS = ["status", "turn", "hero_hp", "hero_pos", "enemies"]
TOUCHED = ["src/game_logic.js"]              # tactics는 game_logic만 건드린다(engine/main 동결)

checks = []


def expect(name, cond):
    checks.append((name, bool(cond)))


def expect_error(name, fn):
    try:
        fn()
        checks.append((name, False))
    except patch_apply.PatchError:
        checks.append((name, True))


# --- selective 번들 구성(build_graded main()의 레버4 경로 재현) ---
exports_by_path = {f["path"]: f.get("exports", []) for f in manifest.get("files", [])}
touched_chunks, frozen_chunks, held_out, touched_src = [], [], [], {}
for p in sorted(BASE.glob("**/*.js")):
    rel = p.relative_to(BASE).as_posix()
    src = p.read_text(encoding="utf-8")
    if rel in TOUCHED:
        touched_chunks.append(f"=== FILE: {rel} ===\n{src}")
        touched_src[rel] = src
    else:
        frozen_chunks.append(bg._iface_stub(rel, src, exports_by_path.get(rel, [])))
        held_out.append((rel, src))
selective = {"touched_paths": TOUCHED, "touched_code": "\n\n".join(touched_chunks),
             "frozen_iface": "\n\n".join(frozen_chunks), "touched_src": touched_src}
frozen_modules = {"src/scenarios.js": injected_scenarios}


def gate_golden(tag, files):
    """병합 파일에 held_out verbatim + 계약 세계 주입 후 게이트·골든 재현을 검증한다."""
    for rel, src in held_out:
        files.setdefault(rel, src)
    files["src/scenarios.js"] = injected_scenarios          # held_out 복사 뒤 계약 세계로 덮어씀
    ws = BUILD_RUNS / f"_harness_{tag}" / "workspace"
    if ws.parent.exists():
        shutil.rmtree(ws.parent)
    ws.mkdir(parents=True)
    write_candidate(ws, files)
    ok, reason, outputs = bg.gate_and_run(ws, manifest_v, scenarios)
    expect(f"{tag}: 게이트 통과", ok)
    if not ok:
        print(f"  {tag} 게이트 실패: {reason}")
        return
    bad = [f"{s['id']}.{k}" for s in scenarios for k in OUTPUT_KEYS
           if k in (s.get("expected") or {})
           and bg._canon(dict(outputs.get(s["id"], ())).get(k)) != bg._canon(s["expected"][k])]
    expect(f"{tag}: 골든 재현 {len(scenarios)}세계", not bad)
    if bad:
        print(f"  {tag} 골든 불일치: {bad[:4]}")


# --- 1) selective 프롬프트 shape ---
ps = bg.build_prompt(concept, contract, manifest, sysd, scen_inputs,
                     selective=selective, frozen_modules=frozen_modules)
expect("selective: touched(game_logic) 본문 주입", "nextState.turn += 1;" in ps)
expect("selective: frozen(engine) 본문 비공개", "const initialEnemyCount = state.enemies.length;" not in ps)
expect("selective: frozen 시그니처 공개", "exports.runScenario = (initialState, actionSequence) =>" in ps)
expect("selective: touched만 출력 지시", "src/game_logic.js" in ps and "Do NOT output the frozen" in ps)

# --- 2) patch 프롬프트 shape ---
pp = bg.build_prompt(concept, contract, manifest, sysd, scen_inputs,
                     selective=selective, patch=True, frozen_modules=frozen_modules)
expect("patch: FIND/REPLACE 지시", "<<<<<<< FIND" in pp and ">>>>>>> REPLACE" in pp)
expect("patch: 통째 재출력 금지", "do NOT re-output whole files" in pp)
expect("patch: touched 본문 주입", "nextState.turn += 1;" in pp)
expect("patch: frozen 본문 비공개", "const initialEnemyCount = state.enemies.length;" not in pp)

# --- 3) selective 병합 + 골든(REF를 모델출력으로) ---
builder_out = f"=== FILE: src/game_logic.js ===\n{REF}\n"
sel_files = {n: b for n, b in parse_files(builder_out).items() if n.replace("\\", "/") in set(TOUCHED)}
expect("selective: 병합 후 touched=game_logic만", set(sel_files) == {"src/game_logic.js"})
gate_golden("selective", dict(sel_files))

# --- 4) patch 라운드트립 + 골든(base→REF 전체블록 패치) ---
base_logic = touched_src["src/game_logic.js"]
patch_resp = (f"=== PATCH: src/game_logic.js ===\n"
              f"<<<<<<< FIND\n{base_logic}\n=======\n{REF}\n>>>>>>> REPLACE\n")
pf = patch_apply.apply_patches(touched_src, patch_apply.parse_patches(patch_resp))
expect("patch: 복원 == REF(LF 바이트동일)",
       pf["src/game_logic.js"] == REF.replace("\r\n", "\n").replace("\r", "\n"))
gate_golden("patch", dict(pf))

# --- 5) gate 전 시나리오 크래시 잡기 ---
def make_crash_ws(crash_scn=None):
    files = {p.relative_to(BASE).as_posix(): p.read_text(encoding="utf-8")
             for p in sorted(BASE.glob("**/*.js"))}
    files["src/scenarios.js"] = injected_scenarios
    if crash_scn is not None:
        inj = (f"const _i=process.argv.indexOf('--scenario');"
               f"if(_i>=0 && process.argv[_i+1]==='{crash_scn}')"
               f"{{throw new Error('injected crash SCN{crash_scn}');}}\n")
        files["main.js"] = inj + files["main.js"]
    ws = BUILD_RUNS / "_harness_gate" / "workspace"
    if ws.parent.exists():
        shutil.rmtree(ws.parent)
    ws.mkdir(parents=True)
    write_candidate(ws, files)
    return ws


ok1, r1, _ = bg.gate_and_run(make_crash_ws(), manifest_v, scenarios)
expect("gate: 정상 빌드 통과", ok1)
ok2, r2, _ = bg.gate_and_run(make_crash_ws("2"), manifest_v, scenarios)
expect("gate: SCN2 크래시 → 거부", (not ok2) and "SCN2" in r2)

# --- 6) patch_apply 단위(게임 무관) ---
base = {"a.js": "line1\nfind_me\nline3\n", "b.js": "x\ny\nz\n"}
resp = "=== PATCH: a.js ===\n<<<<<<< FIND\nfind_me\n=======\nreplaced\n>>>>>>> REPLACE\n"
out = patch_apply.apply_patches(base, patch_apply.parse_patches(resp))
expect("단일 치환 적용", out == {"a.js": "line1\nreplaced\nline3\n"})
expect("패치 없는 파일은 결과에 없음", "b.js" not in out)
multi = ("=== PATCH: b.js ===\n<<<<<<< FIND\nx\n=======\nX\n>>>>>>> REPLACE\n"
         "<<<<<<< FIND\nz\n=======\nZ\n>>>>>>> REPLACE\n")
out2 = patch_apply.apply_patches(base, patch_apply.parse_patches(multi))
expect("한 파일 여러 쌍 순차 적용", out2 == {"b.js": "X\ny\nZ\n"})
crlf = patch_apply.apply_patches({"a.js": "p\r\nfind_me\r\nq\r\n"}, patch_apply.parse_patches(resp))
expect("CRLF base도 LF 정규화 후 매칭", crlf == {"a.js": "p\nreplaced\nq\n"})
expect_error("FIND 없으면 에러", lambda: patch_apply.apply_patches(
    base, patch_apply.parse_patches("=== PATCH: a.js ===\n<<<<<<< FIND\nnope\n=======\nr\n>>>>>>> REPLACE\n")))
expect_error("FIND 2회면 모호 에러", lambda: patch_apply.apply_patches(
    {"a.js": "dup\ndup\n"}, patch_apply.parse_patches(
        "=== PATCH: a.js ===\n<<<<<<< FIND\ndup\n=======\nr\n>>>>>>> REPLACE\n")))
expect_error("base에 없는 파일 패치면 에러", lambda: patch_apply.apply_patches(
    base, patch_apply.parse_patches("=== PATCH: zzz.js ===\n<<<<<<< FIND\nx\n=======\nr\n>>>>>>> REPLACE\n")))
expect_error("마커만 있고 쌍 없으면 에러",
             lambda: patch_apply.parse_patches("=== PATCH: a.js ===\n(no blocks)\n"))

shutil.rmtree(BUILD_RUNS / "_harness_selective", ignore_errors=True)
shutil.rmtree(BUILD_RUNS / "_harness_patch", ignore_errors=True)
shutil.rmtree(BUILD_RUNS / "_harness_gate", ignore_errors=True)

print("=== 하네스 키0 검증(레버4 selective·patch·gate, tactics 픽스처) ===")
allok = True
for name, res in checks:
    print(f"  [{'OK' if res else 'FAIL'}] {name}")
    allok = allok and res
print("\nRESULT:", "ALL PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
