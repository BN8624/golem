# 로켓 카드의 BEAT 이벤트에 서사 텍스트(B겹)를 입히는 StoryForge — 바이블 생성 + 비트 대사 + 구조 검증
"""StoryForge (트랙 C 2단계, GolemStudioMode §21.3).

B겹 = 텍스트 내용(저작 데이터). 이벤트 키(BEAT-N)별 별도 파일에 대사를 쓴다.
검증은 구조만(모든 이벤트 id에 텍스트 있나) — 문장의 질은 안 잰다(저작 영역=사람 몫).
바이블 = 모든 B겹 생성이 공유하는 고정 컨텍스트(세계·인물·아크·비트 목록). 비트 목록 =
엔진 마일스톤(이벤트 키)과 공유하는 계약. 규율: 텍스트는 출력 전용, 절대 상태로 안 돌아간다.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))

from planning import _extract_json  # noqa: E402

MODEL_31 = "gemma-4-31b-it"

_BIBLE_PROMPT = """You are the story lead (StoryForge) for a deterministic idle game. Given the game CONCEPT
and the FIXED list of story beats (each tied to an engine milestone — you MUST NOT add, remove, rename, or
reorder beats), author a consistent story bible: world, main characters, an overall arc, and a one-line
synopsis per beat. Be evocative but concise. Write all prose in Korean.

CONCEPT:
{concept}

FIXED BEATS (id -> milestone, in order):
{beats}

Output ONE JSON object EXACTLY, no prose, no markdown fences:
{{
  "premise": "<2-3 sentence premise>",
  "world": "<world / setting>",
  "characters": [{{"name": "<name>", "role": "<role>"}}],
  "arc": "<overall arc in 1-2 sentences>",
  "beats": [{{"id": "BEAT-1", "milestone": "<milestone>", "synopsis": "<one-line synopsis>"}}]
}}
Every beat id from FIXED BEATS must appear exactly once, in order."""

_BEATS_PROMPT = """You are writing the in-game narrative text (B-layer) for a deterministic idle game.
Use the STORY BIBLE below as the single fixed canon — stay consistent with its world, characters, and arc.
For EACH beat id, write a short narrative/dialogue snippet (2-4 sentences, Korean) shown when that beat fires
in play. Do not invent new beats; cover exactly the beat ids given, no more, no less.

STORY BIBLE:
{bible}

BEAT IDS TO WRITE (in order): {beat_ids}

Output ONE JSON object EXACTLY, no prose, no markdown fences. Keys are the beat ids:
{{ {template} }}"""


def extract_beats(concept_text):
    """concept.md의 단계 시퀀스에서 비트 목록 추출 — '... 발사대(시작) → 대기권 → 궤도 → 달 → 화성'.
    시작 단계(첫 조각)는 제외, 나머지가 stage 1..N 마일스톤 = BEAT-1..N."""
    for line in concept_text.splitlines():
        if "→" in line:
            parts = [re.sub(r"\(.*?\)", "", p).strip().rstrip(" .,") for p in line.split("→")]
            stages = [p for p in parts if p][1:]
            return [{"id": f"BEAT-{i + 1}", "milestone": m} for i, m in enumerate(stages)]
    return []


def make_bible(pool, concept, beats):
    from llm import LLMClient
    beat_lines = "\n".join(f"- {b['id']} -> {b['milestone']}" for b in beats)
    prompt = _BIBLE_PROMPT.format(concept=concept, beats=beat_lines)
    with pool.checkout() as key:
        return _extract_json(LLMClient(api_key=key).generate("generator", prompt))


def make_beat_texts(pool, bible, beats):
    from llm import LLMClient
    ids = [b["id"] for b in beats]
    template = ", ".join(f'"{i}": "<text>"' for i in ids)
    prompt = _BEATS_PROMPT.format(
        bible=json.dumps(bible, ensure_ascii=False, indent=2),
        beat_ids=", ".join(ids), template=template)
    with pool.checkout() as key:
        return _extract_json(LLMClient(api_key=key).generate("generator", prompt))


def verify(engine_beats, bible, beat_texts):
    """구조 검증(키0) — 엔진 비트 키 = 바이블 = 대사, 모든 비트에 비어있지 않은 텍스트."""
    engine_ids = {b["id"] for b in engine_beats}
    bible_ids = {b.get("id") for b in (bible.get("beats") or [])}
    text_ids = set((beat_texts or {}).keys())
    checks = {
        "bible_covers_engine": engine_ids == bible_ids,
        "text_covers_engine": engine_ids == text_ids,
        "all_text_nonempty": all(
            isinstance((beat_texts or {}).get(i), str) and (beat_texts or {}).get(i, "").strip()
            for i in engine_ids),
    }
    return checks, all(checks.values())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", default="planning_packet_rocket")
    ap.add_argument("--out", default="storyforge_packet_rocket")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    concept = (HERE / args.packet / "concept.md").read_text(encoding="utf-8")
    beats = extract_beats(concept)
    if not beats:
        print("[STORYFORGE] 비트 추출 실패 — concept.md에 '→' 단계 시퀀스가 없음")
        return 1
    print(f"[STORYFORGE] 비트 {len(beats)}개 추출: "
          f"{[b['id'] + '=' + b['milestone'] for b in beats]}  | 모델 {MODEL_31}\n")

    from config import get_api_keys
    from llm import KeyPool
    pool = KeyPool(get_api_keys(), models=[MODEL_31])

    print("[1/2] 바이블 생성 중...")
    bible = make_bible(pool, concept, beats)
    print("[2/2] 비트 대사 생성 중...")
    beat_texts = make_beat_texts(pool, bible, beats)

    checks, ok = verify(beats, bible or {}, beat_texts or {})

    out = HERE / args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "bible.json").write_text(json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "beats.json").write_text(json.dumps(beat_texts, ensure_ascii=False, indent=2), encoding="utf-8")
    status = "COMPLETE" if ok else "OPEN"
    lines = [f"# STORY_STATUS: {status}", "",
             f"- 비트 {len(beats)}개: {', '.join(b['id'] for b in beats)}",
             "- 구조 검증:"]
    lines += [f"  - {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    (out / "STORY_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"[STORYFORGE 검증] {checks}")
    for b in beats:
        txt = (beat_texts or {}).get(b["id"], "")
        head = (txt[:50] + "…") if len(txt) > 50 else txt
        print(f"  {b['id']} ({b['milestone']}): {head}")
    print(f"[STORYFORGE] STORY_STATUS={status} → {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
