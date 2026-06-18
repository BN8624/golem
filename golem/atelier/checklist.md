# Atelier 체크리스트

## 코어 — 캐논 채점기 (frontier 1)

- [x] `auto_oracle.py` → `canon_check.py` 포팅 (캐논 위반 검출 + N시드·exact·recall·안정성·오탐).
- [x] 픽스처: `bible.json`(캐논 4규칙) + 깨끗한 초고 + 모순 심은 초고(골든 C1·C2) + `cases.json`.
- [x] 키 없는 `--replay`로 채점 배선 검증 → exact/recall/오탐 수학 정확 확인.
- [x] ★실제 31B 런(`--n 3`, atelier 11키) — **exact 1.0, 2/2 완전정확, 안정 1.0, 오탐 0** (canon-20260618-145250).
- [x] 어려운 픽스처(`fixtures_ko_hard`: 함의 위반 + 위반0 함정)로 한계 노출 — canon-20260618-170505 등.
- [x] 캐논/미학 경계 1차 결정: **검출(recall)은 한국어 함의로도 강함(C3·C6 1.0), precision(일치 방향
      판정)이 실한계**(trap "친누이"를 C2 위반으로 3/3 뒤집음). 프롬프트·few-shot 둘 다 불가역. 상세 context-notes.
- [x] rule_id 정규화 버그 픽스(`_norm_id`) + fp 진단 계측(`false_alarm_by_rule/_evidence`).
- [x] precision 한계 2패스 검증(`--verify`)으로 **깨짐**: trap 오탐 1.0→0, hard 검출 1.0 유지,
      전체 exact 1.0(canon-20260618-171503). precision은 모델 한계 아닌 단일콜 프레이밍 한계 — 검출/검증
      분리하면 풀림(콜 약 2배). **경계 재이동: precision도 기계화 가능.** 상세 context-notes.

## 자족화 (골렘 폴더 비의존 — 나중에 독립 프로젝트로 이전 대비)

- [x] 인프라 vendoring → `lib/`(config·llm·key_usage·jsonutil). golem 폴더 import 0.
- [x] `lib/config.py` PROJECT_ROOT = atelier 루트(.env·runs 따라오게). 이동성 격리 import로 증명.
- [x] 모델 정직화 — `generate("generator")`(26B)를 물려받던 것을 `ROLE="critic"`(31B='머리')로 교정.
      print도 상수 대신 `get_model`로 실제 모델 출력. **주의: 앞 1.0 런은 사실 26B였다.**
- [x] ★31B로 재실행 — exact 1.0 / 2-of-2 / 안정 1.0 / 오탐 0 (canon-20260618-150843). 정직한 31B 수치.

## planning 단계 (frontier 2)

- [x] `golem/studio/planning.py` → `planning.py` 포팅(자족 lib, 31B critic). A/B/C arm + synthesis.
- [x] 소설판 10축(동기·복선·타임라인·지식상태·세계규칙·중복인물·테마·톤·스테이크·핸드오프).
- [x] 출력 = `bible.json`(premise + canon[{id,text}]) — **canon_check 입력 모양과 일치, 루프 닫힘**.
- [x] 키 없는 `--replay`로 A/B/C·synthesize 배선 검증(BLOCKING 흡수→FROZEN, canon 5).
- [x] ★실제 31B 런(영어) — BLOCKING 12 흡수 → canon 8 → FROZEN. 한 줄 아이디어가 실제로 자람.
- [x] ★한국어 출력 — LANGUAGE 프롬프트 박음. **빈 패킷 버그 재현 안 됨: synth 11키 병렬 0/11 빈패킷
      (단발 1 + 병렬 11 = 12/12 FROZEN, canon 5~7).** 코드 수정 없이 통과 → 그때 모델/서버 일시 상태로 판단.
      진단 덤프(`_synth_raw.txt`)는 안전망으로 유지(실패시만 작동, 무해). 측정 2026-06-18.
- [x] ★planning 바이블 → canon_check 실초고 채점 end-to-end(한국어, `fixtures_ko/`, canon-20260618-162900):
      clean exact 1.0/오탐 0, violation C1·C2 모두 1.0. **패러프레이즈 모순(왼손 고삐·피 안 섞인 남남)도 검출.**
      → frontier 1·2가 한 줄→바이블→채점으로 닫힘.

## design 단계 (frontier 3) — setup→payoff 채점기

- [x] `design_check.py` 출범 — canon_check의 거울(모순 검출↔약속 미회수 검출). 추적 설정 목록 +
      비트시트 → 31B가 회수 안 된 설정을 짚나. 검출/검증 2패스 + N시드·exact·recall·오탐·안정성 그대로 재사용.
- [x] 심은 픽스처 `fixtures_design/`: outline.json(설정 S1~S5) + 클린(전부 회수) + 미회수(S2·S4 떨굼,
      골든) + cases.json + replay_demo.json. 미회수는 *언급은 하되 회수만 안 함*(노골적 부재 아님).
- [x] 키 없는 `--replay`로 채점 배선 검증 — exact/fp/fn/recall/안정성 수학 정확(`[S4]`→`S4` 정규화 포함,
      일부러 흔든 시드가 exact 0.67·S4 recall 0.667로 구분됨). design-20260618-192236.
- [x] ★실제 31B 런(`--n 3`·`--verify`) — design-20260618-193115/193408: exact **1.0**, S2·S4 recall 1.0,
      2패스도 1.0 유지(과교정 없음). 단 1패스가 이미 완벽해 2패스 측정 가치 0(canon hard2와 동일 상황) →
      어려운 픽스처 필요.
- [x] 31B 핀 가드 — canon_check·design_check 실콜 경로에 `GENERATOR_MODEL`·`CRITIC_MODEL`=31B 핀 +
      `ROLE!=critic` 가드. 26B 전수조사 호출 0 확인 뒤 잠복 위험 차단. (commit f567e0a)
- [x] design 생산자 `design.py`(planning의 거울): FROZEN 바이블 → lead 비트시트 → 10축 리뷰 → synthesis.
      출력 `outline.json`(premise + setups[{id,text}]) + `beatsheet.md` = design_check 입력 모양. 31B 핀 포함.
      키리스 `--replay` 통과 — BLOCKING 2 흡수, setups 5/beats 11, OUTLINE_STATUS FROZEN.
- [x] ★design 실생산(`--bible runs/bible_packet_ko/bible.json`, runs/outline_ko) — BLOCKING 5 흡수,
      setups 6/beats 10 FROZEN. 생산물을 design_check `--verify` 채점(golden=[]) → exact **1.0**/오탐 0/
      안정 1.0(design-20260618-195923). **생산자가 setup 6개 다 회수 + 채점기 동의 = planning→design→
      design_check end-to-end 닫힘**(canon-162900의 design판).
- [x] 어려운 픽스처 `fixtures_design_hard`(정황회수 fp축 + 헛회수 fn축)로 2패스 한계 측정 —
      design-200627(1패스)/200930(2패스). **1패스가 양방향 다 깸**: subtle_clean 오탐 0(함의 회수를
      회수로 인정), hidden_unresolved S2·S4 recall 1.0(재언급-only 헛회수를 미회수로 검출). 2패스도 1.0
      유지(과교정 없음). **canon과 비대칭 — canon은 precision에 2패스 필요, design은 1패스부터 강함.**
      단 이 두 함정으론 한계 미도달(더 센 함정 필요). 상세 context-notes·HANDOFF.
- [x] hard2 `fixtures_design_hard2`(오회수·부분회수 = 가짜 payoff)로 한 번 더 밀기 — design-202038/202419.
      misattributed(던져탈출·복수처럼 쓰이나 정체/명령자X) recall 1.0·2패스 과교정 0, partial(4/5 조각)
      recall 1.0. **4축(정황회수·헛회수·오회수·부분회수) 모두 1패스 robust. 잠정결론: setup→payoff는
      31B 1패스로 충분.** 남은 미시도: 장거리·setup충돌(후자는 canon 범위). 상세 context-notes.

## 외부 리뷰 반영 (계약 동결 토대 점검)

- [x] (리뷰 1) **FROZEN 게이트 거짓 수정** — `resolved=bool(decisions or assumed or deferred)`는 BLOCKING
      여럿 중 하나만 답해도 통과 + STATUS가 미해소 0 거짓보고. 개수 게이트(흡수≥BLOCKING)로 교체, STATUS
      실제 미해소 수. planning·design 동일. 단위테스트+회귀 통과. (commit 1095172)
- [x] (리뷰 2) canon/setup ID 중복 검사 추가 — frozen 조건에 `and not dup_ids`, STATUS 보고.
- [x] (리뷰 5) planning 결과 타임스탬프 보존 — `planning-{stamp}.json` + `planning_result.json` 포인터.
- [ ] (리뷰 3) evidence 실문장 근거 검증 — 우선순위 낮음(채점 정확도 무관). 보류.
- [ ] (리뷰 4) 생산·검증 독립화 — 26B/사람 표본 비교 측정설계(코드수정 아님). 보류.
- [ ] (리뷰 6) vendoring 분기 — atelier 독립이전 시점 정리. 보류.

## specQA 단계 (frontier 4) — 캐논/미학 격리 채점기

- [x] `NovelStudioMode.md` specQA 행 읽음 → **분류(격리) 과제**로 확정(검출 아님): 씬 계약 기준을
      캐논(검증가능)/미학(검증불가)으로 가르기. "초고 검증"은 build/integration 범위라 제외. 상세 context-notes.
- [x] `specqa_check.py` 출범 — canon_check·design_check의 형제(검출↔격리). 입력=premise+씬 기준목록,
      출력=31B가 캐논이라 라벨한 집합, 골든=심은 캐논 ID. detect/verify 2패스·N시드·exact·recall·fp·안정성
      기계 재사용(`verifiable`/`criterion_id`만 다름). **fp(미학→캐논 오라벨)=금지된 합의채점 흉내라 핵심
      측정축**, 보수적 기본값 "의심되면 미학". 31B 핀+ROLE 가드 포함.
- [x] 심은 픽스처 `fixtures_specqa/`: contract.json(scene_mixed C1·C3·C4·C6=캐논/C2·C5=미학 +
      scene_aesthetic 전부 미학) + cases.json(골든 [C1,C3,C4,C6]·[]) + replay_demo.json. 후자는 design
      clean(빈 골든)의 거울이되 반대 실패(검증가능 지어내기)를 잼.
- [x] 키 없는 `--replay`로 채점 배선 검증 — specqa-20260618-214057: scene_mixed exact 0.667(흔든 시드
      C4누락+C2헛라벨), C4 recall 0.667·나머지 1.0, fp 0.33. scene_aesthetic exact 0.667(C1 헛라벨),
      "(전부 미학 계약)" 출력. fp 진단 계측도 결과 JSON에 기록. 일부러 흔든 시드가 구분돼 수학 신뢰됨.
- [x] ★실제 31B 런(`--n 3` 및 `--verify`) — specqa-20260618-214932(1패스)/215325(2패스): **둘 다 동일**
      exact 0.5·안정 1.0·**fp 0**. **scene_aesthetic exact 1.0 — 전부 미학 계약에서 검증가능을 하나도
      안 지어냄(금지된 합의채점 흉내 방향이 0, 핵심 성공).** 유일 오류는 scene_mixed의 C6(적대자/우호적
      묘사 금지)을 안정적(3/3)으로 미학으로 흘린 fn — 안전한 방향(과격리). **2패스 측정가치 0이되 canon과
      이유가 다름**: verify는 fp(과대주장) 억제용인데 specQA 오류는 fn(과소주장)이라 verify가 구조적으로
      못 건드림(과교정도 0, C1/C3/C4 유지). 경계는 *혼합 기준*(사실+톤)에 있다. 상세 context-notes·HANDOFF.
- [x] 어려운 픽스처 `fixtures_specqa_hard` 심음 — scene_fp_trap(미학을 구체어로 위장: "3단계 점층"·
      "톤 일관"·"고르게 배치"·"이음매 없이", 골든 []) + scene_atomized(순수 원자화 캐논: 등장·S2회수·
      타임라인·왼팔연속성, 골든 전부). 키0 replay 통과 — fp_trap 오탐 1.00·exact 0.33(fp 유발 확인),
      atomized exact 0.67·C4 recall 0.667(흔든 시드 구분). 채점 수학 신뢰.
- [ ] ★실콜(`--fixtures fixtures_specqa_hard --n 3` 및 `--verify`) — **사용자 go 뒤에만**. 측정:
      (1)fp_trap에서 1패스가 구체어 위장에 낚여 fp 내나 + **2패스가 그 fp를 깎나**(canon precision판 검증),
      (2)atomized 순수 캐논 recall 1.0이면 C6 미스가 혼합 기준 탓이란 가설 확정.
- [ ] specQA 생산자(planning/design 거울) — 그 뒤. FROZEN 아웃라인 → 씬 계약 산출.

## 이전 (frontier 2 마무리)

- [x] 2패스 스트레스 픽스처 `fixtures_ko_hard2/3` `--verify` 비교 측정 완료 — 과교정 없음 확정 +
      통사적 부정 한계 발견. HANDOFF·context-notes 참조.
- [ ] 캐논 원장 누적(p0..p4 단계적 확장).
- [ ] 어려운 캐논 픽스처로 채점기 한계 깨기(경계 확정).
