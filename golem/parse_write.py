# FILE 마커 멀티파일 파서/작성기 — 빌드 산출(=== FILE: name === 본문)을 파싱·기록하는 순수 헬퍼(공용 live)
"""build_graded·build·검증 스크립트가 공유하는 순수 함수. driver.py(legacy 빌드 흐름)에서 분리해
live 코드가 옛 bank/worker_prompt 흐름을 끌어오지 않게 한다. 의존 없음(re·pathlib만)."""

import re

FILE_RE = re.compile(r"^===\s*FILE:\s*(.+?)\s*===\s*$", re.MULTILINE)


def parse_files(text):
    """'=== FILE: name ===' 마커로 멀티파일 추출. 코드펜스(```)는 벗긴다."""
    parts = FILE_RE.split(text)   # [intro, name1, body1, name2, body2, ...]
    files = {}
    for i in range(1, len(parts) - 1, 2):
        files[parts[i].strip()] = _strip_fence(parts[i + 1])
    return files


def _strip_fence(body):
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    # 여는/닫는 펜스를 독립적으로 벗긴다. 모델이 전체 응답을 ```lang … ``` 한 덩이로 감싸면
    # 닫는 ```가 마지막 파일 본문 끝에만 남아(여는 펜스는 intro로 빠짐) 누출됐다(G81 잘림 3건).
    if lines and lines[0].lstrip().startswith("```"):
        lines.pop(0)
    if lines and lines[-1].strip().startswith("```"):
        lines.pop()
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) + "\n"


def write_candidate(out_dir, files):
    out_dir.mkdir(parents=True, exist_ok=True)
    root = out_dir.resolve()
    for name, body in files.items():
        p = (out_dir / name).resolve()
        if root != p and root not in p.parents:   # 경로 탈출 차단
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
