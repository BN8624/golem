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

## 현재 위치 (생산 3 + 채점 3 = 6 도구, specQA 생산자까지 키0 닫힘 — ★실콜 다음)

- **planning.py** (기획, 생산) — 로그라인 → lead 바이블 → 10축 리뷰 → synthesis(FROZEN 바이블).
  출력 `bible.json`(premise+canon) = canon_check 입력 모양.
- **canon_check.py** (QA, 채점) — 동결 바이블 대비 챕터 초고의 캐논 *모순*을 31B가 잡나. 2패스·N시드·exact·recall·오탐.
- **design.py** (구조, 생산) — FROZEN 바이블 → lead 비트시트 → 10축 리뷰 → synthesis(FROZEN 아웃라인).
  출력 `outline.json`(premise+setups) = design_check 입력 모양. planning의 거울.
- **design_check.py** (구조, 채점) — 비트시트의 setup→payoff *미회수*를 31B가 잡나. canon_check의 거울.
- **specqa_check.py** (계약, 채점) — 씬 계약 기준을 캐논(검증가능)/미학(검증불가)으로 *가르나*. 앞 둘이
  *검출*이면 이건 *격리(분류)*. fp(미학→캐논 오라벨)=금지된 합의채점 흉내라 핵심축. ★실콜·hard 완료.
- **specqa.py** (계약, 생산) — FROZEN 아웃라인 → lead 씬 계약 → 10축 → synthesis(FROZEN). 기준 원자화 +
  kind 태깅. 출력 contract.json(=specqa_check 입력) + cases.json(=닫힘 검증 golden). specqa_check의 거울.
- **lib/** — 자족 인프라(config·llm·key_usage·jsonutil). 골렘 import 0. `PROJECT_ROOT`=atelier 루트.
- 최근 커밋: `2109aad`(specqa.py 생산자)·`c39b56c`(HANDOFF 정리)·`624a768`(specQA hard 실콜)·`61c1cb3`(specQA hard 픽스처).

검증된 실측치(실 31B):
- canon_check: 기본 exact 1.0. hard1 1패스 0.5→2패스 1.0(precision은 2패스 필요). hard3 이중부정은 2패스도 0.834(통사 한계).
- design_check: 기본·hard·hard2 모두 exact 1.0 — **정황회수·헛회수·오회수·부분회수 4축 1패스 robust**(2패스 불필요).
- specqa_check: 기본 exact 0.5(혼합 기준 C6만 미학으로 흘림)·hard exact 1.0 — **순수 캐논 recall 1.0·순수 미학 fp 0(미끼에도)**.
  유일 soft spot은 혼합 기준(사실+톤) → 채점기 아닌 계약 원자화(생산자) 몫.
- → **3채점기 비대칭: canon(모순검출)만 precision에 2패스 필요, design(setup→payoff)·specQA(격리)는 1패스 충분.** 과제 구조가 가름.
- planning/design: 실생산 FROZEN 패킷 생성 + end-to-end(생산물→채점) 한 바퀴(canon-162900 / design-195923).
- **FROZEN 게이트 결함 수정됨**(외부 리뷰): 거짓 0 제거(개수 게이트) + canon/setup ID 중복 검사 + 결과 타임스탬프 보존.

## 지나온 길 (실측 타임라인 — 상세 추론은 `context-notes.md`, 진행 체크는 `checklist.md`)

- **frontier 1·2 닫힘** (canon-162900) — 한국어 FROZEN 바이블(`runs/bible_packet_ko/`, canon 7축) →
  `fixtures_ko/` 실콜 채점: clean exact 1.0, violation C1·C2 1.0. 패러프레이즈 모순도 검출. 한국어 synth
  빈 패킷은 코드 결함 아님(재현 실패, 진단 덤프만 안전망 유지).
- **canon 한계·2패스** (canon-170505/171503) — hard1 1패스는 precision 약(trap "친누이" 오탐 1.0,
  프롬프트·few-shot 불가역). `--verify` 2패스로 오탐 1.0→0·검출 1.0 유지·exact→1.0. precision도 기계화 가능.
- **canon 2패스 스트레스** (canon-185805/190219) — hard3로 과교정 없음 확정(미묘 위반 1패스=2패스 1.0).
  단 **이중부정(통사 구조)**은 2패스도 0.33 잔존 — 별개 한계 축. (부수: `_norm_id` 픽스 + fp 진단 계측.)
- **design 채점기 + 생산자** (design-193115/195923) — design_check(setup→payoff 미회수) ★실콜 exact 1.0,
  design.py(planning 거울) 출범, end-to-end 닫힘(생산물→채점 1.0). 31B 핀 가드 추가.
- **design 4축 robust** (design-200627~202419) — hard/hard2로 정황회수·헛회수·오회수·부분회수 4축 모두
  1패스 robust, 2패스 불필요·무해. **canon과 비대칭**(국소 모순판정 vs 전역 약속탐색이 2패스 필요성을 가름).
- **외부 리뷰 반영** — FROZEN 게이트 거짓 0 수정(개수 게이트) + ID 중복 검사 + 결과 타임스탬프 보존(planning·design).
- **specQA 채점기 출범·실콜** (specqa-214057/214932) — 검출 아닌 *격리(분류)* 과제. 기본 exact 0.5,
  fp 0(금지된 합의채점 흉내 안 나타남). 유일 오류는 혼합 기준 C6를 미학으로 흘린 fn.
- **specQA hard 실콜** (specqa-220612/220910) — fp 함정("3단계"·"일관" 등 구체어 위장) 안 먹힘(fp 0),
  순수 원자화 캐논 recall 1.0 → **C6 미스 = 혼합 기준 탓 확정.** 격리는 1패스 충분, soft spot은 계약 원자화 몫.
- **specQA 생산자 출범** (키0) — specqa.py(design 거울): 아웃라인 → 씬 계약. 기준 원자화 + kind 태깅으로
  혼합 기준을 *생산 단계에서* 차단. contract.json(kind 제거)+cases.json(golden) 산출. replay에서 혼합 기준을
  리뷰어가 잡고 synth가 둘로 쪼갬 → FROZEN(scenes 3/criteria 10). 생산물→specqa_check 닫힘 루프 키0 exact 1.0.

### ▶ 다음 세션 첫 액션 — specQA 생산자 ★실콜 (사용자 go 필요)

생산자가 키0으로 FROZEN+닫힘까지 섰다. 남은 건 31B 실생산 측정.

- **★실콜**: `python specqa.py --outline runs/outline_ko --out runs/contract_ko` (없으면 design.py로 outline_ko
  먼저 생성). 측정 — (1)31B가 실제로 **원자화된** 씬 계약을 낳나(혼합 기준 C6류를 스스로 안 내나),
  (2)생산물 contract.json을 `specqa_check.py --fixtures runs/contract_ko --verify`로 채점해 **채점기 블라인드
  분류가 생산자 의도 kind(cases.json)와 합의하나.** 합의=원자화 깨끗, 불일치=혼합/오분류 잔존.
- 이게 닫히면 planning→design→specQA 3단계가 실데이터로 한 바퀴(canon-162900·design-195923의 specQA판).
- 그 뒤: NovelStudioMode 매핑상 **build**(같은 씬 병렬 초고) 또는 **integration**(캐논 게이트). 4번째 frontier.

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
