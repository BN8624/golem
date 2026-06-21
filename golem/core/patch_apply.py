# 레버4 패치모드(§21.2 레버2) — 모델의 FIND/REPLACE 블록을 base 본문에 적용해 전체 파일을 복원
"""안2(앵커/search-replace) 포맷. 줄번호 없이 원문 토막을 그대로 베껴 바꿀 곳만 표시한다.

모델 출력 모양(파일별, 한 파일에 여러 쌍 허용):

    === PATCH: src/engine.js ===
    <<<<<<< FIND
    <base에 정확히 한 번 나오는 원문 토막>
    =======
    <대체 본문>
    >>>>>>> REPLACE

하네스가 base 본문에 순서대로 적용해 전체 파일 본문을 재구성한다(출력=diff, 적용=하네스).
FIND가 0번/2번 이상 나오면 PatchError — 통째 재출력 폴백은 두지 않는다(★키 A/B/patch 비교를
깨끗하게 유지·정확일치 규율). 적용 실패는 build_graded에서 CARD 실패로 분류된다."""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

import re

PATCH_RE = re.compile(r"^===\s*PATCH:\s*(.+?)\s*===\s*$", re.MULTILINE)
_BLOCK_RE = re.compile(
    r"<<<<<<<\s*FIND\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>>\s*REPLACE",
    re.DOTALL)


class PatchError(Exception):
    """패치 파싱·적용 실패(모델 출력 결함). CARD 실패로 본다."""


def _lf(s):
    """CRLF/CR을 LF로 통일 — 플랫폼 줄끝 차이로 FIND 매칭이 깨지지 않게."""
    return s.replace("\r\n", "\n").replace("\r", "\n")


def parse_patches(text):
    """'=== PATCH: name ===' 마커로 파일별 (find, replace) 쌍 목록을 뽑는다.
    반환 {경로: [(find, replace), ...]}. 마커는 있는데 쌍이 없으면 PatchError."""
    parts = PATCH_RE.split(text)   # [intro, name1, body1, name2, body2, ...]
    patches = {}
    for i in range(1, len(parts) - 1, 2):
        name = parts[i].strip()
        pairs = [(_lf(f), _lf(r)) for f, r in _BLOCK_RE.findall(parts[i + 1])]
        if not pairs:
            raise PatchError(f"{name}: PATCH 마커는 있으나 FIND/REPLACE 쌍 없음")
        patches[name] = pairs
    return patches


def _locate(cur, find):
    """cur에서 find의 유일 위치 (start, end)를 찾는다. exact 우선, 실패하면 줄끝 공백 무시 폴백.
    유일하지 않으면 PatchError. 앞 들여쓰기는 폴백서도 정확히 비교한다(오적용 방지)."""
    cnt = cur.count(find)
    if cnt == 1:
        i = cur.index(find)
        return i, i + len(find)
    if cnt > 1:
        raise PatchError(f"FIND 토막이 {cnt}회 — 모호함\n--FIND--\n{find[:200]}")
    # 폴백: 줄끝 공백만 무시한 전체-줄 블록 유일매치(흔한 LLM 차이). 앞 들여쓰기는 그대로 본다.
    f = find.strip("\n")
    if not f.strip():
        raise PatchError("FIND가 비었음")
    flines = [ln.rstrip() for ln in f.split("\n")]
    blines = cur.split("\n")
    n = len(flines)
    starts = [s for s in range(len(blines) - n + 1)
              if all(blines[s + k].rstrip() == flines[k] for k in range(n))]
    if len(starts) > 1:
        raise PatchError(f"FIND 토막이 {len(starts)}회(공백무시) — 모호함\n--FIND--\n{find[:200]}")
    if not starts:
        raise PatchError(f"FIND 토막이 base에 없음\n--FIND--\n{find[:200]}")
    s = starts[0]
    start = sum(len(blines[k]) + 1 for k in range(s))
    end = start + sum(len(blines[s + k]) + 1 for k in range(n)) - 1  # 블록 끝 \n 제외
    return start, end


def apply_patches(base_sources, patches):
    """base_sources {경로: 원본본문}에 patches를 적용해 {경로: 수정본} 반환.
    patches에 있는 파일만 결과에 담는다(touched). FIND는 base에 유일해야 한다(exact 우선·줄끝공백 폴백)."""
    out = {}
    for name, pairs in patches.items():
        if name not in base_sources:
            raise PatchError(f"{name}: base에 없는 파일에 패치")
        cur = _lf(base_sources[name])
        for find, repl in pairs:
            try:
                start, end = _locate(cur, _lf(find))
            except PatchError as e:
                raise PatchError(f"{name}: {e}")
            cur = cur[:start] + repl + cur[end:]
        out[name] = cur
    return out
