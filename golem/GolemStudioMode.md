# Golem Studio Mode 제안서

> **레이아웃 주의 (2026-06-21 재설계)**: 이 문서 본문의 `golem/studio/...` 경로는 역사적 표기다. 코드는 `golem/{core,tools,tactics,validators}/`로 재편됐고 데이터는 `tactics/{bases,packets,play}`·`validators/{fixtures,schemas}`에 있다. 현재 경로 정본은 루트 `README.md`와 `golem/paths.py`를 본다. 검증 명령 = `python golem/validators/verify_tactics.py`.

## 11개 Gemma Worker Slot 기반 역할 순환형 가상 게임회사 구조

## 0. 배경

현재 `arag/golem` 서브프로젝트는 Gemma 계열 모델을 이용해 작은 JS 게임/룰 엔진을 자동 생성하고 검증하는 실험이다.

지금까지는 모델의 안정성을 너무 낮게 보고, 산출물을 지나치게 작게 제한한 경향이 있었다. 하지만 실제 실험에서는 Gemma4가 작은 범위의 게임 규칙 엔진을 매우 쉽게 생성하는 모습을 보였다.

따라서 다음 단계는 단순히 “작은 게임을 여러 개 만들기”가 아니라, **11개의 Gemma worker slot을 역할별 샘플링 슬롯처럼 운영해서 더 큰 산출물을 만들 수 있는지 검증하는 것**이다.

핵심 아이디어는 다음과 같다.

> 11개 worker slot을 독립 인격으로 간주하지 않고, 단계마다 기획팀·설계팀·개발팀·QA팀·통합팀으로 역할과 검토 관점을 바꿔가며 사용하는 “역할 순환형 가상 게임회사” 구조를 만든다.

이 구조를 임시로 **Golem Studio Mode**라고 부른다.

---

## 1. 목표

Golem Studio Mode의 목표는 다음이다.

1. Gemma4를 단순한 소형 코드 생성기로 쓰지 않고, 단계별 팀 작업자로 활용한다.
2. 11개 Auth Key를 11개의 병렬 샘플링 슬롯으로 묶어 사용한다.
3. 같은 11개 worker slot이 기획팀, 설계팀, 개발팀, QA팀, 통합팀으로 순환한다.
4. 각 팀은 `lead slot 1 + reviewer slot 10` 구조로 움직인다.
5. 팀 간 인수인계는 대화가 아니라 **계약 패킷 문서**로만 한다.
6. Claude의 역할은 직접 코딩이 아니라 총괄 감리, 계약 검토, 최종 승인으로 줄인다.
7. 최종적으로 Claude Code의 토큰 부담을 줄이고, Gemma 11개 슬롯을 하위 실무 샘플러처럼 활용한다.

---

## 1.5 북극성 — 다작·선별 퍼널 (제품 전략, 2026-06-19 확정)

측정 프로그램(G33~G74)은 닫혔다. 이후 골렘의 **방향(목표)**은 단발 게임 제작이 아니라 아래 퍼널이다.

> **인간 창의력은 유한하다.** 그래서 실현 가능한 아이디어를 무한히 짜내는 게 아니라,
> **아뜰리에가 소설을 다작하고 → 골렘이 그 시나리오로 게임을 다작하고 → 사람이 될 만한 것을 골라 더 판다.**
> "한 발의 비용을 낮추고 여러 발 쏴, 맞은 것에 집중한다"(포트폴리오/shots-on-goal).

**핵심 통찰 — 병목은 "생성"이 아니라 "선별 + 품질"로 이동한다.** "더 많이 만들자"로 최적화하면
검증된 쓰레기 더미만 빠르게 쌓여 사람이 익사한다. 그래서 골렘이 가야 할 파이프라인은:

```
생성 → [싼 사전필터] → 사람 판단 → [실노출 신호] → 더블다운
        └ 대괄호 두 개가 골렘이 지어야 할 미완성 조각 ─┘
```

- **골렘이 이 전략의 받침**: "게임이 안 깨졌나(구조 건전성)"를 골든·속성검사로 **공짜로 거른다.**
  그래서 사람의 판단력을 "맞나/돌아가나"가 아니라 **"재미있나/될 만한가"에만** 쓰게 해준다.
- **지어야 할 미완성 조각 ①  싼 사전필터**: 자동 신호 + 모델-비평가(불완전한 취향 대리, 명시적으로 인정)로
  "될 것 같은 top N"만 사람에게 올린다. 사람은 생존자만 본다. (단 구조지표≠품질임을 잊지 않는다.)
- **지어야 할 미완성 조각 ②  실노출 신호**: 살아남은 후보를 작게라도 실제로 내보내 반응을 측정한다
  (가장 진짜인 신호). 그 뒤 더블다운.

**네 가지 실제 제약(우선순위순, 이걸로 의사결정한다)**:
1. **선별 처리량** — 전체 throughput은 "기계가 얼마나 빨리 만드나"가 아니라 "사람이 얼마나 빨리 거르나"에
   묶인다. 과생성은 분류 못 한 적체일 뿐. → 사람 판단을 싸게 만드는 데 투자한다.
2. **생성 품질 바닥** — 골렘은 구조 건전성만 보장하고 재미는 보장 못 한다. 후보 평균 품질이 낮으면 사금 찾기가
   더 어려워진다. → 양보다 "후보가 평균적으로 쓸 만한가"(아뜰리에 산문·골렘 각색 품질).
3. **싼 사전필터 신호** — 위 조각 ①. 지금 가장 빠진 부분.
4. **씨앗 다양성** — 기계는 증폭만 한다. 씨앗(인간 창의력)이 적/비슷하면 산출도 상관관계가 높다("무궁무진"이
   "비슷한 거 여러 개"가 됨). 다양성은 씨앗 단계에서 챙긴다.

**경계(불변)**: 구조 건전성은 골렘이 자동 검증한다. **품질·재미·각색 충실도는 정답지가 없어 사람이 최종 oracle**
이다(아뜰리에 §oracle 2층 분리와 동일 규율). 사전필터·모델비평가는 사람 판단을 **줄이는** 보조이지 **대체**가 아니다.

---

## 2. 핵심 개념

### 2.1 역할 순환형 워커풀

기존 멀티에이전트 구조는 보통 역할이 고정된다.

예:

```text
기획자 1명
설계자 1명
개발자 5명
QA 3명
통합자 1명
```

하지만 Golem Studio Mode는 다르다.

```text
Round 1: 11개 worker slot = 기획팀
Round 2: 11개 worker slot = 설계팀
Round 3: 11개 worker slot = 개발팀
Round 4: 11개 worker slot = QA팀
Round 5: 11개 worker slot = 통합/수정팀
```

즉 11개 worker slot이 고정 인격이 아니라, 단계마다 책상을 옮기듯 다른 역할과 review_axis를 수행한다.

중요한 제한도 명시한다.

```text
11개 worker slot은 독립 인격이 아니다.
동일 프롬프트 10회 반복을 다양성으로 간주하지 않는다.
각 reviewer slot은 서로 다른 review_axis를 가져야 한다.
결과 리포트에는 duplicate_issue_rate와 unique_issue_count를 기록한다.
```

---

### 2.2 Lead 1 + Reviewer Slot 10 패턴

각 부서는 항상 같은 패턴으로 작동한다.

```text
1. lead slot 1개가 초안 작성
2. reviewer slot 10개가 서로 다른 review_axis로 독립 검토
3. lead slot은 10개의 의견을 통합
4. 통합 결과를 계약 패킷으로 고정
5. 다음 팀으로 전달
```

중요한 점은 reviewer slot들이 서로 대화하지 않는다는 것이다.
자유 토론을 시키면 비용이 커지고 산출물이 산으로 갈 수 있다.

따라서 구조는 “회의”가 아니라 **비동기 문서 리뷰**여야 한다.

예를 들어 기획 리뷰의 10개 축은 다음처럼 나눈다.

```text
Reviewer 1: 규칙 모호성만 찾기
Reviewer 2: 빠진 실패 케이스 찾기
Reviewer 3: 상태 객체에 반영 안 된 규칙 찾기
Reviewer 4: 테스트하기 어려운 규칙 찾기
Reviewer 5: 너무 복잡한 기능 찾기
Reviewer 6: 중복 규칙 찾기
Reviewer 7: 용어 충돌 찾기
Reviewer 8: 구현 난이도 위험 찾기
Reviewer 9: 범위 초과 기능 찾기
Reviewer 10: 다음 단계 인수인계 위험 찾기
```

---

## 3. 가장 중요한 원칙: 계약 모호성 제거

이 구조에서 제일 중요한 문제는 모델 체급이 아니라 **팀 간 계약의 모호성**이다.

기획팀이 만든 문서를 설계팀이 다르게 해석하고, 설계팀이 만든 manifest를 개발팀이 다르게 해석하면 실패한다.

따라서 팀에서 팀으로 넘어가기 전에 반드시 **Ambiguity Review**, 즉 모호성 사냥 단계를 넣어야 한다.

---

## 4. 계약 패킷 구조

팀 간 인수인계는 단일 `기획안.md`가 아니라, 다음과 같은 계약 패킷으로 해야 한다.

```text
HANDOFF_PACKET/
├─ 01_goal.md              # 이번 단계의 목표
├─ 02_decisions.md         # 이미 확정된 결정
├─ 03_terms.md             # 용어 정의
├─ 04_scope.md             # 포함/제외 범위
├─ 05_contract.json        # 다음 팀이 반드시 지켜야 할 기계적 계약
├─ 06_examples.md          # 맞는 예시 / 틀린 예시
├─ 07_acceptance_tests.md  # 통과 기준
└─ 08_questions.md         # BLOCKING / ASSUMED / DEFERRED 질문 분류
```

이 구조를 **Golem Contract Relay**라고 부른다.

핵심은 다음이다.

> 각 팀은 이전 팀의 최종 계약 패킷만 읽고 작업한다.
> 이전 논의 과정 전체를 읽지 않는다.
> 말이 아니라 파일이 기억 역할을 한다.

---

## 5. 팀 간 계약의 5종류

### 5.1 목표 계약

무엇을 만들지, 무엇을 만들지 않을지를 명확히 한다.

예:

```text
목표:
- 텍스트 기반 로그 출력 게임
- 타일 이동
- 적 전투
- 아이템 획득
- 환경 상호작용

비목표:
- 그래픽 렌더링 없음
- 실시간 입력 없음
- 랜덤 맵 생성 없음
- 외부 패키지 없음
- 네트워크 없음
```

작은 모델에게는 “해야 할 것”보다 “하지 말아야 할 것”이 매우 중요하다.

---

### 5.2 용어 계약

같은 단어를 모든 팀이 같은 의미로 쓰도록 한다.

예:

```text
turn: 플레이어 명령 1개가 처리된 횟수
tick: 현재 사용하지 않음
enemy: hp, x, y, type을 가진 객체
blocked tile: player와 enemy가 이동할 수 없는 타일
hazard tile: 이동은 가능하지만 효과가 발생하는 타일
```

---

### 5.3 데이터 계약

게임 상태 객체의 구조를 고정한다.

예:

```json
{
  "turn": 0,
  "player": {
    "x": 1,
    "y": 1,
    "hp": 5,
    "inventory": []
  },
  "enemies": [
    {
      "id": "e1",
      "type": "slime",
      "x": 3,
      "y": 1,
      "hp": 2
    }
  ],
  "tiles": [
    {
      "x": 2,
      "y": 2,
      "type": "fire"
    }
  ],
  "log": []
}
```

개발팀은 이 구조를 임의로 바꾸면 안 된다.
계약 의미 변경이 필요하면 `CHANGE_REQUEST.md`를 만들어야 한다.

---

### 5.4 인터페이스 계약

각 모듈의 파일명, export, import를 고정한다.

예:

```json
{
  "files": {
    "state.js": {
      "exports": ["createInitialState", "cloneState"]
    },
    "movement.js": {
      "exports": ["applyMove"],
      "imports": ["state.js"]
    },
    "combat.js": {
      "exports": ["applyAttack"],
      "imports": ["state.js"]
    },
    "engine.js": {
      "exports": ["runCommand", "runScenario"],
      "imports": ["movement.js", "combat.js"]
    }
  }
}
```

이렇게 해야 개발팀이 `movePlayer`, `doMove`, `handleMovement`처럼 제각각 함수명을 만들지 않는다.

---

### 5.5 테스트 계약

규칙은 반드시 예상 결과와 함께 있어야 한다.

예:

```text
Scenario: wall_block

초기 상태:
- player at (1,1)
- wall at (2,1)

입력:
- MOVE_EAST

기대 결과:
- player remains at (1,1)
- turn increases by 1
- log contains "BLOCKED"
```

말로 된 규칙만 있으면 안 된다.
반드시 테스트 가능한 형태여야 한다.

---

## 6. Ambiguity Review

다음 팀으로 넘기기 전에 reviewer slot 10개는 구현이나 아이디어 추가를 하지 않는다.
오직 모호한 부분만 찾는다.

출력 형식은 JSON으로 제한한다.

```json
{
  "ambiguous_terms": [],
  "missing_rules": [],
  "conflicting_rules": [],
  "underspecified_outputs": [],
  "risky_assumptions": [],
  "questions_for_lead": []
}
```

lead slot은 이 10개의 리뷰를 받아 계약 패킷을 수정한다.

### 6.1 반복 모호성 종류 사전 (실측 G60~64, 2026-06-18)

frontier 측정에서 자율 oracle/빌드가 갈린 실패는 *항상* 미명세 계약이었고, 그 종류가 반복된다. 모호성은
무한이 아니라 유한한 어휘(아래 6종)에서 나온다 — reviewer slot은 FROZEN 전에 계약을 이 목록으로 점검하고,
새로 박은 핀은 영구 규약이 된다(반응적 땜질 → 사전 차단). 새 종류가 나오면 여기 추가한다.

| 종류 | 어떻게 터지나(실측) | 박는 법(핀) |
|---|---|---|
| **enum 리터럴 어휘** | gameStatus/status를 모델이 `success`·`ok`·`completed`로 지어냄 (G60·62·64) | 허용 토큰을 리터럴로 못박음 — "정확히 'PLAYING' 또는 'WON'" |
| **빈/디폴트 컬렉션 구조** | `levels`가 빈 `{}`냐 모든 id를 0으로 채우냐 (G60·61) | 초기 구조 명시 — "모든 constants id를 0으로, 0레벨도 포함" |
| **경계/클램프** | 좌표가 월드 밖으로(음수/초과) — 허용? 고정? (G64) | 범위 거동 명시 — "[0, worldSize-1]로 클램프" |
| **순서·타이밍·동률** | 번식 자격 평가 시점, PHASE 적용 순서, 동률 처리 (G62·63·64) | 평가 시점 + 처리 순서 명시 — "tick 시작 energy로 자격 / sorted by ID" |
| **카운터 증가 의미** | 어떤 액션이 카운터를 올리나 — `turn`을 ADVANCE도 올리나 (로켓) | 각 카운터의 증가 조건 명시 — "turn은 WAIT 횟수, 다른 액션은 안 올림" |
| **빈 입력·미지 참조** | 빈 입력/0틱, 미지 id 참조 시 크래시 (G37·38) | 디폴트·무시 규칙 명시 — "actions 없으면 [], 미지 id는 무상태변경+로그" |

핀은 골든을 안 바꾸는 1변수 수정이면 L0~L1, 의미를 바꾸면 L3다. self-suggest(§21.6 도구 `self_suggest.py`)가
이 점검을 빌드 *전에* 자동 생성하는 방향이다. underspecified_outputs↔enum/컬렉션/카운터,
ambiguous_terms↔순서/타이밍, missing_rules↔경계/빈입력으로 매핑된다.

질문은 0개가 아니어도 된다.
대신 모든 질문은 다음 세 종류로 분류되어야 한다.

```text
BLOCKING: 다음 단계로 넘어가면 안 되는 질문
ASSUMED: 명시적 가정으로 고정하고 진행하는 질문
DEFERRED: 후속 버전으로 미루는 질문
```

완료 조건은 다음이다.

```text
BLOCKING questions = 0
ASSUMED questions는 assumptions.md에 기록
DEFERRED questions는 backlog.md에 기록
```

수정 후 반드시 다음 상태를 선언한다.

```text
CONTRACT_STATUS: FROZEN
```

계약이 FROZEN된 뒤에는 다음 팀이 임의로 계약을 바꿀 수 없다.
다만 변경은 다음 등급으로 나누어 처리한다.

```text
L0: 문서/포맷 수정
- 오타, 설명 보강, 파일 정리
- 승인 없이 가능

L1: 명명/경로 수정
- 함수명, 파일명, export 이름 정정
- validator 통과 조건이면 가능

L2: 테스트 보강
- 기존 계약 의미를 바꾸지 않는 테스트 추가
- QA 단계에서 가능

L3: 계약 의미 변경
- 규칙, 상태 구조, 모듈 책임 변경
- CHANGE_REQUEST.md 필요

L4: 범위 변경
- 기능 추가/삭제, 게임 목표 변경
- lead slot 또는 Claude 감리 승인 필요
```

---

## 7. Traceability JSON

기획 요구사항이 설계, 코드, 테스트와 어떻게 연결되는지 추적해야 한다.
정본은 Markdown이 아니라 JSON이어야 한다.

예:

```json
{
  "REQ-001": {
    "text": "플레이어는 북/남/동/서 이동 가능",
    "design_modules": ["movement.js"],
    "exports": ["applyMove"],
    "tests": ["SCN-001", "SCN-002"],
    "status": "covered"
  },
  "REQ-002": {
    "text": "벽으로 이동하면 위치는 변하지 않는다",
    "design_modules": ["movement.js"],
    "exports": ["applyMove"],
    "tests": ["SCN-003"],
    "status": "covered"
  }
}
```

validator는 다음을 확인해야 한다.

```text
- 모든 REQ가 최소 1개 module에 연결됨
- 모든 REQ가 최소 1개 test에 연결됨
- manifest에 없는 파일이 trace에 나오면 실패
- 존재하지 않는 test id가 trace에 나오면 실패
```

사람이 읽는 `traceability_report.md`는 JSON에서 생성되는 보조 문서로 둔다.

---

## 8. Definition of Done

각 팀은 완료 기준을 가져야 한다.

### 8.1 기획팀 완료 기준

```text
- 핵심 루프가 명확함
- 플레이어 행동 목록이 있음
- 적/아이템/타일/승패 조건이 정의됨
- 비목표가 명확함
- 모호성 리뷰 완료
- BLOCKING questions가 0개
- ASSUMED questions가 assumptions.md에 기록됨
- DEFERRED questions가 backlog.md에 기록됨
```

### 8.2 설계팀 완료 기준

```text
- 모든 REQ가 하나 이상의 모듈에 배정됨
- 모든 모듈이 파일명과 exports를 가짐
- 순환 의존성 없음
- 테스트되지 않는 REQ 없음
- module_manifest.json 존재
- traceability.json 존재
- traceability_report.md는 traceability.json에서 생성됨
- BLOCKING questions가 0개
```

### 8.3 개발팀 완료 기준

```text
- 모든 manifest 파일 존재
- 모든 export 이름 일치
- node --check 통과
- static_gate 통과
- 외부 패키지 없음
- Math.random 없음
- acceptance_tests 통과
```

### 8.4 Spec QA 완료 기준

```text
- 기획/설계 문서가 테스트 가능한 표현을 가짐
- acceptance_tests 초안 존재
- expected output이 모호한 시나리오가 표시됨
- 각 REQ에 최소 1개 테스트 후보 연결
- TEST_ORACLE_ERROR 위험이 분리됨
```

### 8.5 Adversarial QA 완료 기준

```text
- 정상 시나리오 존재
- 실패 시나리오 존재
- 경계 조건 시나리오 존재
- 각 REQ에 최소 1개 테스트 연결
- golden output이 명확함
- 구현을 깨는 edge_cases.json 존재
```

---

## 9. 산출물 크기를 키우는 방법

Gemma4에게 단순히 “크게 만들어라”라고 하면 안 된다.
대신 각 단계마다 최소 산출물 예산을 줘야 한다.

### 9.1 기획팀 산출물 깊이 조건

```text
- 핵심 루프 1개
- 각 플레이어 행동은 입력, 상태 변화, 실패 케이스, 로그 출력, 테스트 후보를 가짐
- 각 적 타입은 이동 규칙, 공격 규칙, HP/피해량, 지형 상호작용, 사망 시 효과 중 최소 2개 이상에서 차이를 가짐
- 각 아이템은 획득 조건, 상태 변화, 실패 케이스, 로그 출력, 최소 1개 테스트 시나리오를 가짐
- 각 타일은 진입 가능 여부, 효과 발동 시점, 로그 출력, 최소 1개 테스트 시나리오를 가짐
- 실패/예외 상황은 관련 REQ와 연결됨
```

### 9.2 설계팀 산출물 깊이 조건

```text
- 각 모듈은 책임, 입력, 출력, 금지 책임을 가짐
- 각 export 함수는 호출자, 입력 schema, 반환 schema, 실패 케이스를 가짐
- 상태 객체 schema 정의
- 이벤트 타입은 발생 조건과 소비 모듈을 가짐
- 금지된 의존성 명시
- 각 모듈별 테스트 포인트가 REQ와 연결됨
```

### 9.3 개발팀 산출물 깊이 조건

```text
- main.js 포함
- manifest에 정의된 src 모듈 포함
- 테스트 가능한 순수 함수 중심
- 외부 패키지 금지
- Math.random 금지
- 모든 명령은 deterministic
- 각 export는 manifest의 이름과 일치
```

산출물을 키우는 방식은 “프롬프트에 크게 만들라고 쓰기”가 아니라 **최소 산출물 계약을 명시하는 것**이다.

---

## 10. 확장 래칫

한 번 통과한 기능은 기본적으로 다음 버전에서 유지한다.
이를 **확장 래칫**으로 관리한다.

예:

```text
Golem Studio v0
- 이동
- 벽
- 로그
- 5개 시나리오

Golem Studio v1
- 적
- 공격
- HP
- 10개 시나리오

Golem Studio v2
- 아이템
- 인벤토리
- 효과
- 15개 시나리오

Golem Studio v3
- 환경 타일
- 상태 이상
- 연쇄 효과
- 20개 시나리오

Golem Studio v4
- 퀘스트
- 승패 조건
- 스코어
- 30개 시나리오
```

v2에서 아이템이 들어갔다면 v3에서 아이템이 사라지면 안 된다.
다만 잘못 만든 기능까지 무조건 끌고 가면 안 된다.
아래 조건 중 하나에 해당하면 제거나 축소가 가능하다.

```text
1. 해당 기능이 2회 이상 연속으로 통합 실패를 유발
2. 테스트 대비 구현 복잡도가 과도함
3. 다른 핵심 기능과 계약 충돌 발생
4. 현재 목표 버전의 scope를 벗어남
5. QA가 유지 비용이 크다고 판정
```

제거 시 `DEPRECATION_REQUEST.md`를 작성한다.
래칫은 무조건 쌓기가 아니라, 성공한 기능은 유지하되 실패한 기능은 근거를 남기고 제거할 수 있는 구조다.

---

## 11. 제안하는 Golem Studio Mode 파이프라인

```text
Stage 1: Planning
- concept.md
- gdd.md
- ambiguity_review.json

Stage 2: Design
- system_design.md
- module_manifest.json
- traceability.json

Stage 3: Spec QA
- acceptance_tests_draft.json
- oracle_risk_review.json

Stage 4: Build
- src/*.js
- implementation_notes.md

Stage 5: Adversarial QA
- acceptance_tests.json
- edge_cases.json

Stage 6: Integration
- final workspace
- static_gate_result.json
- grade_result.json
- final_report.md
```

처음부터 전부 구현하지 말고, 1차 구현은 다음만 해도 된다.

```text
Planning → Design → Spec QA → Build → Adversarial QA → Integration
```

---

## 12. 추천 폴더 구조

```text
golem/
  studio/
    roles/
      executive.md
      planning_lead.md
      planning_reviewer.md
      design_lead.md
      design_reviewer.md
      dev_lead.md
      dev_reviewer.md
      qa_lead.md
      qa_reviewer.md
      integration_lead.md

    stages/
      01_planning.yaml
      02_design.yaml
      03_spec_qa.yaml
      04_build.yaml
      05_adversarial_qa.yaml
      06_integration.yaml

    schemas/
      contract_packet.schema.json
      module_manifest.schema.json
      ambiguity_review.schema.json
      traceability.schema.json
      acceptance_tests.schema.json

    artifacts/
      concept.md
      gdd.md
      system_design.md
      module_manifest.json
      traceability.json
      traceability_report.md
      acceptance_tests_draft.json
      acceptance_tests.json
      final_report.md

    runs/
      <timestamp>/
        planning/
        design/
        spec_qa/
        build/
        adversarial_qa/
        integration/
        report.md
```

---

## 13. 구현 우선순위

바로 LLM 병렬 실행부터 만들면 안 된다.
먼저 계약 패킷과 검증기를 만들어야 한다.

### Step 1: Contract Microkernel Replay

실제 API 호출 없이 fake output으로만 검증한다.
이 단계는 Golem Studio 전체가 아니라 계약 검증 마이크로커널만 만든다.

작업:

```text
1. fake_planning_packet.json 작성
2. module_manifest.schema.json 작성
3. fake src/*.js build output 추가
4. import/export validator 작성
5. static_gate bridge 연결
6. replay_result.json 생성
7. contract_validation_report.md 생성
```

이 단계에서는 Gemini/Gemma API 호출 금지.
목표는 게임 생성이 아니라 manifest에 적힌 파일, export, import와 실제 코드가 일치하는지 기계적으로 검증하는 것이다.

---

### Step 2: Planning 팀만 Gemma로 실행

처음에는 기획팀만 실제 worker slot을 사용한다.

```text
- planning_lead 1회
- planning_reviewer 3회 또는 10회
- 선택한 reviewer 수만큼 ambiguity review 생성
- planning_lead synthesis 1회
- contract_packet 생성
```

성공 기준:

```text
- BLOCKING questions가 0개
- concept.md 생성
- gdd.md 생성
- ambiguity_review.json 생성
- contract_packet 검증 통과
```

---

### Step 3: Design 팀 실행

Planning 산출물을 입력으로 받아 설계팀을 실행한다.

성공 기준:

```text
- module_manifest.json 생성
- traceability.json 생성
- traceability_report.md 생성
- 모든 REQ가 모듈에 연결됨
- 모든 REQ가 테스트 후보에 연결됨
- 순환 의존성 없음
- BLOCKING questions가 0개
```

---

### Step 4: Spec QA 팀 실행

Design 산출물을 입력으로 받아 테스트 가능한 계약인지 먼저 검토한다.

성공 기준:

```text
- acceptance_tests_draft.json 생성
- oracle_risk_review.json 생성
- 모든 REQ가 최소 1개 테스트 후보에 연결됨
- expected output이 모호한 시나리오가 표시됨
- BLOCKING questions가 0개
```

---

### Step 5: Build 팀 실행

Design 산출물을 입력으로 받아 모듈별 구현을 수행한다.

성공 기준:

```text
- manifest에 정의된 모든 파일 존재
- export/import 일치
- node --check 통과
- static_gate 통과
- grade 통과
```

---

### Step 6: Adversarial QA 팀 실행

Adversarial QA팀은 구현을 새로 하지 않는다.
오직 깨질 만한 케이스를 만든다.

성공 기준:

```text
- acceptance_tests.json 생성
- edge_cases.json 생성
- 각 REQ별 최소 1개 테스트 존재
- 실패 케이스가 명확한 expected output을 가짐
```

---

## 14. Claude의 역할

초기에는 Claude가 lead slot 역할을 일부 맡아도 된다.

하지만 최종 목표는 다음이다.

```text
Gemma key 1 = lead slot
Gemma key 2~11 = reviewer slot
Claude = 총괄 감리 / 최종 승인 / 실패 원인 판단
```

Claude가 직접 코드를 많이 쓰면 이 구조의 의미가 줄어든다.
Claude는 가능한 한 다음에 집중해야 한다.

```text
- 계약 패킷이 모호하지 않은지 검토
- 게이트 실패 원인 판단
- 잘못된 단계로 롤백
- 다음 실험 방향 결정
- 위험한 구조 변경 차단
```

---

## 15. 측정 지표

기존의 `11/11 통과`만으로는 부족하다.

Golem Studio Mode에서는 다음을 기록해야 한다.

```text
- stage별 성공률
- ambiguity 개수
- BLOCKING / ASSUMED / DEFERRED questions 개수
- contract freeze까지 걸린 호출 수
- manifest 검증 실패 수
- import/export mismatch 수
- static_gate 실패 원인
- grade 실패 원인
- Claude가 직접 수정한 코드 줄 수
- Claude 토큰 사용량
- Gemma 토큰 사용량
- 최종 산출물 파일 수
- 최종 테스트 수
- 이전 버전 대비 기능 증가량
- duplicate_issue_rate
- unique_issue_count
- accepted_review_count
- contract_validation_failure_count
- build_failure_count
- final_pass_rate
- latency
```

핵심 지표는 단순히 Gemma 통과율이 아니라:

```text
Claude touch 감소량
계약 모호성 감소량
산출물 복잡도 증가량
```

이다.

11개 슬롯 효과는 반드시 비교군으로 측정한다.

```text
A안: single Gemma
- planning → design → build를 단일 Gemma가 수행

B안: 1 lead + 3 reviewers
- lead 초안
- reviewer 3개 축
- lead synthesis

C안: 1 lead + 10 reviewers
- lead 초안
- reviewer 10개 축
- lead synthesis
```

C안이 B안보다 unique issue를 충분히 늘리지 못하면 10 reviewers를 기본값으로 쓰지 않는다.
기본값은 3 reviewers로 두고, 위험 단계나 실패 반복 단계에서만 10 reviewers로 승격한다.

---

## 16. 실패 분류와 롤백 기준

실패했을 때 Claude가 감으로 판단하면 다시 Claude touch가 늘어난다.
따라서 실패는 다음처럼 분류하고 롤백 위치를 정한다.

```text
SPEC_AMBIGUITY
- 요구사항이 서로 다르게 해석 가능
- Planning 또는 Design으로 롤백

MANIFEST_MISMATCH
- 파일명/export/import 불일치
- Design으로 롤백

IMPLEMENTATION_BUG
- 계약은 맞는데 코드 동작이 틀림
- Build로 롤백

TEST_ORACLE_ERROR
- 테스트 기대값이 계약과 다름
- Spec QA로 롤백

INTEGRATION_ERROR
- 개별 모듈은 맞지만 조립 실패
- Integration 또는 Design으로 롤백

SCOPE_BLOAT
- 기능이 너무 많아져 핵심 목표 실패
- Planning으로 롤백하거나 DEPRECATION_REQUEST.md 생성
```

---

## 17. 주의할 실패 패턴

### 17.1 회의가 길어지는 문제

11개 slot이 서로 대화하면 비용이 폭발한다.
반드시 독립 리뷰 후 lead slot이 통합하는 구조여야 한다.

### 17.2 그럴듯한 말만 많고 결정이 없는 문제

모든 단계는 파일 산출물로 종료해야 한다.
다음 단계는 대화 로그가 아니라 최종 파일만 읽어야 한다.

### 17.3 계약 변경 남발

다음 팀이 이전 팀의 결정을 계속 바꾸면 시스템이 무너진다.
계약 의미 변경은 반드시 `CHANGE_REQUEST.md`로 처리한다.
단, L0~L2 변경은 validator와 단계 규칙 안에서 빠르게 처리한다.

### 17.4 산출물 축소

모델이 안전하게 가려고 이전보다 작은 게임을 만들 수 있다.
이를 막기 위해 확장 래칫과 산출물 깊이 조건이 필요하다.

### 17.5 테스트 없는 요구사항

모든 요구사항은 최소 하나의 테스트와 연결되어야 한다.

---

## 18. 최종 요청

Claude는 현재 `arag/golem` 구조를 확인한 뒤, 바로 대규모 구현에 들어가지 말고 다음 순서로 진행해라.

1. 기존 golem 구조를 깨지 말 것.
2. `golem/studio/` 하위에 Golem Studio Mode를 별도 실험 모드로 추가할 것.
3. 먼저 Contract Microkernel Replay부터 만들 것.
4. 실제 Gemini/Gemma API 호출은 Step 1에서 금지할 것.
5. module manifest schema, import/export validator, fake artifacts, static_gate bridge, replay report를 먼저 만들 것.
6. replay가 통과한 뒤 Planning 팀만 실제 호출하는 Step 2로 넘어갈 것.
7. 모든 단계 산출물은 파일로 저장할 것.
8. 다음 단계는 이전 단계의 최종 계약 패킷만 읽게 할 것.
9. Claude가 직접 코드를 많이 쓰는 구조가 아니라, Gemma worker slots가 역할 순환하며 산출물을 키우는 구조를 목표로 할 것.

---

## 19. Pending Decisions / Known Open Problems

다음 항목은 Golem Studio Mode의 전체 설계에서 아직 확정되지 않은 문제다.
다만 v0.1 구현이 막히지 않도록 임시 기본값을 둔다.

### PENDING-001: module_manifest.schema.json 전체 필드

v0.1에서는 최소 필드만 사용한다.

```json
{
  "schema_version": "0.1",
  "module_format": "commonjs",
  "entry": "main.js",
  "files": [
    {
      "path": "main.js",
      "exports": [],
      "imports": ["src/engine.js"]
    },
    {
      "path": "src/engine.js",
      "exports": ["runScenario"],
      "imports": ["src/state.js", "src/movement.js"]
    }
  ]
}
```

`description`, `owner`, `req_ids`, `test_ids`, `side_effects` 같은 필드는 v0.2 이후로 미룬다.

### PENDING-002: JS module format

v0.1은 CommonJS만 허용한다.

```text
- require(...) 사용
- module.exports 또는 exports.xxx 사용
- ESM import/export 금지
```

v0.1 validator는 named export만 검증한다.
허용 패턴은 `exports.name = ...` 또는 `module.exports = { name }`이다.
`module.exports = function ...` 같은 bare default export는 entry 파일처럼 `exports: []`인 파일이 아니면 금지한다.

ESM은 v1 이후 별도 실험으로 다룬다.

### PENDING-003: static_gate bridge I/O

v0.1 bridge 입력은 다음 JSON으로 고정한다.

```json
{
  "workspace_path": "golem/studio/runs/demo/workspace",
  "manifest_path": "golem/studio/runs/demo/module_manifest.json"
}
```

출력은 다음 JSON으로 고정한다.

```json
{
  "ok": true,
  "checks": [
    {
      "name": "manifest_schema",
      "ok": true
    },
    {
      "name": "file_exists",
      "ok": true
    },
    {
      "name": "import_export",
      "ok": true
    },
    {
      "name": "static_gate",
      "ok": true
    }
  ],
  "errors": [],
  "warnings": []
}
```

### PENDING-004: A/B/C 비교의 충분성 기준

v0.1에서는 임시 기준을 사용한다.

```text
- B안이 A안보다 unique_issue_count를 30% 이상 늘리지 못하면 B안은 기본값으로 채택하지 않는다.
- C안이 B안보다 unique_issue_count를 20% 이상 늘리지 못하면 10 reviewers는 기본값으로 쓰지 않는다.
- 단, C안이 B안이 못 잡은 BLOCKING 문제를 1개 이상 잡으면 예외적으로 유효하다고 본다.
- 이 기준은 10회 이상 실행 후 조정한다.
```

---

## 20. 한 줄 요약

Golem Studio Mode는 다음 구조다.

> 11개의 Gemma Auth Key를 독립 인격이 아니라 역할별 병렬 샘플링 슬롯으로 순환 배치하고, 팀 간 인수인계는 계약 패킷으로 고정하여, 작은 모델들이 모호성 없이 큰 산출물을 단계적으로 만들어가게 하는 역할 순환형 가상 게임회사 구조.

우선 구현 목표는 다음이다.

> `Contract Microkernel Replay + manifest validation + import/export validator + fake build output + static gate bridge`

이게 통과한 뒤에만 실제 worker slots를 투입한다.

## 21. 확장 방향 — 큰 게임 / 서사 레이어 / 밸런스 (2026-06-18, 대화 G 합의)

frontier(G60~64)가 "싼 모델이 결정적 게임을 빌드+자율검증한다"를 닫았다. 다음 = 작은 게임에서 멈추지 않고
**골격을 만들어 카드로 누적해 큰 게임으로** 키운다. 이 절은 그 방향의 설계 정본이다. 결정 이유는
context-notes 대화 G(서사·밸런스·스케일) 참조.

### 21.1 "큰 게임"의 정의 — 결정적 시뮬/전략
대상 = 코에이식 결정적 시뮬/전략(영걸전·삼국지4·징기스칸4·심시티·심즈2·대항해시대4). 이들의 코어는
턴/틱 단위 상태 전이라 Golem의 홈그라운드다 — **eco 카드 = 아기 심시티, combat 카드 = 아기 영걸전**.
비대상 = NPC 자유대화·탐험 서사 어드벤처(정확일치 채점 불가, Golem 검증 모델 밖). 아트·음악·UI 폼은 사람 몫.

### 21.2 누적 빌드 4레버
지금 Golem은 "동결 계약 → 매번 scratch 빌드"다(누적 아님). 골격에 붙이려면 넷이 필요하다.
> **G74 닫힘**: 넷 다 patch로 구현·★키 실증됐다(`build_graded.py --patch`·`patch_apply.py`). 레버3 누적은
> station 3장 체인(EVACUATE→PING→서사 비트, 전원 1.0)으로, 도메인 일반성은 고결합 combat(FATIGUE 1.0)으로
> 닫힘. 상세 = checklist/context-notes G74.
1. **기존 코드 주입** — 빌드 프롬프트에 현재 코드베이스를 텍스트로 먹인다(계약 주입과 같은 메커니즘).
2. **편집 모드** — "기존 파일 + 이번 카드 = 수정본/diff"를 내게 한다(G74: 통째 재출력 B + diff 패치 둘 다 구현,
   patch가 출력을 모듈 크기와도 분리해 B 상위호환).
3. **누적 회귀** — 카드 N에서 카드 1..N 시나리오 골든을 다 재실행(이전 기능 안 깨졌나).
4. **선택적 컨텍스트(+선택적 출력)** — 게임이 커지면 전체가 프롬프트에 안 들어간다. "이번 카드가 건드리는
   모듈만" 주입하고, **모델도 그 모듈만 출력**(나머지는 하네스가 verbatim 조립). Golem의 계약/모듈 분해가
   토대다. ※ 진짜 벽은 컨텍스트가 아니라 **출력 토큰**임이 G73에서 드러남 — §21.5 참조(B가 그걸 푸는 길).

오해 정정 — "gemma가 파일을 못 읽는다"는 문제가 아니다(하네스가 읽어서 텍스트로 주입). 멀티턴도 답이
아니다(Gemma API 무상태 — 매 호출 전체 재전송이라 단일 프롬프트와 본 양이 같다). 레버는 위 넷이다.

### 21.3 서사 2겹 (결정적 엔진에 이야기 붙이기)
- **A겹 — 발동 로직(결정적, golden 검증).** "상태 조건 → 이벤트 발동"(예: 마일스톤 도달 시 events에
  `BEAT-N` 추가). 계약 규칙 한 줄이라 자율 oracle이 그대로 채점한다. 서사의 뼈대.
- **B겹 — 텍스트 내용(저작 데이터, 정확일치 안 잼).** 실제 대사는 이벤트 키로 별도 파일에. 검증은 구조만
  (모든 이벤트 id에 텍스트 있나), 문장의 질은 안 잰다.
- **규율: 텍스트는 출력 전용, 절대 상태로 되돌아가지 않는다**(`상태 → 텍스트` 일방). 어기면 결정성·golden 붕괴.
- **StoryForge = 일관 바이블** — B겹의 모든 생성이 공유하는 고정 컨텍스트(세계·인물·아크·비트 목록). 독립
  생성된 텍스트 조각이 표류하지 않게 묶는 역할이다(planning 대체 아님). 바이블의 비트 목록 = 엔진 마일스톤과
  공유하는 계약(이벤트 키).
- 프로브 = 방치형 **로켓 카드**(`studio/planning_packet_rocket`). A겹=ADVANCE 시 `BEAT-N` 발동.

### 21.4 밸런스 — config와 로직 분리, 측정+탐색
- 밸런스는 **숫자(config)**에 산다. 로직(rules)과 분리돼 있어(예: 규칙은 `fuel>=stageCost[stage]`, 숫자는
  `stageCost`) **검증 안 깨고 무한 튜닝** 가능하다. 일방 규율과 동형 — 숫자가 엔진에 들어가지, 엔진 정확성이
  숫자에 의존하지 않는다.
- 두 겹. **잴 수 있는 밸런스**(페이싱·지배전략 유무·난이도 곡선·자원 성장)는 엔진을 여러 config로 돌려
  코드로 측정한다. **취향 밸런스**(어떤 곡선이 재밌나)는 사람 몫.
- 조정 루프 = 사람이 목표 곡선 정함 → 기계가 config 훑어 지표 측정 → 후보 추림 → 사람이 느낌 판정 → 반복.
  모델도 self-suggest처럼 낄 수 있다(측정값 보고 config 조정 제안). **지표=코드, 제안=모델, 취향=사람.**
- 재미 중 "의미 있는 선택(지배 전략 없음)"은 측정 가능 속성이라 밸런스에 흡수된다. 순수 사람 몫 =
  놀라움·테마 공명·취향(크리에이티브 디렉터 자리).

### 21.5 스케일 한계 — "완벽·공짜"는 없고 규율로 푼다
- **손계산 스케일** — auto_oracle는 모델이 머리로 시뮬한다. 스텝이 길면(예 150틱) 부정확(게임 결함 아님,
  oracle 한계). 해결 = ① 시나리오를 짧게(검증은 길이 아닌 커버리지) ② 본질적으로는 oracle를 "코드 작성+실행"
  으로(스텝 한계 소멸, 단 빌드와 독립성 약화 — 다른 프롬프트/레퍼런스 스타일로 완충).
- **진짜 천장은 컨텍스트가 아니라 출력 토큰이다 (G73 실측·정정)** — 처음엔 "코드가 커서 프롬프트에 안
  들어감(컨텍스트 천장)"으로 봤으나 실측은 다르다. gemma-4 31B 256k 창에 46모듈 카드 입력 ~26k = 10%로,
  컨텍스트는 한계가 아니다. **진짜 벽은 출력 32k(추론 포함)** 이고, 그 벽은 **A(매 턴 전체 재출력)에만** 걸린다.
  A는 코드가 실효 출력한도(추론 빼면 ~20–25k토큰≈70–90KB)를 넘으면 한 응답에 못 담아 — 카드를 키울수록
  A가 더 못 뱉는 자기모순. **해결 = 선택적 컨텍스트(입력)에 더해 선택적 출력(레버4 B)** — 모델은 touched
  파일만 출력하고 하네스가 held-out를 verbatim 조립(`build_graded.py:90·370-374`)하므로 **콜 출력이 게임
  크기와 분리(항상 작음)**. 큰 게임은 "전체 재생성"이 아니라 "선택적 읽기 + 패치 쓰기"로 짓는 게 필연이고,
  그게 유일하게 출력한도를 안 건드린다. **실측(G73): B는 546모듈/입력 ~24k(engine이 545 시그니처 사이에
  묻힘)에서도 정확도·충실도 1.0·held-out 드리프트 0** — B는 모듈 수에 사실상 무관. A는 행동 1.0이나
  verbatim 보존 실패(주석 패러프레이즈·기능 재배치)라 충실도까지 B가 우위. 천장은 "큰 걸 못 만든다"가 아니라
  "패치로 설계해야 만든다"로 옮겨간다.
- 끝까지 안 남는 환원 불가 = 재미(놀라움·테마)·밸런스 취향·아트. 사람 몫.

### 21.6 두 트랙
- **트랙 A(생산화)** — reconcile에 자율 oracle+self-suggest 배선(손-oracle 대체) / combat 자율 oracle(곁).
  실질 마무리는 reconcile 배선 하나. **이게 트랙 C의 토대**(카드 여러 장 쌓을 때 골든 손저작 제거).
- **트랙 C(서사)** — 로켓 A겹 검증 → B겹 대사 → StoryForge 바이블. 큰 결정적 게임으로 가는 본선.

## 22. 운영 모델·장르 (2026-06-19 확정, G81)

### 22.1 3겹 분업 — 누가 무엇을
- **골렘(gemma 31B) = 설계 + 빌드 + 검증.** **설계도 골렘이 한다** — `planning.py`(아이디어→계약)·`design.py`(모듈 분해)·build로 게임을 산출. §13 파이프라인의 본래 의미가 이것.
- **클로드 = 하네스 + 외형.** ① 골렘이 설계·생성하다 막히면 게이트·프롬프트·계약·validator를 고쳐 *되게 만든다* ② 검증된 엔진 상태를 읽어 화면을 그린다(렌더러). **클로드는 게임 설계·base 코드를 손으로 쓰지 않는다.**
- **사용자 = 아이디어·장르·취향.** 한 줄 방향을 주고, 골렘 자동화가 소진된 **맨 끝에만** 개입(플레이테스트·밸런스 가이드·기능 아이디어).
- **교정 배경**: detective/sokoban/eterno base는 클로드가 손으로 쓴 골격이었다(골렘은 카드만 패치) — §13(골렘이 처음부터 설계)에서 드리프트한 것. 방치형·발열만 풀 파이프라인 자율 완주. 앞으로 새 게임 base는 골렘이 planning→design→build로 산출한다.

### 22.2 작게 시작 → 점진 검증 (핵심)
처음부터 큰 엔진을 한 번에 설계·빌드하지 않는다. **최소 플레이 가능한 커널**을 골렘이 설계·빌드·그린 받고, 그 위에 **카드를 한 장씩 누적**하며 매 칸 검증(게이트·합의·골든 diff 0) 통과 후에만 다음으로. 실패가 작아 어느 카드에서 깨졌는지 바로 잡힌다(누적 빌드 모델 = §21.2). 처음엔 단계(planning→design→specqa→build)마다 끊어 리뷰하고 하네스를 조인다.

### 22.3 보조는 한시적, 골렘 완전 자율이 목표
지금 사용자+클로드가 하는 보조(스코프를 최소 커널로 좁히기·단계별 끊어 보기·하네스 손으로 조이기)는 처음이라 임시로 메우는 발판이다. **종착점 = 골렘이 한 줄 아이디어만으로 스코프 좁히기·점진 확장까지 처음부터 스스로** 한다. 매 보조는 "나중에 하네스로 흡수할 후보"로 보고, 손으로 한 판단을 골렘 planning/design에 가르쳐 넣어 보조를 0으로 줄인다.

### 22.4 장르 = 전술 SRPG(영걸전형), 정사각 2D부터
- 단발 IF는 사용자 취향 아님 → **전술 SRPG(격자 이동·공격 + 짜여진 루트).** 전투 RPG(취향) + 소설 충실(루트로 서사 보존) + 골렘 검증(결정적 격자) + 비주얼(타일맵→고도)이 한 줄로 정렬되는 교집합.
- **정사각 상하좌우 2D부터.** 골렘 검증·이미지 추출·고도 렌더가 전부 "이산·격자 구조"에서 floor 난이도라 같은 지점. 쿼터뷰/아이소메트릭은 겹침·높이 모호성 때문에 나중(바닥 레이어는 추출 쉬움, 높이 오브젝트는 반자동).
- **엔진과 스토리 분리.** 엔진=전술 룰(스토리 무관, 골렘 검증), 스토리=루트·맵·대사 데이터 레이어(교체 가능). 에테르노 12장면은 캠페인 루트 콘텐츠로 시운전, 풀스토리는 데이터만 교체.

### 22.5 비주얼 단계 (골렘이 룰 소진 후)
- 디자이너 없이 **에셋 팩**(Kenney 등) + **이미지→타일맵 추출**(결정적 CV, 격자 칸을 타일셋과 매칭 — 레이아웃만 뽑음, 규칙은 그림에 없으니 골렘 엔진 몫) + **고도**(TileMap 네이티브).
- 외형은 엔진 상태를 **읽기만** 한다(룰 복제 금지 = 검증 보장 유지). 첫 외형 = 이모지 웹(`studio/eterno_play/server.js`, 아이폰 테일스케일).
- 가챠/카드뽑기 가능 — **시드 PRNG**(결정적·검증 가능)로. 금지는 `Math.random`(비결정)뿐. 골렘이 확률·천장 정확성까지 검증.
- 환원 불가 = 재미·밸런스 취향·아트·게임 "손맛". 사람 몫.

## 23. 실현된 자율 파이프라인 — 완결-후보 무인 생성 (2026-06-20, G82)

§22의 "골렘 완전 자율"이 전술 SRPG에서 실제로 동작하는 형태. 누적 9카드(l1 변칙검술·l2 사거리·l3 지형·l4 유닛·l5 루트맵·l6 상태이상·l7 밸런스·l8 흡혈·l9 처형) 전부 게이트 11/11·골든 diff 0. 클로드 손번역 없이 골렘+하네스가 "엔진+카드+스토리+렌더" 완결 후보를 찍는다.

### 23.1 카드 = base 가산 델타 (그래프트 모델)
한 카드 = 직전 계약(REQ-001..0NN) **verbatim 이월** + 새 REQ 1개(자기완결) + 새 세계 + 참조 game_logic의 **순수 슈퍼셋**(분기만 추가). 가산성 덕에 직전 세계는 자동 바이트동일(회귀 무결). 메커니즘은 hero/enemy의 **opt-in 필드**로 게이팅(없으면 기존과 동일) — 출력 5필드 고정, engine/main/scenarios 불변, **`game_logic.js` 한 모듈만** 변경. 다층 구조(루트맵의 전투 전환)도 updateState/checkGameState에 담아 engine 불변을 유지.

### 23.2 4조각 도구 (각 단계가 무인)
- **(a) 설계 = `card_delta.py` + `graft.py`.** card_delta: 골렘이 현 base 계약+참조 game_logic을 FROZEN으로 받아 가산 델타(new_req·new_worlds+골렘 자기 expected·game_logic 전문)를 base 관례로 직접 출력(HERO-ONLY 불변 앵커로 적턴/AI 환각 차단). graft: 델타를 조립해 키0 검증(회귀 바이트동일·gate·골든·결정성) + **교차검산**(골렘 코드 실행 결과 ↔ 골렘이 적은 expected — 어긋나면 그럴듯하게 틀림으로 보고 기각).
- **빌드 = patch-누적 base.** graft 검증된 lN 참조를 `tactics_base_lN`으로 동결 → 다음 카드는 `build_graded --base tactics_base_lN --inject-modules src/game_logic.js --patch`. 빌더가 전체가 아니라 **델타(FIND/REPLACE)만** 출력 → 출력이 누적 게임 크기와 분리. **전체 재출력(A)은 8카드 깊이에서 붕괴(overall 0.718, 빌더가 누적 코드 축약), patch는 1.0 회복**(§21.5 입증). patch_apply는 줄끝공백 폴백으로 적용 성공률 보강(앞 들여쓰기·모호는 거부=오적용 방지).
- **(b) 스토리 = `gen_tactics_story.py`.** 골렘이 캠페인 전투 시퀀스(고정 비트)를 받아 서사(title/prologue/scenes[name/intro/clear]/epilogue) 저작. 검증은 **구조만**(장면 수=전투 수·키 채움), 엔진/룰 불변(출력전용 B겹), 문장 질은 사람. 산출=campaign_story.json.
- **(c) 렌더 = `gen_tactics_play.py --level lN`.** 패킷·참조 자동 로드, 정사각 탑다운 canvas로 전 세계+캠페인 턴 재생(읽기전용·검증 엔진 require). campaign_story.json 있으면 서사 패널 표시.

### 23.3 종착점 드라이버 = `driver_autocard.py`
한 줄 아이디어 → card_delta(설계+검증) → 참조 동결 → patch 빌드(그린 판정 gate≥1·합의1.0·golden []) → 누적 → 끝나면 스토리+렌더 → REPORT. 실패 단계면 마지막 그린 base 보존하고 중단(키 낭비 방지). 한 바퀴 무인 시연 = l9 처형 카드(손번역 0·5.7분).

### 23.4 "어디까지 만드냐"의 답
스코프는 골렘이 계산하는 고정선이 아니라 **선별 퍼널(§1.5)이 닫는다.** 골렘은 "안 깨진 완결 후보"까지 싸게·많이 찍고, "더 키울지"는 사람 판단("재미있나")·실노출 신호가 정한다. driver_autocard가 이 "완결 후보까지·선별에서 멈춤"을 코드로 구현. 남은 손작업(card_delta·patch 1패스율, 인터랙티브 플레이, 선별 퍼널 결합)은 점진 흡수 대상.
