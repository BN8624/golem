# Golem Studio Step 5 Build(v1) — design 4모듈 manifest + Spec QA 시나리오로 빌드, 합의 채점(§13 Step5)
"""Build v0(스파이크)와 달리 (1) Planning 2파일 통짜가 아니라 Design의 분해 manifest를 목표로 주고,
(2) Spec QA의 구체 시나리오를 scenarios.json으로 공통 제공해 모든 빌드가 같은 입력을 받게 하고,
(3) 정답을 특권 golden이 아니라 **빌드들의 다수합의**로 잰다(사용자 산출물축소 우려 반영 — 오라클을
'우리'가 아니라 '자'로만 쓴다). 오라클위험(float 등)으로 표시된 시나리오는 채점에서 제외한다.

게이트(빌드별): static_gate + contract_validator(design manifest 정합) + 스모크.
채점: 게이트 통과 빌드들이 채점가능 시나리오에서 같은 출력에 모이나(시나리오별 다수합의 + 일치율).

사용:
  python golem/studio/build_graded.py [--cap 11]   # ★키
"""

import argparse
import json
import re
import subprocess
import sys
import threading
from collections import Counter
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))

import contract_validator                       # noqa: E402
import static_gate                              # noqa: E402
import patch_apply                              # noqa: E402
from driver import parse_files, write_candidate  # noqa: E402

MODEL_31 = "gemma-4-31b-it"

_PROMPT = """You are the BUILD engineer. Implement this design EXACTLY. Deterministic Node.js, CommonJS,
stdlib only, NO Math.random. Use named exports only (`exports.X` or `module.exports = {{ X }}`).

CONCEPT:
{concept}

RULES:
{rules}

MODULE DESIGN (responsibilities — split the logic this way, do NOT collapse into fewer files):
{system_design}

FILES YOU MUST CREATE (exact paths/exports/imports):
{files}
NOTE: the import paths listed above are project-root-relative (for reference). In actual require() calls use
MODULE-relative paths that resolve from the requiring file's OWN directory — e.g. from `src/engine.js`, require a
sibling in `src/` as `require('./game_logic')`, NOT `require('./src/game_logic')`. From `main.js` (at root),
require `require('./src/engine')`.

INPUT (FIXED — `scenarios.json` is a JSON array; `node main.js --scenario N` reads element N-1, 1-based,
and runs it deterministically). Match this EXACT input format (these are the real scenario elements you must
support — infer the shape precisely from them):
{input_examples}
Read the scenario element's setup / initial fields AND its config from the element itself, apply its actions
in order, then print the final state. Use the config values PROVIDED in the element — never invent your own.
NEVER crash on a missing optional field.

OUTPUT CONTRACT (FIXED — print EXACTLY these lines, this order, nothing else):
{output_block}

{provided_block}Output every file with EXACT markers, one per file:
=== FILE: <path> ===
<file body>
"""

_EDIT_HEADER = """You are the BUILD engineer making an INCREMENTAL EDIT to an EXISTING, WORKING codebase
(shown below). Do NOT rewrite from scratch. MODIFY the existing files to add ONLY this card's NEW rule(s),
keeping ALL existing behavior byte-for-byte intact — any scenario that does not use the new action MUST produce
identical output to before. Re-output the COMPLETE content of EVERY file with the same file markers (include
unchanged files verbatim). Keep the same module split.

EXISTING CODEBASE:
{base_code}

--- Now apply the card below on top of that codebase: ---

"""

# 레버4: 선택적 컨텍스트. 건드리는 모듈만 본문 주입, 나머지는 동결 인터페이스(시그니처)만.
_EDIT_HEADER_SELECTIVE = """You are the BUILD engineer making an INCREMENTAL EDIT to an EXISTING, WORKING
codebase. Do NOT rewrite from scratch. You are shown ONLY the modules this card touches, in full. The OTHER
modules are FROZEN and already verified — you see ONLY their public interface (signatures), never their bodies.
Call the frozen modules exactly by those signatures; assume they behave correctly. Keep every existing export
name/signature of the touched modules intact so the frozen modules keep working.

OUTPUT RULE: re-output ONLY these touched files, with file markers — {touched_list}. Do NOT output the frozen
modules; they are supplied unchanged by the harness. Any scenario not using the new action MUST produce output
identical to before.

TOUCHED MODULES (full source — edit these):
{touched_code}

FROZEN MODULES (interface only — call, do not reimplement, do not output):
{frozen_iface}

--- Now apply the card below on top of that codebase: ---

"""

# 레버4 패치모드(§21.2 레버2): touched 모듈도 통째 재출력하지 말고 바뀐 토막만 FIND/REPLACE로 낸다.
# 출력을 모듈 크기와도 분리한다(B는 게임 크기와만 분리). 적용은 하네스(patch_apply).
_EDIT_HEADER_PATCH = """You are the BUILD engineer making an INCREMENTAL EDIT to an EXISTING, WORKING
codebase. Do NOT rewrite from scratch. You are shown ONLY the modules this card touches, in full. The OTHER
modules are FROZEN and already verified — you see ONLY their public interface (signatures), never their bodies.
Call the frozen modules exactly by those signatures; assume they behave correctly. Keep every existing export
name/signature of the touched modules intact so the frozen modules keep working.

OUTPUT RULE: do NOT re-output whole files. Output ONLY the minimal CHANGES to the touched files as
search/replace patch blocks. For each change, copy an EXACT snippet from the touched source as FIND (long
enough to occur EXACTLY ONCE in that file — include surrounding lines if needed), then give the new text as
REPLACE. Use this EXACT format, one or more blocks per file:

=== PATCH: <path> ===
<<<<<<< FIND
<exact snippet copied verbatim from the touched source>
=======
<replacement text>
>>>>>>> REPLACE

Output NOTHING else — no prose, no whole files, no frozen modules. If a touched file needs NO change for this
card, output NO block for it (the harness keeps it unchanged). Any scenario not using the new action MUST
behave identically to before.

TOUCHED MODULES (full source — patch these):
{touched_code}

FROZEN MODULES (interface only — call, do not reimplement, do not output):
{frozen_iface}

--- Now apply the card below on top of that codebase: ---

"""


def _iface_stub(path, src, exports):
    """held-out 모듈을 본문 없이 시그니처만으로 표현(레버4). exports 각 이름의 `exports.NAME = ...`
    선언 첫 줄에서 화살표 파라미터만 남기고 본문은 가린다. 데이터(객체) export는 값을 가린다(런타임엔
    verbatim 복사본의 실제 값이 들어간다)."""
    lines = src.splitlines()
    out = [f"// {path} (FROZEN — 검증된 모듈, 본문 비공개. 시그니처대로 호출만. 이 파일은 출력하지 마라.)"]
    for name in exports:
        sig = None
        for ln in lines:
            m = re.match(rf"\s*exports\.{re.escape(name)}\s*=\s*(.*)", ln)
            if not m:
                continue
            rhs = m.group(1)
            if "=>" in rhs:
                params = rhs.split("=>", 1)[0].strip()
                sig = f"exports.{name} = {params} => {{ /* 본문 비공개 */ }};"
            else:
                sig = f"exports.{name} = /* 값 비공개(런타임에 실제 값 주입) */;"
            break
        out.append(sig or f"exports.{name} = /* 시그니처 미확인 */;")
    return "\n".join(out)


def load_all(pdir, ddir, sdir):
    contract = json.loads((pdir / "contract.json").read_text(encoding="utf-8"))
    concept = (pdir / "concept.md").read_text(encoding="utf-8") if (pdir / "concept.md").exists() else ""
    manifest = json.loads((ddir / "module_manifest.json").read_text(encoding="utf-8"))
    sysd = (ddir / "system_design.md").read_text(encoding="utf-8") if (ddir / "system_design.md").exists() else ""
    scen = json.loads((sdir / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
    risk = json.loads((sdir / "oracle_risk_review.json").read_text(encoding="utf-8"))
    return contract, concept, manifest, sysd, scen, risk


def _output_lines(state_shape):
    """출력계약 줄을 state_shape에서 도출 — 최상위 스칼라 필드 + logs (중첩 dict=config 등은 미출력)."""
    lines = []
    for k, v in state_shape.items():
        if k == "logs" or isinstance(v, dict):
            continue
        lines.append(f"{k}: <{v}>")
    lines.append('logs: <a JSON array of strings in order, e.g. [] if none>')
    return "\n".join(lines)


def _output_block(state_shape, output_contract=None):
    """프롬프트 OUTPUT CONTRACT 본문. output_contract(평면 필드·logs 없음)가 있으면 그걸 쓰고,
    없으면 기존 state_shape 스칼라+logs 동작(다른 게임 무손상)."""
    if output_contract and output_contract.get("lines"):
        return ("\n".join(output_contract["lines"])
                + "\nAll numeric state values are integers (use floor where a rule specifies). "
                  "Print NOTHING else — no logs, no extra lines.")
    return (_output_lines(state_shape)
            + "\nAll numeric state values are integers (use floor where a rule specifies). The `logs` line is "
              "a JSON array of\nlog strings in order (e.g. [] if none); emit a log ONLY where a rule explicitly "
              "says to, with that exact\nwording, and never as a separate bare line.")


def _provided_block(frozen_modules=None):
    """계약 데이터로 하네스가 미리 써넣는 고정 모듈(예: src/scenarios.js)을 프롬프트에 표시해
    모델이 그 인터페이스에 맞춰 나머지 파일을 짓게 한다. 없으면 빈 문자열(기존 동작)."""
    if not frozen_modules:
        return ""
    chunks = [f"=== FILE: {rel} ===\n{src}" for rel, src in frozen_modules.items()]
    return ("PROVIDED MODULE (already written by the harness — call it as-is; do NOT output it, do NOT "
            "redefine it):\n" + "\n\n".join(chunks)
            + "\nmain.js MUST read --scenario N, call getScenario(N) to obtain the world "
              "{initialState, actions}, and pass world.initialState and world.actions to the engine. "
              "Build the OTHER files normally.\n\n")


def _gen_scenarios_module(scenario_data):
    """계약 scenario_data(고정 세계)에서 src/scenarios.js 본문 생성 — 모든 빌드가 동일 세계를 받게 한다."""
    worlds = [{"initialState": s["initialState"], "actions": s["actions"]} for s in scenario_data]
    body = json.dumps(worlds, ensure_ascii=False, indent=2)
    return ("// 전술 커널 시나리오 세계(계약 고정·하네스 주입). getScenario(n)은 1-based n번 세계를 반환한다.\n"
            f"const SCENARIOS = {body};\n"
            "exports.getScenario = (n) => SCENARIOS[n - 1] || null;\n")


def build_prompt(concept, contract, manifest, sysd, scen_inputs, base_code=None, selective=None,
                 patch=False, frozen_modules=None):
    rules = contract.get("data_contract", {}).get("rules", [])
    state_shape = contract.get("data_contract", {}).get("state_shape", {})
    output_contract = contract.get("data_contract", {}).get("output_contract")
    examples = json.dumps(scen_inputs[:3], ensure_ascii=False, indent=2)
    files_desc = "\n".join(
        f"- {f['path']}: exports {f.get('exports', [])}, imports {f.get('imports', [])}"
        for f in manifest.get("files", []))
    body = _PROMPT.format(concept=concept.strip() or "(none)",
                          rules="\n".join(f"- {r}" for r in rules) or "(none)",
                          system_design=sysd.strip() or "(none)", files=files_desc,
                          input_examples=examples,
                          output_block=_output_block(state_shape, output_contract),
                          provided_block=_provided_block(frozen_modules))
    if selective:  # 레버4: 건드리는 모듈만 본문 + 나머지 동결 인터페이스
        header = _EDIT_HEADER_PATCH if patch else _EDIT_HEADER_SELECTIVE
        return header.format(
            touched_list=", ".join(selective["touched_paths"]),
            touched_code=selective["touched_code"],
            frozen_iface=selective["frozen_iface"]) + body
    if base_code:  # 편집 모드(레버1·2): 기존 코드 주입 + scratch 금지 헤더
        return _EDIT_HEADER.format(base_code=base_code) + body
    return body


def _norm_output(stdout):
    """key:value 출력을 정규화(dict) — 합의 비교용. 줄 순서 무관."""
    d = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            d[k.strip()] = v.strip()
    if "logs" in d:  # 공백·따옴표 차이로 헛갈리지 않게 JSON 정규화(순서는 보존)
        try:
            d["logs"] = json.dumps(json.loads(d["logs"]))
        except Exception:  # noqa: BLE001
            pass
    return tuple(sorted(d.items()))


def _canon(val):
    """빌드 stdout 문자열이든 oracle 파이썬 값이든 같은 캐노니컬 JSON 문자열로 만든다.
    표현차(파이썬 repr vs JS JSON: None/'None'·True/'true', dict 키순서·공백, 리스트 출력)를
    제거해 거짓 불일치를 막는다. G52는 None/bool 스칼라만 맞췄으나 entities 같은 구조적 출력은
    여전히 str()로 새 거짓 불일치를 냈다(G55) — JSON 정규화로 스칼라·구조 모두 통일한다.
    파싱 불가한 순수 문자열(예: 'RUNNING')은 그대로 둔다."""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except (ValueError, TypeError):
            return val
    return json.dumps(val, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def classify_attempt_failure(reason):
    """게이트 실패 사유를 기존 라벨 어휘로 사전분류(키0, G48). 카드 탓 전에 INFRA/HARNESS 먼저 분리.
    INFRA=plan2 INFRA_FAIL(api·network·쿼터) / HARNESS=plan2 HARNESS_FAIL(우리 도구 크래시) /
    CARD=plan2 MODEL_FAIL(생성 코드·계약 난이도: static/contract/스모크 실패). 새 taxonomy 도입 아님."""
    from observability import INFRA_MARKERS
    t = str(reason).lower()
    if t.startswith("infra:") or any(m in t for m in INFRA_MARKERS):
        return "INFRA"
    if t.startswith("harness:"):
        return "HARNESS"
    return "CARD"


def gate_and_run(workspace, manifest, scenarios):
    """게이트 통과 시 채점가능 시나리오를 실행해 출력 dict 반환. (ok, reason, outputs) ."""
    sg = static_gate.check(str(workspace))
    if not sg["ok"]:
        return False, f"static_gate: {sg['reason']}", {}
    mpath = workspace.parent / "module_manifest.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cv = contract_validator.validate(workspace, mpath, strict=False)  # 빌드=자유구현 수용
    if not cv["ok"]:
        return False, f"contract_validator: {cv['errors'][:2]}", {}
    outputs = {}
    for i, sc in enumerate(scenarios, 1):
        try:
            r = subprocess.run(["node", "main.js", "--scenario", str(i)], cwd=str(workspace),
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=30, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return False, f"smoke SCN{i}: 타임아웃", {}
        if r.returncode != 0:
            return False, f"smoke SCN{i}: exit {r.returncode} out={r.stdout[:80]!r}", {}
        if i == 1 and ":" not in r.stdout:
            return False, f"smoke SCN1: 출력 형식 의심 out={r.stdout[:80]!r}", {}
        outputs[sc["id"]] = _norm_output(r.stdout)
    return True, "ok", outputs


MIN_VOTERS = 2  # 합의는 최소 2표부터 의미 — 1표는 자기자신과 자명히 1.0(G55 표본수 오염 가드)


def consensus(passed_outputs, gradeable_ids):
    """시나리오별 다수합의 + 일치율. passed_outputs: {build: {scen_id: norm_output}}.
    overall은 표 ≥ MIN_VOTERS 시나리오만 평균(자명한 1표 합의 제외) — 표 부족이면 None을 돌려
    카드 간 합의 비교가 표본수에 오염되지 않게 한다(G55)."""
    report = {}
    for sid in gradeable_ids:
        votes = [outs.get(sid) for outs in passed_outputs.values() if outs.get(sid) is not None]
        if not votes:
            report[sid] = {"agree": 0, "total": 0, "rate": 0.0}
            continue
        top, n = Counter(votes).most_common(1)[0]
        report[sid] = {"agree": n, "total": len(votes), "rate": round(n / len(votes), 3)}
    rates = [r["rate"] for r in report.values() if r["total"] >= MIN_VOTERS]
    overall = round(sum(rates) / len(rates), 3) if rates else None
    return overall, report


def _golden_diff(passed_outputs, scenarios, gradeable, contract):
    """합의(다수) vs golden(expected) 자동 대조 — 출력표면 키만. 수작업 diff 제거(키0).
    각 항목에 reconcile.resolve가 쓰는 `input`(채점메타 제외 시나리오)도 담는다."""
    ss = contract.get("data_contract", {}).get("state_shape", {})
    oc = contract.get("data_contract", {}).get("output_contract")
    if oc and oc.get("fields"):
        output_keys = set(oc["fields"])
    else:
        output_keys = {k for k, v in ss.items() if not isinstance(v, dict)}
    grading = {"id", "expected", "oracle_risk", "covers_reqs"}
    by_id = {s["id"]: s for s in scenarios}
    diffs = []
    for sid in gradeable:
        votes = [outs[sid] for outs in passed_outputs.values() if outs.get(sid) is not None]
        if not votes:
            continue
        top = Counter(votes).most_common(1)[0]
        cons = dict(top[0])
        sc = by_id.get(sid, {})
        exp = sc.get("expected") or {}
        d = {k: {"consensus": _canon(cons.get(k)), "oracle": _canon(exp[k])}
             for k in (set(exp) & output_keys) if _canon(cons.get(k)) != _canon(exp[k])}
        if d:
            diffs.append({"id": sid, "input": {k: v for k, v in sc.items() if k not in grading},
                          "differing": d, "agreement": {"agree": top[1], "total": len(votes)}})
    return diffs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", default=str(HERE / "planning_packet"))
    ap.add_argument("--design", default=str(HERE / "design_packet"))
    ap.add_argument("--base", default=None,
                    help="누적 빌드(편집 모드): 기존 코드 디렉토리를 주입하고 scratch 대신 수정시킴. "
                         "design(manifest)도 이 디렉토리에서 읽는다.")
    ap.add_argument("--inject-modules", default=None,
                    help="레버4(선택적 컨텍스트): 이번 카드가 건드리는 모듈만 본문 주입(쉼표구분, base 기준 "
                         "상대경로). 나머지 base 모듈은 시그니처만 주고 verbatim 복사한다. --base 필요.")
    ap.add_argument("--patch", action="store_true",
                    help="레버4 패치모드(§21.2 레버2): touched 모듈도 통째 재출력 대신 FIND/REPLACE diff만 "
                         "내게 하고 하네스가 base에 적용. 출력을 모듈 크기와도 분리. --inject-modules 필요.")
    ap.add_argument("--specqa", default=str(HERE / "specqa_packet"))
    ap.add_argument("--cap", type=int, default=11)
    ap.add_argument("--out", default=None)
    ap.add_argument("--reconcile", action="store_true",
                    help="빌드 후 합의-vs-oracle 불일치를 모델로 진단/라우팅(★키)")
    ap.add_argument("--apply", action="store_true",
                    help="--reconcile 진단 중 AUTO만 자동 적용(ESCALATE는 사람 대기)")
    args = ap.parse_args(argv)
    if args.patch and not args.inject_modules:
        ap.error("--patch는 --inject-modules와 함께 써야 한다(레버4 위에서 동작).")

    import os
    os.environ["GENERATOR_MODEL"] = MODEL_31
    os.environ["CRITIC_MODEL"] = MODEL_31
    from config import force_utf8_stdout, get_api_keys
    from llm import AllKeysExhausted, KeyPool, LLMClient
    force_utf8_stdout()

    ddir = Path(args.base) if args.base else Path(args.design)
    contract, concept, manifest, sysd, scenarios, risk = load_all(
        Path(args.packet), ddir, Path(args.specqa))
    risky = set(risk.get("risky_scenarios", []))
    gradeable = [s["id"] for s in scenarios if s["id"] not in risky and s.get("expected") is not None]
    grading_keys = {"id", "expected", "oracle_risk", "covers_reqs"}
    scen_inputs = [{k: v for k, v in s.items() if k not in grading_keys} for s in scenarios]

    # 계약 scenario_data가 있으면 src/scenarios.js를 그 고정 세계로 하네스가 써넣어 모든 빌드가
    # 동일 입력을 받게 한다(scratch 전용; --base는 held_out 메커니즘이 따로 있음).
    frozen_modules = {}
    scenario_data = contract.get("data_contract", {}).get("scenario_data")
    if scenario_data and not args.base:
        frozen_modules["src/scenarios.js"] = _gen_scenarios_module(scenario_data)

    base_code = None
    selective = None
    held_out = []  # 레버4: (상대경로, 원본소스) — 워크스페이스에 verbatim 복사
    if args.base:
        bdir = Path(args.base)
        all_js = sorted(bdir.glob("**/*.js"))
        if args.inject_modules:  # 레버4: 건드리는 모듈만 본문, 나머지는 시그니처+verbatim
            touched_paths = [m.strip().replace("\\", "/") for m in args.inject_modules.split(",")]
            exports_by_path = {f["path"]: f.get("exports", []) for f in manifest.get("files", [])}
            touched_chunks, frozen_chunks, touched_src = [], [], {}
            for p in all_js:
                rel = p.relative_to(bdir).as_posix()
                src = p.read_text(encoding="utf-8")
                if rel in touched_paths:
                    touched_chunks.append(f"=== FILE: {rel} ===\n{src}")
                    touched_src[rel] = src
                else:
                    frozen_chunks.append(_iface_stub(rel, src, exports_by_path.get(rel, [])))
                    held_out.append((rel, src))
            selective = {"touched_paths": touched_paths,
                         "touched_code": "\n\n".join(touched_chunks),
                         "frozen_iface": "\n\n".join(frozen_chunks),
                         "touched_src": touched_src}
        else:  # 레버1: 기존 코드(.js 전부)를 FILE 마커 형식으로 주입
            base_code = "\n\n".join(
                f"=== FILE: {p.relative_to(bdir).as_posix()} ===\n{p.read_text(encoding='utf-8')}"
                for p in all_js)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = Path(args.out) if args.out else (HERE / "build_runs" / f"graded-{run_id}")
    prompt = build_prompt(concept, contract, manifest, sysd, scen_inputs,
                          base_code=base_code, selective=selective, patch=args.patch,
                          frozen_modules=frozen_modules)
    pool = KeyPool(get_api_keys(), models=[MODEL_31])
    mode = (("EDIT/패치" if args.patch else "EDIT/선택적") if selective
            else ("EDIT/누적" if args.base else "SCRATCH"))
    extra = f" touched={selective['touched_paths']} frozen={len(held_out)}" if selective else ""
    print(f"[BUILD v1/{mode}] manifest {len(manifest.get('files', []))}모듈, 시나리오 {len(scenarios)}"
          f"(채점가능 {len(gradeable)}), cap={args.cap} keys={pool.size}, run={run_id}{extra}")

    manifest_v = {"schema_version": "0.1", "module_format": "commonjs", **manifest}
    lock = threading.Lock()
    passed_outputs = {}
    failures = []
    cracked = None

    def worker(attempt):
        try:
            with pool.checkout() as key:
                resp = LLMClient(api_key=key).generate("critic", prompt)
        except AllKeysExhausted:
            raise
        except Exception as e:  # noqa: BLE001 — 생성 단계 실패는 api/network(INFRA)
            return attempt, False, f"infra: gen {type(e).__name__}: {e}", {}
        ws = base / f"attempt{attempt:02d}" / "workspace"
        ws.mkdir(parents=True, exist_ok=True)
        (ws.parent / "_raw_response.txt").write_text(resp, encoding="utf-8")  # 출력토큰 정량 대조용
        try:  # 파싱·쓰기·게이트는 우리 하네스 — 여기 크래시는 HARNESS(카드 탓 아님), 런 안 깨고 기록
            if args.patch:  # 레버4 패치모드: FIND/REPLACE diff를 base touched 본문에 적용해 전체 복원
                try:
                    patches = patch_apply.parse_patches(resp)
                    files = patch_apply.apply_patches(selective["touched_src"], patches)
                except patch_apply.PatchError as pe:
                    return attempt, False, f"patch: {pe}", {}
                for rel, src in selective["touched_src"].items():  # 패치 안 한 touched=안 바꿈→base verbatim
                    files.setdefault(rel, src)
            else:
                files = parse_files(resp)  # {경로: 본문}
            if selective:  # 레버4: 동결 모듈은 빌더 출력 무시하고 base 원본을 verbatim 강제
                touched = set(selective["touched_paths"])
                files = {n: b for n, b in files.items() if n.replace("\\", "/") in touched}
                for rel, src in held_out:
                    files[rel] = src
            for rel, src in frozen_modules.items():  # 계약 고정 모듈(scenario_data 등)을 verbatim 강제
                files[rel] = src
            write_candidate(ws, files)
            (ws / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")
            ok, reason, outputs = gate_and_run(ws, manifest_v, scenarios)
        except Exception as e:  # noqa: BLE001
            return attempt, False, f"harness: {type(e).__name__}: {e}", {}
        return attempt, ok, reason, outputs

    with ThreadPoolExecutor(max_workers=min(pool.size, args.cap)) as ex:
        futs = {ex.submit(worker, a): a for a in range(1, args.cap + 1)}
        for fut in as_completed(futs):
            try:
                a, ok, reason, outputs = fut.result()
            except CancelledError:
                continue
            except AllKeysExhausted as e:
                print(f"[BUILD v1] 중단: {e}")
                break
            print(f"  [attempt {a:02d}] gate={ok} {reason}")
            if ok:
                with lock:
                    passed_outputs[a] = outputs
                    if cracked is None:
                        cracked = a
            else:
                with lock:
                    failures.append(reason)

    overall, report = consensus(passed_outputs, gradeable)
    golden_diffs = _golden_diff(passed_outputs, scenarios, gradeable, contract)
    fail_classes = Counter(classify_attempt_failure(r) for r in failures)
    scored = [r["total"] for r in report.values() if r["total"] >= MIN_VOTERS]
    voters = {"min_voters": MIN_VOTERS, "scenarios_scored": len(scored),
              "mean_voters": round(sum(scored) / len(scored), 2) if scored else 0}
    base.mkdir(parents=True, exist_ok=True)
    (base / "_prompt.txt").write_text(prompt, encoding="utf-8")  # 입력크기 대조용(런당 1개)
    (base / "consensus.json").write_text(json.dumps(
        {"gate_passed": len(passed_outputs), "cap": args.cap,
         "gradeable": gradeable, "overall_agreement": overall, "voters": voters,
         "per_scenario": report, "golden_diffs": golden_diffs,
         "failure_classes": dict(fail_classes), "gate_failed_reasons": failures},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[BUILD v1] 게이트 통과 {len(passed_outputs)}/{args.cap}, "
          f"합의 채점(채점가능 {len(gradeable)}): 전체 일치율 {overall} "
          f"(채점시나리오 {voters['scenarios_scored']}, 평균 {voters['mean_voters']}표)")
    if overall is None or voters["mean_voters"] < 3:
        print("  [표본수 주의] 표 부족(평균<3) — 합의값이 표본수에 오염될 수 있음. 카드 간 비교는 cap↑로 표 맞춘 뒤(G55).")
    if failures:  # 실패 사전분류(G48): 카드 탓 전에 INFRA/HARNESS 먼저 분리
        print("  [실패 사전분류] " + ", ".join(f"{k}={v}" for k, v in fail_classes.items())
              + "  (INFRA·HARNESS는 카드 실패로 안 셈 — 하네스 수정 후 재실행)")
    for sid, r in report.items():
        print(f"    {sid}: 합의 {r['agree']}/{r['total']} (일치율 {r['rate']})")
    if golden_diffs:  # 합의-vs-oracle 자동 diff(키0) — 수작업 제거
        print(f"  [합의 vs oracle] 불일치 {len(golden_diffs)}건 — reconcile --resolve로 진단(★키):")
        for d in golden_diffs:
            print("    - " + d["id"] + ": " + ", ".join(
                f"{k}(합의={v['consensus']} vs oracle={v['oracle']})" for k, v in d["differing"].items()))
    else:
        print("  [합의 vs oracle] 전부 일치.")

    if args.reconcile and golden_diffs:  # T0: diff → resolve(★키) → AUTO apply → ESCALATE/BUILD_BUG 리포트
        import reconcile  # 늦은 import(순환 방지)
        rules = contract["data_contract"]["rules"]
        rc = reconcile.RealCaller()
        verdicts = []
        for d in golden_diffs:
            v = rc.resolve(rules, d)
            v["id"] = d["id"]
            verdicts.append(v)
            print(f"    [{v.get('diagnosis')}/{v.get('class')}] {d['id']}: {v.get('reason', '')}")
        guarded = reconcile.apply_low_consensus_guard(verdicts, golden_diffs)
        if guarded:
            print(f"  [저합의 가드] AUTO→ESCALATE 강등 {len(guarded)}: {guarded}")
        applied = reconcile.apply_fixes(
            verdicts, Path(args.packet) / "contract.json",
            Path(args.specqa) / "acceptance_tests_draft.json", scenarios) if args.apply else []
        auto_verification = reconcile.verify_auto_fixes(
            verdicts, golden_diffs, Path(args.specqa) / "auto_fix_ledger.jsonl", run_id) \
            if args.apply else []
        escalate = [v["id"] for v in verdicts if v.get("class") == "ESCALATE"]
        build_bugs = [v["id"] for v in verdicts if v.get("diagnosis") == "BUILD_BUG"]
        auto_summary = reconcile.summarize_auto_verification(auto_verification)
        (base / "reconcile_report.json").write_text(json.dumps(
            {"verdicts": verdicts, "applied": applied, "auto_verification": auto_verification,
             "auto_summary": auto_summary,
             "low_consensus_guarded": guarded, "escalate": escalate, "build_bugs": build_bugs},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [reconcile] 자동적용 {len(applied)}, ESCALATE(사람) {len(escalate)}, BUILD_BUG {len(build_bugs)}")
        for a in applied:
            print(f"    적용: {a}")
        for c in auto_verification:
            flag = " ★되돌림" if c["reverted_prior"] else ""
            print(f"    [AUTO검증] {c['id']}: {c['status']} (합의율 {c['consensus_rate']}){flag}")
        if auto_summary["green_blocked"]:
            print(f"    ★GREEN 금지 — auto_suspect {auto_summary['auto_suspect']}건"
                  f"(confidently-wrong 적용 후보). ESCALATE 수와 무관하게 사람 확인 필요.")
        if build_bugs:
            print(f"    ★재빌드 권장(BUILD_BUG {build_bugs}) — 계약 정본 그대로, 빌드만 다시.")
        for sid in escalate:
            print(f"    ★ESCALATE {sid} — 사람 결정 필요.")

    print(f"[BUILD v1] → {base}")
    return 0 if passed_outputs else 1


if __name__ == "__main__":
    raise SystemExit(main())
