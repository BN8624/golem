# 카드 생성 레저 — 검토 교훈(부정 예시)·검증된 패턴(좋은 예시)을 적재하고 제안기 프롬프트용으로 검색한다(키0)
"""사람 검토를 코드로 흡수하는 RAG-lite 저장소. 규모가 작으니 임베딩 없이 game/scope로 필터해 전부 주입한다.
- lessons.jsonl : 부정 예시(이러지 마라). 검토에서 잡힌 드리프트를 재사용 가능한 가드로.
- exemplars.jsonl: 긍정 예시(이렇게 깨끗하게). 검증 그린 카드의 최소 패턴.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR = HERE / "cardgen"
LESSONS = DIR / "lessons.jsonl"
EXEMPLARS = DIR / "exemplars.jsonl"


def _load(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def retrieve(game):
    """해당 game에 적용되는 교훈(scope==game 또는 'all')과 예시(같은 game 우선 + 타 game 1개)를 반환."""
    lessons = [l for l in _load(LESSONS) if l.get("scope") in (game, "all")]
    ex_all = _load(EXEMPLARS)
    same = [e for e in ex_all if e.get("game") == game]
    other = [e for e in ex_all if e.get("game") != game][:1]
    return lessons, same + other


def format_for_prompt(lessons, exemplars):
    lines = []
    if lessons:
        lines.append("MUST NOT (과거 검토에서 잡힌 것 — 어기면 자동 반려):")
        for l in lessons:
            lines.append(f"- {l['rule']}")
    if exemplars:
        lines.append("\nCLEAN EXAMPLES (이렇게 최소·누적으로):")
        for e in exemplars:
            lines.append(f"- [{e.get('game')}/{e.get('mechanic')}] {e['pattern']}")
    return "\n".join(lines)


def add_lesson(rule, why, scope="all", source="manual", lesson_id=None):
    """검토에서 새 교훈을 발견하면 추가(append)한다. 사람 검토 → 코드화의 입구."""
    existing = _load(LESSONS)
    if lesson_id is None:
        lesson_id = f"L-{len(existing) + 1:03d}"
    entry = {"id": lesson_id, "scope": scope, "rule": rule, "why": why, "source": source}
    DIR.mkdir(parents=True, exist_ok=True)
    with LESSONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    ls, ex = retrieve("sokoban")
    print(f"교훈 {len(ls)} · 예시 {len(ex)}")
    print(format_for_prompt(ls, ex))
