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

## 현재 위치 (2팀이 책상에 앉음)

- **planning.py** (기획팀) — 로그라인 → lead 바이블 초안 → 10축 독립리뷰 → synthesis(BLOCKING 흡수→FROZEN).
  출력 `bible.json`(premise + canon[{id,text}]) = canon_check 입력 모양 → **두 단계 루프가 닫힘**.
- **canon_check.py** (QA팀) — 동결 바이블 대비 챕터 초고의 캐논 위반을 31B가 잡나. N시드·exact·recall·오탐.
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

### ▶ 다음 세션 첫 액션 — 콜 직전까지 준비됨 (키만 대면 돈다)

**준비물**: `fixtures_ko_hard2/`(2패스 스트레스 픽스처) 작성·검증 완료. 키 콜 직전에서 멈춤.
- `subtle_violation`(golden C1·C6): **미묘한 진짜 위반** — "두 팔 늘어뜨림"(C1=왼팔없음 위반),
  "발타자르도 곁가지나마 옛 왕가 핏줄"(C6=발타자르 왕가아님 위반). → 2패스가 *과교정*으로 이 진짜
  위반을 reject해 검출을 깎나?
- `subtle_clean`(golden 없음): **위반0 함정** — "다섯 조각 중 셋"(C5 일치), 카엘이 왕가 방계로 조각
  활성화(C3·C4 일치), 무장 은닉 국경 우회(C7 일치). → 1패스 오탐을 2패스가 제대로 거르나?

**돌릴 것** (★키, 비교 측정):
```
python canon_check.py --fixtures fixtures_ko_hard2 --n 3            # 1패스 (오탐 기준선)
python canon_check.py --fixtures fixtures_ko_hard2 --n 3 --verify   # 2패스
```
**판정**: 2패스가 subtle_clean 오탐을 0으로 거르면서 subtle_violation 검출(C1·C6)을 1.0 유지하면
→ 2패스 robust 확정. 만약 subtle_violation 검출이 떨어지면 → **2패스의 precision↔recall 트레이드오프**
노출(과교정). fp 계측(`false_alarm_evidence`)으로 무엇을 거르고 무엇을 놓쳤나 본다.

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
