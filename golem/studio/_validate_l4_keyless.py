# 레버4 선택적 컨텍스트 배선을 키0으로 검증한다(프롬프트 가림 + verbatim 병합 + 골든 재현)
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_graded as bg
from driver import parse_files

BASE = HERE / "rocket_base"
contract, concept, manifest, sysd, scenarios, risk = bg.load_all(
    HERE / "planning_packet_rocket_l4", BASE, HERE / "specqa_packet_rocket_l4")
grading_keys = {"id", "expected", "oracle_risk", "covers_reqs"}
scen_inputs = [{k: v for k, v in s.items() if k not in grading_keys} for s in scenarios]

# main()의 selective 번들 구성 재현
touched_paths = ["src/engine.js"]
exports_by_path = {f["path"]: f.get("exports", []) for f in manifest.get("files", [])}
touched_chunks, frozen_chunks, held_out = [], [], []
for p in sorted(BASE.glob("**/*.js")):
    rel = p.relative_to(BASE).as_posix()
    src = p.read_text(encoding="utf-8")
    if rel in touched_paths:
        touched_chunks.append(f"=== FILE: {rel} ===\n{src}")
    else:
        frozen_chunks.append(bg._iface_stub(rel, src, exports_by_path.get(rel, [])))
        held_out.append((rel, src))
selective = {"touched_paths": touched_paths,
             "touched_code": "\n\n".join(touched_chunks),
             "frozen_iface": "\n\n".join(frozen_chunks)}
prompt = bg.build_prompt(concept, contract, manifest, sysd, scen_inputs, selective=selective)

checks = []
checks.append(("engine 본문 주입(applyWait 호출 포함)", "applyWait(state, config)" in prompt))
checks.append(("logic 본문 비공개(누적 로직 'turn: state.turn + 1' 없음)", "state.turn + 1" not in prompt))
checks.append(("logic 시그니처 공개(applyWait 인터페이스)",
               "exports.applyWait = (state, constants) =>" in prompt))
checks.append(("constants 값 비공개(stageCost 배열 본문 없음)", "[2, 3, 4, 5]" not in prompt))
checks.append(("ABORT 규칙 주입", "ABORT" in prompt and "ABORTED" in prompt))
checks.append(("touched만 출력 지시", "src/engine.js" in prompt and "Do NOT output the frozen" in prompt))

# 워커 selective 병합 재현: 빌더가 engine만 출력(=참조 답) + 동결 verbatim 병합
ref_resp = (HERE / "build_runs" / "_l4_golden_derive" / "src" / "engine.js").read_text(encoding="utf-8")
builder_out = f"=== FILE: src/engine.js ===\n{ref_resp}\n"
files = parse_files(builder_out)
touched = set(selective["touched_paths"])
files = {n: b for n, b in files.items() if n.replace("\\", "/") in touched}
for rel, src in held_out:
    files[rel] = src
checks.append(("병합 후 4파일 전부(verbatim 포함)",
               set(files) == {"src/engine.js", "src/logic.js", "src/constants.js", "main.js"}))
checks.append(("동결 logic verbatim 일치", files["src/logic.js"] == (BASE / "src/logic.js").read_text(encoding="utf-8")))

# 게이트+실행으로 골든 재현
ws = HERE / "build_runs" / "_l4_validate" / "workspace"
if ws.parent.exists():
    shutil.rmtree(ws.parent)
ws.mkdir(parents=True)
from driver import write_candidate
write_candidate(ws, files)
(ws / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")
manifest_v = {"schema_version": "0.1", "module_format": "commonjs", **manifest}
ok, reason, outputs = bg.gate_and_run(ws, manifest_v, scenarios)
checks.append(("게이트 통과", ok))

# 출력 vs 골든
match = 0
for s in scenarios:
    exp = bg._norm_output("\n".join(f"{k}: {json.dumps(v) if isinstance(v,(list,dict)) else v}"
                                    for k, v in s["expected"].items()))
    got = outputs.get(s["id"])
    # expected엔 log 없음 → 부분비교: expected 키만
    got_d = dict(got) if got else {}
    exp_keys = set(s["expected"])
    okm = all(got_d.get(k) is not None for k in exp_keys) and all(
        bg._canon(got_d.get(k)) == bg._canon(json.dumps(v) if isinstance(v, (list, dict)) else str(v))
        for k, v in s["expected"].items())
    match += okm
    print(f"  {s['id']}: {'OK' if okm else 'MISMATCH'}  got={got_d}")
checks.append((f"골든 재현 {match}/{len(scenarios)}", match == len(scenarios)))

print("\n=== 검증 ===")
allok = True
for name, res in checks:
    print(f"  [{'OK' if res else 'FAIL'}] {name}")
    allok = allok and res
print("\nRESULT:", "ALL PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
