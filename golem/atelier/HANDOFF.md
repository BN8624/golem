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
python canon_check.py --replay fixtures/replay_demo.json --n 3      # 캐논 채점기
python planning.py --replay fixtures/planning_replay.json            # 기획 A/B/C
python planning.py --replay fixtures/planning_replay.json --synthesize --out runs/demo  # FROZEN 바이블
```

## 현재 위치 (3팀이 책상에 앉음 — design은 채점기만 섬)

- **planning.py** (기획팀) — 로그라인 → lead 바이블 초안 → 10축 독립리뷰 → synthesis(BLOCKING 흡수→FROZEN).
  출력 `bible.json`(premise + canon[{id,text}]) = canon_check 입력 모양 → **두 단계 루프가 닫힘**.
- **canon_check.py** (QA팀) — 동결 바이블 대비 챕터 초고의 캐논 위반을 31B가 잡나. N시드·exact·recall·오탐.
- **design_check.py** (구조팀, 채점) — 비트시트의 setup→payoff 미회수를 31B가 잡나. canon_check의 거울
  (모순 검출↔미회수 검출), 같은 2패스·채점 기계. ★실콜 exact 1.0(S2·S4 recall 1.0, 과교정 없음).
- **design.py** (구조팀, 생산, 신규) — FROZEN 바이블 → lead 비트시트 → 10축 리뷰 → synthesis(FROZEN
  아웃라인). planning.py의 거울. 출력 `outline.json`(premise+setups) = design_check 입력 모양 → 루프 모양 닫힘.
  키 0 `--replay` 통과(setups 5/beats 11 FROZEN). 31B 핀+ROLE 가드 포함.
- **lib/** — 자족 인프라(config·llm·key_usage·jsonutil). 골렘 import 0. `PROJECT_ROOT`=atelier 루트.
- 커밋됨: `2882c90`(planning)·`9711990`(자족화)·`94cf9a7`(canon_check 출범)·`8b16314` 등.

검증된 실측치:
- canon_check 실 31B: exact 1.0 / 2-of-2 / 안정 1.0 / 오탐 0 (단, 픽스처가 쉬워 당연에 가까움).
- planning 실 31B(영어): BLOCKING 12 흡수 → canon 8 → FROZEN. 한 줄 아이디어가 실제로 자람(Soul-Echo 등).
- planning 실 31B(한국어): BLOCKING 10 흡수 → canon 7 → FROZEN. synth 11병렬 빈패킷 0/11 = 한국어 안정.

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

### ▶ 다음 세션 첫 액션 — design end-to-end ★실콜 (키 필요, 사용자 go)

1. **design 실생산 → 실채점**(루프 닫기 마무리): `python design.py --bible runs/bible_packet_ko/bible.json
   --out runs/outline_ko` 로 실제 비트시트 생산 → 생산물(outline.json+beatsheet)을 design_check으로
   golden=[] 채점(임시 cases.json 1줄). "생산자가 정말 모든 setup을 회수했나"가 통과하면 planning→design→
   design_check end-to-end가 닫힌다(canon-162900의 design판).
2. **어려운 design 픽스처**(2패스 한계 측정): 회수를 정황에만 숨기거나(미회수를 1패스가 놓치게) 회수처럼
   보이는 함정(헛회수를 1패스가 오인하게)을 깔아, design_check 2패스가 canon처럼 precision을 끌어올리나 본다.

> 권고: 1을 먼저(루프 닫기) → 2로 한계 측정. 보류 카드: 통사적 부정 한계 공략(canon hard3 subtle_clean
> 오탐 0.33→0, 검증 프롬프트에 "부정문 방향 먼저" 명시) — 별도 안건, 필요할 때.

> 한계 메모: 지식상태/타임라인 위반은 현재 canon 구조(정적 사실 7개)론 직접 채점 불가 — canon이 "X시점엔
> Y를 모른다" 같은 시간적 사실을 안 담는다. 그 유형을 재려면 canon 스키마 확장이 선행돼야 한다(별도 안건).

### 그 뒤 — design 단계

planning이 한국어로 닫혔고 precision도 2패스로 확보됐으니, FROZEN 바이블을 계약 패킷으로 받아 design
(비트시트 + setup→payoff)이 얹힌다. design 산출물도 같은 검출/검증 2패스 패턴으로 채점한다.

## 그 뒤 로드맵

- design 단계(비트시트 + setup→payoff traceability) — 다음 팀.
- 캐논 원장 누적(p0..p4 단계적 확장 = "아이디어 키우기").
- **어려운 캐논 픽스처**로 채점기 한계 깨기(지금 1.0은 쉬운 픽스처 탓). 캐논/미학 경계 확정.

## 키 규칙 (중요)

- atelier는 **자기 11키**(`atelier/.env`)만 쓴다. 골렘 루트 11키와 값 0겹침, 22프로젝트 독립.
- 골렘 규칙 준수: 실제 31B 런(키)은 사용자 go 뒤에. replay는 키 0.
- 키·값을 로그/아티팩트에 출력하지 않는다. `runs/`·`.env`는 gitignore.

## 한국어 보고 규칙

문장은 마침표로 끝낸다(콜론은 라벨·키밸류·코드만). 새 소스파일 첫 줄은 역할 한국어 주석.
