# golem

무료 gemma-4-31B(31solo) × 오케스트레이션으로 멀티파일 프로토타입을 자동 생성하는 시스템.
원래 `arag` 저장소의 서브프로젝트였고, 2026-06-17 독립 프로젝트로 승격했다.

작업 규칙·현재 상태·결정 로그는 `golem/` 안의 문서를 본다 — 새 세션은 **`golem/HANDOFF.md`** 부터.

## 저장소 구조

```
golem/                         ← 이 저장소 루트
├─ config.py                   ┐
├─ llm.py                      │ arag에서 복사한 공유 인프라 (아래 "정본" 주의)
├─ observability.py            │
├─ run_index.py                ┘
├─ requirements.txt
├─ .env                        (gitignore — 직접 만들고 키를 넣는다)
└─ golem/                      ← 본체 (둥지 구조: "루트=golem의 부모" 가정 유지용)
   ├─ CLAUDE.md HANDOFF.md context-notes.md GolemStudioMode.md
   ├─ studio/                  ← Golem Studio 파이프라인 (planning→design→specqa→build→...)
   └─ game_bank.py game_bank.sqlite ...
```

> **둥지 구조(`golem/golem/`)인 이유**: 코드가 "저장소 루트 = `golem/` 폴더의 부모"라고
> 가정해 config 등을 찾는다(`studio`는 `__file__`의 `.parent.parent`). 이 관계를 유지하면
> 이전 시 코드를 0줄 고쳐도 된다. 평탄화하면 여러 스크립트의 `sys.path`를 손봐야 한다.

## 셋업

```bash
pip install -r requirements.txt        # google-genai, pytest
# .env 생성: 저장소 루트(config.py 옆)에 둔다. config.py가 __file__ 옆에서 .env를 찾는다.
#   GOOGLE_API_KEY_1=...
#   GOOGLE_API_KEY_2=...   (키마다 한 줄, 워커=키 병렬)
```

키 없이 도는 회귀 검증(replay):

```bash
cd golem/studio
python replay.py                                          # v0.1 Contract Microkernel
python reconcile.py --replay fixtures/reconcile_demo/fixture.json
```

실제 생성(★키 사용):

```bash
python golem/studio/build_graded.py --packet ... --design ... --specqa ... --reconcile --cap 11
```

## 주의

- **정본**: `config.py`·`llm.py`·`observability.py`·`run_index.py`는 arag에서 복사한 사본이다.
  이 저장소가 독립한 뒤로는 **여기가 정본**이고 arag 원본과 따로 진화한다. arag로 역포팅하지 않는다.
- **키 쿼터**: `.env`의 키가 arag와 같으면 Google AI Studio 쿼터(RPD 1,500/키/모델)를 arag와 **공유**한다.
  완전 분리하려면 별도 키를 발급해 이 저장소 `.env`에만 넣는다.
- 무료 티어는 입력이 모델 개선에 쓰일 수 있다 — 민감한 아이디어 입력 금지.
