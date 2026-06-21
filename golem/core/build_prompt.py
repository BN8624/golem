# 빌드 프롬프트/컨텍스트 조립 — 템플릿·build_prompt·헬퍼(★키 경로 보수 분해). 출력=프롬프트 문자열만
"""build_graded에서 분리. 모델 입력 프롬프트 문자열 생성이 전부 — 문자열 동일=★키 동작 동일.
의존: re·json·stdlib만(build_graded 역참조 없음=순환 방지). build_graded가 re-export."""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

import json
import re



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
REPLACE. Copy the FIND snippet's indentation and whitespace EXACTLY as in the source. Prefer several small,
clearly-unique FIND blocks over one large block. Use this EXACT format, one or more blocks per file:

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
