<!-- 소설 "에테르노의 그림자"(아뜰리에 원고)를 골렘 게임 카드로 옮기는 구조 설계 — 선형→분기 발명 + 메커니즘 직역 + 카드 분해 (키0 산출물) -->

# 에테르노의 그림자 — 소설→게임 브리지 구조 설계

원작: 아뜰리에 `runs/release_manuscript_ko_adversarial_fix_v5/manuscript.md`(12장면, 읽기 전용).
이 문서는 **골렘이 하는 일(구조화+건전성)** 만 정의한다. 문장·각색 충실도는 사람 몫.
장르 = **내러티브 IF 뼈대 + 턴제 전투 카드(하이브리드)**. IF는 `detective_base`, 전투는 `combat_base` 패턴 재사용.

## 1. 원작 12장면 → 게임 매핑

| # | 원작 장면 | 게임 노드(IF) | 핵심 사건 | 직역 메커니즘 |
|---|---|---|---|---|
| 1 | (검문 잠입) | `checkpoint` | 호흡법으로 마력 동조→위장→통과 | 잠입 분기(들킴=BAD) |
| 2 | 첫 번째 조각의 각성 | `altar_1` | 결정체에 피→조각1 각성·방계 자각 | 조각 수집 +1 |
| 3 | 고대 유적으로의 여정 | `ruins_approach` | 피의 제사 소문→유적 함정 매복 | 타이머 노출·전투 진입 |
| 4 | 불균형의 발견 | `combat_discover` | 정석 막힘→환상통 불균형=변칙 관통 | **변칙검술 발견(전투)** |
| 5 | 두 번째 조각의 기억 | `altar_2` | 조각2·숙청 환영→북부 무기고 | 조각 수집 +1 |
| 6 | 배신의 낙인 | `armory` | 조각3·팔 잃은 배신 기억 | 조각 수집 +1 |
| 7 | 변칙의 완성 | `combat_master` | 조각4·리아 신호로 변칙 의도적 완성 | **변칙검술 숙달(전투)** |
| 8 | 찬탈자의 실체 | `sanctum` | 조각5·발타자르 진실(혈족 사육) | 조각 수집 +1(=5/5) |
| 9 | 결단과 여명 | `decision` | 추격대 포위→지휘관이 "보름 뒤 개기일식" 확정 | **타이머 시작(보름)** |
| 10 | 에테르노 잠입 | `infiltrate` | 보름 소진→재잠입→선제공격 | 타이머 소비·잠입 |
| 11 | 최후의 결전 | `final_combat` | 변칙 역격으로 혈액 추출관 파괴 | **변칙검술 보스(전투)** |
| 12 | 새로운 시대의 선포 | `end_dawn` | 다섯 조각 융합→가짜권능 붕괴 | 결말(승리) |

원작은 **단선**이다. 게임화의 핵심 발명은 "실패할 수 있게" 만드는 분기(아래 §4).

## 2. 게임 상태 스키마 (detective state 확장)

```
turn        number      진행 카운터
scene       string      현재 노드
fragments   string[]    수집한 조각 ['F1'..'F5'] (유니크, 5개 목표)
eclipse     number      개기일식까지 남은 보름; 시작=ECLIPSE_TURNS(10), 결말 아닌 장면 매 턴 −1, 0이면 RITUAL
beats       string[]    발동한 서사 비트(AWAKENING=F1, RESONANCE=F1~5)
ending      string|null NEW_DAWN | RITUAL_COMPLETE | FLED | CAUGHT | null
isGameOver  boolean
logs        string[]
```

전투 노드는 `combat_base` 서브상태(HP·gauge·energy·distance·stun·shield)를 별도로 돌리고,
결과(승/패)만 IF 상태로 환원한다(전투는 카드 단위로 누적).

## 3. 4대 메커니즘 직역 (검증 가능 = 골렘 / 취향 = 사람)

1. **조각 수집(F1~F5)** — detective 단서(clue) 패턴 직역. 제단 노드에서 "피를 떨어뜨린다" 선택 시
   해당 조각을 `fragments`에 유니크 추가·`조각:F<n>` 로그. 5개 모두 모여야 보스 노드가 진실 결말로 분기.
   → `detective_base` clue 메커니즘과 1:1. **검증 가능**(개수·유니크·로그 결정적).
2. **개기일식 타이머(보름)** — `eclipse`가 시작부터 카운트다운(always-on, ECLIPSE_TURNS=10). 결말 아닌
   장면에 머무는 매 턴 −1, 0이면 결말 `RITUAL_COMPLETE`(피의 제사 완성=BAD). always-on이라 시작턴 off-by-one
   모호성 없음. **검증 가능**(카운트다운 결정적).
3. **변칙검술(정석=막힘/변칙=관통)** — `combat_base`로 직역. 적은 *마나 방패*(정석 궤적 필터) 보유.
   - 정석 ATTACK(RULE-04)은 방패가 흘려보냄 → 데미지 0(막힘).
   - 신규 ANOMALY 액션: "환상통으로 무게중심 붕괴"를 비용으로(자세 불안정 토큰) 방패 사각 관통 → 데미지 적중.
   → combat RULE-09+로 카드화. **검증 가능**(정석=0뎀/변칙=적중 결정적). 검술의 "느낌"은 사람.
4. **분기 결말** — 단서 완비(detective verdict 패턴) + 타이머로 결말 셋(아래 §4).

## 4. 분기 발명 (선형 → 분기) — 골렘이 더하는 가치

원작엔 없는 "질 수 있는 길"을 넣어 게임으로 만든다. 충실도 훼손 없이 *원작 결말을 정답 경로*로 둔다.

- **NEW_DAWN(원작 결말, 정답)**: F1~F5 전부 수집 + `march`로 대면 승리(타이머 만료 전).
- **RITUAL_COMPLETE(실패)**: 조각 미완으로 대면하거나 타이머 소진(`eclipse<=0`) → 피의 제사 완성.
- **FLED(이탈)**: `turn_back`/`flee`로 퀘스트 포기.
- **CAUGHT(실패)**: 검문에서 `bluff`로 들킴 → 즉시 구금(Card1이 더하는 분기). 원작에서 카엘이 *피한* 길.
- (이후 전투 패배도 CAUGHT/RITUAL로 환원.)

base 결말 셋(NEW_DAWN/RITUAL_COMPLETE/FLED)은 detective의 TRUTH/COLD_CASE/WALKED_AWAY와 동형, CAUGHT는 카드가 add-only로 추가.

## 5. 카드 분해 (허브형 add-only 누적 — engine/state/beats 고정, scenes 곁가지만 성장)

**핵심 규율(A1, 수정)**: detective/sokoban처럼 **base가 완결된 줄거리**이고 카드는 **허브(hub)에 곁가지를
ADD**한다(기존 전이 불변 → 회귀 바이트동일 보장). 줄거리를 "앞으로 늘리는"(기존 종료를 전이로 바꾸는) 방식은
누적 회귀를 깨므로 금지.

- **eterno_base(완결)** — `start`→(`enter`)→`hub`에서 다섯 조각(altar_1~5) 회수→`march` 대면→
  NEW_DAWN/RITUAL_COMPLETE/FLED. AWAKENING(F1)·RESONANCE(F1~5)·타이머 전부 base가 실행. **엔진 기계장치 완비.**
- **Card 1 (l1, scenes.js만)** — `start`에 `infiltrate` 곁가지 ADD → `checkpoint`(attune→hub / bluff→CAUGHT).
  기존 enter/turn_back 불변 = 회귀 무결. **패킷화 완료, 첫 빌드 대상.**
- **Card 2 (combat, 누적)** — hub에 전투 곁가지(`patrol`→combat_base 마나방패+ANOMALY→hub) ADD. 변칙검술.
- **Card 3 (beats/scenes 누적)** — 조각 회수 시 추가 서사 비트(배신 기억 등) + 곁가지 장면. add-only.

각 카드는 직전 카드 출력 위에 누적, 직전 전체 시나리오 회귀 0 깨짐이 불변식(쇼케이스 규율 + 사전필터 ①).

## 6. 경계 — 골렘 vs 사람

- **골렘(검증 가능)**: 조각 개수/유니크, 타이머 카운트다운, 정석=0뎀·변칙=적중, 결말 분기 조건, 회귀 무결.
- **사람(취향)**: 장면 묘사·대사 문장, 변칙검술의 연출, 분기 난이도 밸런스, 각색이 원작 정서를 지키는가.
- 사전필터 ②가 "안 깨졌나"를 공짜로 걸러 사람 판단을 "재미있나"에만 쓰게 한다(북극성 §1.5).

## 7. 다음 단계

1. **Card 1 패킷화 — 완료.** `eterno_base`(7모듈, RULE-01~07 완비) + `planning_packet_eterno_l1`(RULE-08) +
   `specqa_packet_eterno_l1`(누적 8시나리오, REF node 역산, 회귀 base 골든과 바이트동일). driver 등록(l1).
2. (다음) **무인 빌드 `driver_showcase.py eterno`(★키)** — 31B가 base에 Card1(scenes.js) 패치 → 게이트·합의·골든 diff.
3. Card 2 combat 규칙(마나방패+ANOMALY) 계약화 → 누적 빌드 → 사전필터 ① 통과 → 사람 검토.
