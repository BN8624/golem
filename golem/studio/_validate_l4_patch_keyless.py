# 레버4 패치모드 배선을 키0으로 검증한다(FIND/REPLACE 파싱·적용·에러 + B와 동일 검증상태 도달)
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_graded as bg
import patch_apply
from driver import write_candidate

checks = []


def expect(name, cond):
    checks.append((name, bool(cond)))


def expect_error(name, fn):
    try:
        fn()
        checks.append((name, False))
    except patch_apply.PatchError:
        checks.append((name, True))


# --- 1) 적용기 단위 검증 ---
base = {"a.js": "line1\nfind_me\nline3\n", "b.js": "x\ny\nz\n"}
resp = (
    "=== PATCH: a.js ===\n"
    "<<<<<<< FIND\nfind_me\n=======\nreplaced\n>>>>>>> REPLACE\n"
)
patches = patch_apply.parse_patches(resp)
out = patch_apply.apply_patches(base, patches)
expect("단일 치환 적용", out == {"a.js": "line1\nreplaced\nline3\n"})
expect("패치 없는 파일은 결과에 없음", "b.js" not in out)

multi = (
    "=== PATCH: b.js ===\n"
    "<<<<<<< FIND\nx\n=======\nX\n>>>>>>> REPLACE\n"
    "<<<<<<< FIND\nz\n=======\nZ\n>>>>>>> REPLACE\n"
)
out2 = patch_apply.apply_patches(base, patch_apply.parse_patches(multi))
expect("한 파일 여러 쌍 순차 적용", out2 == {"b.js": "X\ny\nZ\n"})

# touched인데 패치 없는 파일 = base verbatim 폴백(build_graded 워커 재현)
def merge_unpatched(touched_src, resp):
    files = patch_apply.apply_patches(touched_src, patch_apply.parse_patches(resp))
    for rel, src in touched_src.items():
        files.setdefault(rel, src)
    return files
merged = merge_unpatched(base, "=== PATCH: a.js ===\n<<<<<<< FIND\nfind_me\n=======\nR\n>>>>>>> REPLACE\n")
expect("touched 중 패치 안 한 b.js는 base verbatim",
       merged["b.js"] == base["b.js"] and merged["a.js"] == "line1\nR\nline3\n")

crlf = patch_apply.apply_patches(
    {"a.js": "p\r\nfind_me\r\nq\r\n"},
    patch_apply.parse_patches(resp))
expect("CRLF base도 LF 정규화 후 매칭", crlf == {"a.js": "p\nreplaced\nq\n"})

expect_error("FIND 없으면 에러", lambda: patch_apply.apply_patches(
    base, patch_apply.parse_patches(
        "=== PATCH: a.js ===\n<<<<<<< FIND\nnope\n=======\nr\n>>>>>>> REPLACE\n")))
expect_error("FIND 2회면 모호 에러", lambda: patch_apply.apply_patches(
    {"a.js": "dup\ndup\n"}, patch_apply.parse_patches(
        "=== PATCH: a.js ===\n<<<<<<< FIND\ndup\n=======\nr\n>>>>>>> REPLACE\n")))
expect_error("base에 없는 파일 패치면 에러", lambda: patch_apply.apply_patches(
    base, patch_apply.parse_patches(
        "=== PATCH: zzz.js ===\n<<<<<<< FIND\nx\n=======\nr\n>>>>>>> REPLACE\n")))
expect_error("마커만 있고 쌍 없으면 에러",
             lambda: patch_apply.parse_patches("=== PATCH: a.js ===\n(no blocks)\n"))

# --- 2) 프롬프트 모양(patch=True) ---
BASE = HERE / "rocket_base"
contract, concept, manifest, sysd, scenarios, risk = bg.load_all(
    HERE / "planning_packet_rocket_l4", BASE, HERE / "specqa_packet_rocket_l4")
grading_keys = {"id", "expected", "oracle_risk", "covers_reqs"}
scen_inputs = [{k: v for k, v in s.items() if k not in grading_keys} for s in scenarios]

touched_paths = ["src/engine.js"]
exports_by_path = {f["path"]: f.get("exports", []) for f in manifest.get("files", [])}
touched_chunks, frozen_chunks, held_out, touched_src = [], [], [], {}
for p in sorted(BASE.glob("**/*.js")):
    rel = p.relative_to(BASE).as_posix()
    src = p.read_text(encoding="utf-8")
    if rel in touched_paths:
        touched_chunks.append(f"=== FILE: {rel} ===\n{src}")
        touched_src[rel] = src
    else:
        frozen_chunks.append(bg._iface_stub(rel, src, exports_by_path.get(rel, [])))
        held_out.append((rel, src))
selective = {"touched_paths": touched_paths, "touched_code": "\n\n".join(touched_chunks),
             "frozen_iface": "\n\n".join(frozen_chunks), "touched_src": touched_src}
prompt = bg.build_prompt(concept, contract, manifest, sysd, scen_inputs, selective=selective, patch=True)
expect("patch 프롬프트: FIND/REPLACE 지시", "<<<<<<< FIND" in prompt and ">>>>>>> REPLACE" in prompt)
expect("patch 프롬프트: 통째 재출력 금지", "do NOT re-output whole files" in prompt)
expect("patch 프롬프트: touched 본문 주입", "applyWait(state, config)" in prompt)
expect("patch 프롬프트: 동결 본문 비공개", "state.turn + 1" not in prompt)

# --- 3) end-to-end 등가: 패치 적용 결과가 B(통째출력) 참조와 바이트동일 + 골든 재현 ---
# 참조 engine.js = 통째출력 B가 내는 최종본. 베이스→참조 전체치환 패치로 동일 상태에 도달함을 보인다.
ref_engine = (HERE / "build_runs" / "_l4_golden_derive" / "src" / "engine.js").read_text(encoding="utf-8")
base_engine = touched_src["src/engine.js"]
patch_resp = (f"=== PATCH: src/engine.js ===\n"
              f"<<<<<<< FIND\n{base_engine}\n=======\n{ref_engine}\n>>>>>>> REPLACE\n")
files = patch_apply.apply_patches(touched_src, patch_apply.parse_patches(patch_resp))
expect("패치 복원 == B 참조본(LF 기준 바이트동일)",
       files["src/engine.js"] == ref_engine.replace("\r\n", "\n").replace("\r", "\n"))
for rel, src in held_out:
    files[rel] = src

ws = HERE / "build_runs" / "_l4_patch_validate" / "workspace"
if ws.parent.exists():
    shutil.rmtree(ws.parent)
ws.mkdir(parents=True)
write_candidate(ws, files)
(ws / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")
manifest_v = {"schema_version": "0.1", "module_format": "commonjs", **manifest}
ok, reason, outputs = bg.gate_and_run(ws, manifest_v, scenarios)
expect("게이트 통과", ok)

match = 0
for s in scenarios:
    got_d = dict(outputs.get(s["id"]) or {})
    okm = all(got_d.get(k) is not None for k in s["expected"]) and all(
        bg._canon(got_d.get(k)) == bg._canon(json.dumps(v) if isinstance(v, (list, dict)) else str(v))
        for k, v in s["expected"].items())
    match += okm
expect(f"골든 재현 {match}/{len(scenarios)}", match == len(scenarios))

print("=== 패치모드 키0 검증 ===")
allok = True
for name, res in checks:
    print(f"  [{'OK' if res else 'FAIL'}] {name}")
    allok = allok and res
print("\nRESULT:", "ALL PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
