# Atelier HANDOFF — 새 세션은 여기부터

## 한 줄 정체성

골렘 studio(가상 게임회사)의 구조를 **소설 작가 공방(atelier)** 으로 옮긴 프로젝트.
"굴러가나 → 정답(exact oracle)"을 소설의 **"캐논이 맞나"** 로 재현한다. 설계 정본은 `NovelStudioMode.md`,
결정 이유는 `context-notes.md`, 진행 체크는 `checklist.md`.

> **이전 예정**: atelier는 나중에 독립 프로젝트로 *다른 폴더로 이전*한다. 지금 골렘 밑에 둔 건
> 골렘이 크는 동안 거기 아이디어(auto_oracle·planning 등)를 바로 차용하려는 임시 위치다.
> 그래서 **골렘 폴더 코드 의존은 0**이다(인프라는 `lib/`에 vendoring). 폴더째 옮기면 그대로 돈다.

## 빠른 시작 (키 안 씀 — 배선 확인용)

```bash
cd golem/atelier
python canon_check.py  --replay fixtures/replay_demo.json --n 3                 # 캐논 채점기
python design_check.py --replay fixtures_design/replay_demo.json --n 3          # setup→payoff 채점기
python specqa_check.py --replay fixtures_specqa/replay_demo.json --n 3          # 캐논/미학 격리 채점기
python planning.py --replay fixtures/planning_replay.json --synthesize --out runs/demo          # FROZEN 바이블
python design.py   --replay fixtures_design/design_replay.json --out runs/demo_outline          # FROZEN 아웃라인
```

## 현재 위치 (생산 2 + 채점 3 = 5 도구, specQA 채점기 키0 배선검증까지)

- **planning.py** (기획, 생산) — 로그라인 → lead 바이블 → 10축 리뷰 → synthesis(FROZEN 바이블).
  출력 `bible.json`(premise+canon) = canon_check 입력 모양.
- **canon_check.py** (QA, 채점) — 동결 바이블 대비 챕터 초고의 캐논 *모순*을 31B가 잡나. 2패스·N시드·exact·recall·오탐.
- **design.py** (구조, 생산) — FROZEN 바이블 → lead 비트시트 → 10축 리뷰 → synthesis(FROZEN 아웃라인).
  출력 `outline.json`(premise+setups) = design_check 입력 모양. planning의 거울.
- **design_check.py** (구조, 채점) — 비트시트의 setup→payoff *미회수*를 31B가 잡나. canon_check의 거울.
- **specqa_check.py** (계약, 채점) — 씬 계약 기준을 캐논(검증가능)/미학(검증불가)으로 *가르나*. 앞 둘이
  *검출*이면 이건 *격리(분류)*. fp(미학→캐논 오라벨)=금지된 합의채점 흉내라 핵심축. ★실콜 아직(키0 배선만).
- **lib/** — 자족 인프라(config·llm·key_usage·jsonutil). 골렘 import 0. `PROJECT_ROOT`=atelier 루트.
- 최근 커밋: `1095172`(리뷰 수정)·`bc01e2f`(design hard2)·`538104b`(design.py)·`9693a5a`(design_check)·`f567e0a`(31B 핀).

검증된 실측치(실 31B):
- canon_check: 기본 exact 1.0. hard1 1패스 0.5→2패스 1.0(precision은 2패스 필요). hard3 이중부정은 2패스도 0.834(통사 한계).
- design_check: 기본·hard·hard2 모두 exact 1.0 — **정황회수·헛회수·오회수·부분회수 4축 1패스 robust**(2패스 불필요).
  → **비대칭: 모순검출(canon)은 precision에 2패스 필요, setup→payoff(design)는 1패스 충분.** 과제 구조가 가름.
- planning/design: 실생산 FROZEN 패킷 생성 + end-to-end(생산물→채점) 한 바퀴(canon-162900 / design-195923).
- **FROZEN 게이트 결함 수정됨**(외부 리뷰): 거짓 0 제거(개수 게이트) + canon/setup ID 중복 검사 + 결과 타임스탬프 보존.

## ✓ 해소됨 — 한국어 synthesis 빈 패킷 (재현 안 됨, 2026-06-18)

이전 핸드오프가 "한국어 = 빈 패킷(OPEN)"이라 단정했으나 **코드 수정 없이 재현 실패**. synth만 11키 병렬로
재서 **빈 패킷 0/11**(단발 1 + 병렬 11 = 12/12 FROZEN, canon 5~7). 잘림이 간헐이면 11번 중 한 번은
났어야 하는데 0이다. → 코드 결함 아니라 그때 모델/서버 일시 상태로 판단(이번에도 5xx 재시도 복구).

- 근본 수정(max_output_tokens 상향) 불필요. 진단 덤프(`RealCaller.synth`→`runs/_synth_raw.txt`)는
  안전망으로 **유지**(실패시만 작동, 무해). 자세한 근거는 `context-notes.md`.
- 산출물: `runs/bible_packet_ko/`(한국어 FROZEN 바이블, canon 7축 — 카엘·리아 남매, 영혼의 조각 5개 등).

### end-to-end 닫힘 (2026-06-18, canon-20260618-162900)

`fixtures_ko/`(한국어 바이블 canon 7축 + 위반/클린 초고) 실콜 채점 → clean exact 1.0/오탐 0,
violation C1·C2 모두 1.0. **패러프레이즈 모순(왼손 고삐·피 안 섞인 남남)도 31B가 검출.**
→ frontier 1·2 닫힘: 한 줄 로그라인 → FROZEN 바이블 → 캐논 채점이 실콜로 한 바퀴 돈다.

### 채점기 한계 노출 — 캐논/미학 경계 1차 데이터 (2026-06-18, canon-20260618-170505)

`fixtures_ko_hard`(함의 위반 hard + 위반0 함정 trap)로 밀어 첫 한계 확정.
- **검출(recall) 강함**: hard의 C3·C6를 한국어 함의로 추론 검출(1.0).
- **precision 약함(실한계)**: trap "한 어머니에게서 난 친누이"(C2와 일치)를 31B가 매번 C2 위반으로 뒤집음.
  명시 지시·few-shot(동형 양성예시) **둘 다 불가역**. 오탐 1.0 그대로.
- 부수 수확: rule_id 정규화 버그 픽스(`_norm_id`) + fp 진단 계측(오탐 규칙+근거를 결과 JSON에 남김).
- 경계 1차 결론: 경계는 "검출되나"가 아니라 "거짓 경보 억제하나"에 있다. 상세 `context-notes.md`.

### ✓ 2패스 검증이 precision 한계를 깸 (2026-06-18, canon-20260618-171503)

`--verify`(1패스 위반 후보를 별도 콜로 "정말 모순이냐" 재확인 → confirmed만): trap 오탐 1.0→**0**,
hard 검출 C3·C6 **1.0 유지**, 전체 exact 0.5→**1.0**. precision 한계는 모델 능력이 아니라 단일콜
프레이밍 탓 — 검출/검증을 쪼개니 풀렸다(콜 약 2배). **경계 재이동: precision도 기계화 가능.** 상세 context-notes.

### ✓ 2패스 스트레스 완료 — 과교정 없음 + 통사적 부정 한계 발견 (2026-06-18)

`fixtures_ko_hard2`/`fixtures_ko_hard3` 실콜로 2패스의 두 주장을 스트레스. 결과:
- **hard2**: 측정 가치 0이 됨. 위반을 직접 진술로 둬서 1패스가 이미 완벽(exact 1.0) → 2패스 차이 없음.
  교훈: 위반은 **함의에 숨겨야** 2패스 차이가 측정된다.
- **hard3**(canon-185805 1패스 / 190219 2패스): 위반을 행동·정황에만 숨기고 clean에 이중부정 덫을 깖.
  - **(b) 과교정 없음 — 확정**: subtle_violation 검출 C1·C3 1패스 1.0 → 2패스 **1.0 유지**. 미묘한 진짜
    위반도 2패스가 안 깎는다. precision↔recall 트레이드오프 안 나옴 → 2패스 robust가 hard1 단일 사례를 벗어남.
  - **(a) 새 한계**: subtle_clean 오탐 1패스 1.0 → 2패스 **0.33 잔존**(안정 0.67). **이중부정**("친누이가
    *아니*라는 헛소문을 일축"=실제론 친누이 맞음)을 31B가 못 풀어 2패스 재확인도 시드마다 흔들림. hard1
    trap은 →0 완전 제거였는데 이건 안 사라짐. **통사적 부정 구조는 2패스로도 부분적으로만 강하다.**

**경계 갱신**: 2패스는 *의미 모순*엔 robust, *통사적 부정 구조*엔 부분적. 별개의 한계 축이다. 상세 context-notes.

### ✓ design 단계 출범 — setup→payoff 채점기 (2026-06-18, design-20260618-192236)

frontier 3 시작. 사용자가 "2(design 본류)"를 골랐다. canon_check의 **거울**을 채점기로 먼저 지었다.
- **design_check.py**: 추적 설정 목록(promise/object/mystery/threat) + 비트시트 → 31B가 *회수 안 된
  설정*을 짚나. canon_check이 "사실 모순"을 잡듯 design_check은 "약속 미회수"를 잡는다. 검출/검증
  2패스(`--verify`) + N시드·exact·recall·오탐·안정성 기계 그대로 재사용. `setup_id`/`unresolved`만 다름.
- **심은 픽스처 `fixtures_design/`**: outline.json(설정 S1~S5, 카엘·리아 세계 연속) + 클린(전부 회수)
  + 미회수(S2 펜던트·S4 부대몰살을 *언급은 하되 회수만 안 함*, 골든 [S2,S4]) + cases + replay_demo.
- **키 0 검증 통과**: `--replay`로 채점 수학 정확 — clean exact 0.67/오탐 0.33, unresolved exact 0.67/
  recall S2 1.0·S4 0.667, `[S4]`→`S4` 정규화 작동. 일부러 흔든 시드가 구분돼 수학 신뢰됨. 상세 context-notes.

### ✓ design 채점기 ★실런 + 생산자 design.py (2026-06-18)

- design_check ★실콜: exact 1.0(design-193115/193408), S2·S4 recall 1.0, 2패스 과교정 없음. 단 1패스가
  이미 완벽해 2패스 *차이*는 0(canon hard2 상황) — 어려운 픽스처가 있어야 2패스 가치가 측정된다.
- 31B 핀 가드 추가(canon_check·design_check 실콜 경로) — 26B 전수조사 호출 0 확인 후 잠복 위험 차단.
- design.py(planning 거울) 출범 — 바이블 → 비트시트 → 10축 → FROZEN 아웃라인. 키 0 replay FROZEN 통과.

### ✓ design end-to-end 닫힘 (2026-06-18, design-195923)

`design.py --bible bible_packet_ko/bible.json` 실생산(BLOCKING 5 흡수, setups 6/beats 10 FROZEN) →
생산물을 design_check `--verify`로 golden=[] 채점 → exact **1.0**/오탐 0/안정 1.0. 생산자가 setup 6개를
실제로 다 회수 + 채점기 동의 → **planning → design → design_check가 실데이터로 한 바퀴**(canon-162900의
design판). 단 생산자 synth가 "다 회수하라"를 강제받아 미회수가 잘 안 난다 — 이 루프는 *합의 확인*이지
*채점기 한계 측정*은 아니다(한계는 심은 픽스처 몫).

### ✓ design 2패스 한계 측정 — 1패스가 hard 양방향 깸 (2026-06-18, design-200627/200930)

`fixtures_design_hard`(정황회수 fp축 + 헛회수 fn축)로 밀었다. canon hard1(precision 약→2패스 필요)의
재현을 노렸으나 **반대 결과** — design은 1패스부터 강했다.
- subtle_clean: 함의 회수(서명·문양·호명)를 1패스가 **회수로 인정** → 오탐 0(헛잡지 않음).
- hidden_unresolved: 재언급-only 헛회수(펜던트 꼭 쥠·동료 이름)를 1패스가 **미회수로 검출** → recall 1.0.
- 2패스도 1.0 유지(과교정 없음). → **2패스 측정가치 0**(1패스가 이미 완벽).
- **경계 비대칭(핵심 데이터)**: canon은 precision에 2패스가 필요했는데 design setup→payoff는 1패스부터
  precision·recall 양방향 강하다. 과제 구조(국소 모순판정 vs 전역 약속탐색)가 2패스 필요성을 가른다. 상세 context-notes.

### ✓ design hard2 — 가짜 payoff도 1패스가 깸, 4축 robust (2026-06-18, design-202038/202419)

오회수·부분회수(`fixtures_design_hard2`)도 1패스가 깼다. misattributed(던져탈출·복수처럼 쓰이나 정체/
명령자 미규명) recall 1.0 + **2패스 과교정 0**("썼다" 정황에도 안 깎음), partial(4/5 조각) recall 1.0.
→ **정황회수·헛회수·오회수·부분회수 4축 모두 1패스 robust, 2패스 불필요·무해.** canon은 precision에
2패스를 요했던 것과 대조. **잠정 결론: setup→payoff는 31B 1패스로 충분.**

### ✓ specQA 채점기 출범 — 캐논/미학 격리, 키0 배선검증 (2026-06-18, specqa-214057)

frontier 4 시작. NovelStudioMode oracle 2층("검증가능 캐논 vs 검증불가 미학")을 31B가 기계화하나. 앞 둘과
달리 *검출*이 아니라 *격리(분류)* 과제로 확정했다 — 매핑표 specQA 행과 핸드오프 frontier 질문이 일치.
"초고 검증"은 build/integration 범위라 제외. 상세 context-notes.

- **specqa_check.py**: 입력 premise+씬 기준목록 → 31B가 캐논이라 라벨한 집합 출력, 골든=심은 캐논 ID.
  design_check의 detect/verify 2패스·N시드·exact·recall·fp·안정성 그대로(`verifiable`/`criterion_id`만 다름).
  **fp(미학→캐논 오라벨)=NovelStudioMode가 금지한 "합의채점 흉내"라 핵심 측정축**, 보수적 기본값 "의심되면
  미학". 31B 핀+ROLE 가드 포함.
- **심은 픽스처 `fixtures_specqa/`**: 카엘·리아 세계. scene_mixed(C1·C3·C4·C6=캐논/C2·C5=미학) +
  scene_aesthetic(전부 미학, 골든 []). 후자는 design clean(빈 골든)의 거울이되 **반대 실패**(검증가능
  지어내기)를 잰다.
- **키 0 검증 통과**: scene_mixed exact 0.667(흔든 시드 C4누락+C2헛라벨)·C4 recall 0.667·fp 0.33,
  scene_aesthetic exact 0.667(C1 헛라벨)·"(전부 미학 계약)" 출력. fp 진단 계측도 결과 JSON에 기록.
  일부러 흔든 시드가 구분돼 채점 수학 신뢰됨.

### ✓ specQA ★실콜 — 격리 강함, 혼합 기준이 경계 (2026-06-18, specqa-214932/215325)

1패스/2패스 **완전 동일**: exact 0.5, 안정 1.0, **fp 0**.
- **금지된 방향 0(핵심 성공)**: scene_aesthetic(전부 미학)에서 검증가능을 **하나도 안 지어냄**(exact 1.0).
  NovelStudioMode가 가장 경계한 "합의채점 흉내"(미학→캐논)가 실데이터에 안 나타남.
- **유일 오류 = 안전한 fn**: scene_mixed C1·C3·C4 recall 1.0, 그런데 **C6(적대자/우호적 묘사 금지)을 3/3
  미학으로 흘림.** 위험한 fp가 아니라 보수적 과격리.
- **C6 = 혼합 기준 모호성**: 사실(발타자르=적대자)+톤(우호적이냐)이 섞여, 모델이 작동 절을 취향으로 읽음.
  변호 가능. **진짜 경계는 혼합 기준에 있다** — 씬 계약은 사실/톤 축을 원자화해야(설계 통찰).
- **2패스=1패스이되 canon과 이유 다름**: verify는 fp(과대주장)만 깎는 도구라, 오류가 fn(과소주장)인 이
  케이스엔 구조적으로 안 닿음. 과교정도 0. → specQA의 위험축(fp)을 재려면 fp가 나는 픽스처가 필요. 상세 context-notes.

### ▶ 다음 세션 첫 액션 — specQA hard 픽스처 (키0 먼저, 그 뒤 ★실콜)

- **C6 가설 확인용 hard 픽스처** `fixtures_specqa_hard` — (1)원자화된 순수 캐논 vs 혼합 기준(사실+톤)을
  나란히 둬 격리 한계가 정말 혼합에 몰리나 + (2)**미학을 구체어로 위장한 fp 함정**("점층한다"·"일관돼야"처럼
  검증돼 보이나 실은 취향)으로 *위험 방향(fp)*을 일부러 유발 → 2패스가 그 fp를 깎나(canon precision의 specQA판).
  심은 골든 + 키0 replay → ★실콜. canon/design hard 진행의 specQA판.
- **specQA 생산자**(planning/design 거울) — 그 뒤. FROZEN 아웃라인(`outline.json`+`beatsheet.md`)을 받아
  씬별 계약을 산출. 채점기가 먼저 선 패턴 유지.

### 백로그 (리뷰 미반영 + 보류 카드)

- (리뷰 3) evidence 실문장 근거 검증 — 채점 정확도 안 올려 우선순위 낮음. 필요시.
- (리뷰 4) 생산·검증 동일모델 = 해석의 한계. 26B/사람 표본 비교 *측정설계*로만 갚음(코드수정 아님).
- (리뷰 6) vendoring 분기 — atelier 독립이전 시점에 골렘 정본과 정리.
- design 채점기 장거리 축(비트 20+) — 한계효용 낮음, 1패스 충분 결론 굳히기용.
- 통사적 부정 한계(canon hard3 subtle_clean 오탐 0.33→0) — 검증 프롬프트에 "부정문 방향 먼저" 명시.
- 캐논 원장 누적(p0..p4 단계적 확장 = 아이디어 키우기).

> 한계 메모: 지식상태/타임라인 위반은 현재 canon 구조(정적 사실)론 직접 채점 불가 — canon이 "X시점엔
> Y를 모른다" 같은 시간적 사실을 안 담는다. 그 유형을 재려면 canon 스키마 확장이 선행돼야 한다(별도 안건).

## 키 규칙 (중요)

- atelier는 **자기 11키**(`atelier/.env`)만 쓴다. 골렘 루트 11키와 값 0겹침, 22프로젝트 독립.
- 골렘 규칙 준수: 실제 31B 런(키)은 사용자 go 뒤에. replay는 키 0.
- 키·값을 로그/아티팩트에 출력하지 않는다. `runs/`·`.env`는 gitignore.

## 한국어 보고 규칙

문장은 마침표로 끝낸다(콜론은 라벨·키밸류·코드만). 새 소스파일 첫 줄은 역할 한국어 주석.
