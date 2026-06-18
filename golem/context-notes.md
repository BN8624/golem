# golem 컨텍스트 노트 (결정 + 왜)

## G1 — 정체성: Claude 사용량 절감용 게임 룰엔진 오프로드
ARAG 본체(무료모델 frontier 연구)와는 별개의 실용 도구다. gemma가 손(구현), Claude가
머리(조율). 목적은 사용자가 Claude를 쓸 때 Claude를 덜 닳게 하는 것.
왜: 사용자 결정(2026-06-16). 연구 정체성 논쟁은 빠지고 실용 도구로 합의.

## G2 — 그릇 = JS/TS 웹 (Godot 아님)
근거: gemma 강점=Python/JS, 약점=GDScript. 사용자=폰 작업·판단 → 웹=즉시 플레이.
장르=로직중심 → 웹 적합. 출처: Gemma4 모델카드(HumanEval/MBPP=Python, 강점언어 Python/JS/SQL),
저자원언어 서베이(arxiv 2410.03981), godot-dodo(GDScript는 파인튜닝 필요), MultiPL-E(GDScript 미포함).
→ GDScript 천장을 재는 대신 강점언어로 비껴간다.

## G3 — Phase 1 = 스케줄러부터 (제일 어려운 것 먼저)
ARAG 실측: 난이도=창발적 통합, frontier 벽=틱/속도게이지 턴 스케줄러(T-000012, 단일≈1/3, cracked@2).
de-risk 원칙: 벽을 먼저 치면 뚫림/한계를 싸게 배운다.

## G4 — 격리: Phase 1은 host node + 타임아웃 (docker-node는 나중)
생성물=순수 계산 스케줄러(네트워크·FS 불필요)라 host node + 타임아웃 + temp dir로 충분.
ARAG 본체는 docker 격리(docker_gate) — golem도 멀티 시스템 통합 단계 가면 docker node로 격상.
node 미설치 시: docker node 이미지로 대체.

## G5 — 오라클: ARAG 트레이스diff 철학 재사용
골든 = 레퍼런스 구현이 뱉는 seed→트레이스(모델 비노출). 게이트 = 정확일치 diff(콜0).
자가수정 = 첫-발산 위치 힌트(ARAG 결정27의 JS판).

## G6 — 스파이크 범위 = 전투엔진 통째(스케줄러 단독 아님), 4 고정 시나리오
game/ 읽어보니 스케줄러 난이도가 상태이상·콤보와 분리 불가(타이밍 상호작용이 곧 난이도).
그래서 T-000012와 동일하게 *전투엔진 전체*를 JS로 재구현, 4 고정 시나리오(winner/turns/엔티티HP
정확일치)로 채점. RNG(파티생성)는 워커 범위서 제외(시나리오=고정 파티 입력) → CPython RNG
재현이라는 불공정 짐 없음. 골든은 game/로 공짜 생성(make_golden, 4/4 일치 검증). T-000012(파이썬
cracked@2)와 사과-대-사과.

## G8 — A 방식(Claude 레퍼런스 오라클)이 처음 보는 게임에 일반화됨 (2026-06-16)
golem을 일회성 데모에서 도구로: 검증엔진을 카드로 쌓는 은행(game_bank.sqlite) + A 오라클
(oracle.py — JS 레퍼런스→골든, game/ 의존 제거). 새 게임은 정답이 없다는 문제를, Claude가
레퍼런스 1벌 짜서 골든 생성으로 푼다. 검증: 카드#2 결정적 2048을 A로 적재 → 생성 런
**cracked@4, 11/11 전부 통과**(전투 카드 5/11보다 깔끔). 새 게임이 입출력 스키마(전투 전용
winner/turns/hp)를 강제로 일반화시킴 → 골든=평면 key:value 정확일치(전투·퍼즐 한 틀).
교훈 재확인: 규칙(RULES)이 레퍼런스를 빈틈없이 명세하면 싼 모델도 처음 보는 게임을 맞춘다
— frontier는 모델이 아니라 계약 정밀도에 있다. 다음 = 확장 루프(베이스 카드 + 메카닉 추가).

## G9 — 확장 루프 됨 + Phase 4 방향: 자율 오라클 (2026-06-16)
3단계 확장 루프 검증: 통과한 merge-2048 solution을 워커에 컨텍스트로 주고(driver --base) "벽 메카닉
추가" → cracked@7 11/11. 통과본이 board.js를 베이스 그대로 두고 moves.js만 벽 세그먼트화 = 맨바닥
재작성 아닌 진짜 재사용/확장. 은행이 베이스로 쓰일 때 확장이 싸게 됨을 입증.
**Phase 4 제안(사용자)**: 지금은 Claude가 오라클(레퍼런스+규칙+시나리오)을 손수 짠다 = 사실상 설계.
golem 목적이 Claude 절감이니 그 설계도 31B에 넘기자(주제+골든 최소규격만 Claude가). 핵심 리스크 =
**오라클 신뢰**: 출제(레퍼런스)와 응시(후보)가 같은 모델이면 상관된 오류로 가짜합격 가능. 해결 =
오라클도 게이트 통과 — 독립 gemma K개가 *규칙만* 보고 재구현해 골든에 합의하면 규칙이 정답을
명확히 담았다는 증거(레퍼런스 자의성 배제) + 그게 통과본. 합의 낮으면 규칙 모호 → 31B 재설계.
= select-best/출제·응시 분리 정신을 오라클 생성에 적용. 끝점 = 주제만 주면 도는 자율 게임 생성기.

## G10 — 자율 오라클 작동 입증: 31B가 오라클 설계 + 독립 합의로 신뢰 보증 (2026-06-16)
Phase 4 = 오라클(규칙+레퍼런스+시나리오) 생성 자체를 31B에 넘김(oracle_design.py). Claude는
메타규격(META: 평면 key:value·결정적·멀티파일·stdin금지·레퍼런스 의무)만 줌. 오라클 신뢰 리스크
(출제=응시 같은 모델 → 가짜합격)는 **합의 게이트**로 해소: 독립 gemma가 규칙만 보고 재구현해
레퍼런스 골든과 합의하는 비율 = 신뢰 점수. 검증: theme=Snake → 31B 첫 시도에 규칙 2342자+2파일
레퍼런스 설계, 합의 게이트 **10/11**(실패 1은 출력형식 실수). 죽는 시나리오·내가 짚은 head_pos
모호점도 합의 안 깸. → 자율 오라클 끝까지 작동. 신뢰 임계 데이터: 명확한 자율오라클이면 합의 매우
높음(10/11), 앞선 사람-오라클들(2048·벽 11/11, 전투 5/11)과 같은 결 — 합의율이 곧 규칙 명료도/
난이도 지표. 다음(Phase 5) = 랜덤 주제 대량 캠페인으로 합의율 분포 측정 = 무료모델×자율오라클
한계 지도. 주제 출처 미정(Claude 풀 vs 31B 자율).

## G13 — 부품 추가 시 시연 필수 (사용자 규칙, 2026-06-16)
부품0·1을 합의율(11/11)로만 보고하니 사용자(바이브코더)가 "눈으로 되는 걸 봐야 판단한다" →
**부품이 게이트를 통과하면 시연을 반드시 만든다**(숫자로 끝내지 말 것). 시연 = 통과본을 시나리오에
돌려 사람말 요약 + 격자 시각화(`@`=플레이어 `E`=적 등). 시연도 도구로 굳혀 부품마다 재사용(목표②,
손으로 다시 짜지 말 것). 규칙 정본 = CLAUDE.md "부품 추가 시 시연 필수". 방향 = G11.

## G12 — 타워디펜스 0/11 = 모델 아닌 계약 정밀도 (Claude 정밀화로 0→7/11, 2026-06-16)
Phase 5에서 타워디펜스만 0/11 완전 실패. 1원칙대로 오라클부터 의심 → 장부 발산 해부:
실패가 3갈래(크래시 5, 출력형식 kills=None 3, 로직불일치 kills=0·ticks=2 3)였고 단일 버그
아님. 손 트레이스로 시나리오1·2·3 골든을 만족하는 일관 해석 확인 → 31B 자율오라클 규칙이
**틱 종료 타이밍을 안 못박음**(종료를 currentTick +1 *전*에 판정하나 후에 판정하나 = off-by-one;
종료조건 "웨이브완료 AND 적0"의 AND 누락). **실험(단일변수)**: 골든 그대로 두고 규칙에만 실행
의미(루프 의사코드 + 종료조건 BOTH 명시 + ticks 정의 + 시나리오1 워크드 트레이스)를 덧붙인 카드
`auto-towerdef-tight`(`bank_add_towerdef_tight.py`, 골든동일 검증) → 같은 gemma 11개 재측정 =
**0/11 → 7/11 cracked@5 $0.019**. 겨냥한 로직불일치 3개가 **전부 0**(사라짐), 크래시 5→1. 잔여
실패 4 = 출력형식(kills 줄 미출력) — 틱로직 아님, 출력계약 예시로 잡을 다음 레버. **결론**: frontier는
모델능력이 아니라 계약 정밀도(반복 교훈 재확인). = 부품공장×시공자([[golem-direction]] G11)의 첫
하드 증거 — 시공자(Claude) 정밀화가 같은 부품공장(gemma)의 0을 7로 연다. 목표② 재사용 레시피
확보: "장르가 막히면 센 모델 말고 *실행의미 못박기 + 워크드 트레이스*" = 템플릿화 후보.

## G11 — 본 방향 확정: 부품공장×시공자, 목표=로그라이크, 개입최소화 2목표 (2026-06-16)
사용자가 프레임 교정: golem은 "작은 게임 통째 자율생성"이 아니라 **큰 게임 하나를 부품을 붙여
점점 키우는 것**이다. gemma=부품공장(결정적 룰엔진 부품), Claude=종합시공자(발주=계약작성 +
조립=계약대로 맞물림 + 갭메움=gemma가 못하는 부분 직접). = Phase 3 베이스주입(2048→2048+벽)의
일반화. **목표 큰 게임 = 턴제 로그라이크**(사용자 선택; 부품쌓기 교과서·결정적이라 골든채점 궁합·
바이브코더가 사람말 로그로 판단 가능). 발주 순서: 부품0(격자+결정적 이동)→적→전투→아이템→층이동→
시야·함정·적 다양화. **두 목표**: ① 일단 한 번 끝까지 만들며 Claude 손이 꼭 필요한 지점 실측 →
② 그걸 반복가능 패턴·도구로 굳혀 **Claude 개입을 점점 깎는다**(발주서→템플릿, 조립확인→정적게이트
콜0, 반복 갭메움→부품 사양 선반영). 부품당 Claude 콜·손댄 횟수 = 측정 지표(줄면 성공) = golem 본
목적(Claude 사용량 절감)의 실행형. 측정 재해석: Phase 5 합의율 = 통짜게임 신뢰도가 아니라 **부품별
gemma 신뢰도 지도**(높은 메카닉=발주만, 낮은=Claude가 메움). 새 핵심 미측정축 = **조립 가능성**
(부품 둘 이상이 계약대로 맞물리나).

## G7 — 드라이버 = 키 11개 병렬 select-best (워커=키), 독립 시도
처음 단일키 순차로 짰다가 사용자 지적(2026-06-16) — 키 11개는 RPM 쿼터가 각각 독립이라 병렬=11배.
arag select_run 패턴(KeyPool.checkout + ThreadPool, 첫 통과 시 미시작 취소) 채택. 시도는 독립
(self-fix 없음) = T-000012 병렬 select-best와 동일 모드. self-fix 웨이브는 옵션으로 미룸.


## G14 — 큰 걸음 검증: 4메카닉 동시도 31B가 쉽게 소화 (2026-06-16)
부품3에서 아이템·함정·계단·포션을 한 카드로 묶어 발주 → cracked@10, 11/11 통과($0.023). 캠페인이
frontier로 본 "여러 시스템 동시 맞물림"이 이 규모(턴제 격자)에선 안 막힌다. 단일 메카닉 부품은 너무
쉬워 비효율 → 사용자 결정으로 앞으로 큰 걸음(여러 메카닉/한 부품). 단일메카닉 cracked는 p0@4·p1@3·p2@10.

## G15 — 스케일은 출력토큰이 첫 천장(입력 아님), 측정 내장 (2026-06-16)
gemma는 상태없음(파일 못 읽음) → 베이스를 프롬프트에 주입(입력). 입력 TPM 무제한이라 안 막힘. 진짜
벽은 출력 32k(thinking 포함). 현 구조는 통째 재생성이라 게임 크면 출력도 통째로 커짐. 드라이버에 토큰
측정 내장(attempt·요약별 input/output/thinking, out+think vs 32k). p3 실측: 입력3896 / 출력코드~2132 /
thinking~3379 / out+think 최대 6619=20%. 여유 크나 어려운 부품서 thinking 부풀면 닿음. 사용자 지적.

## G16 — 완전 재설계: 엔진 모듈화 + 파일별 생성 (2026-06-16)
G15 해소. 사용자가 "완전 재설계" 택. ①엔진 6모듈: dungeon/chase/combat/items=안정·재사용(한번 쓰면 안
바뀜→재출력 안 함), engine=얇은 오케스트레이터+main. rogue-p3.solution을 모듈 베이스로 교체(골든 PASS,
bank_remodularize_p3.py). ②파일별 생성: 워커는 바뀐/새 파일만 출력, driver _one_attempt가 베이스+변경분
병합(안 낸 파일은 베이스서 채움). --replay로 검증(engine+main만 응답→나머지4 병합→PASS). 효과=부품당 출력이
전체 크기와 무관. 리스크(미검증): 모듈 추상화로 gemma 크랙률↓ 가능 → 부품4 키 발주로 확인 예정. 데모는
card.reference(모노) 사용이라 무영향.


## G17 — 재설계 검증: 모듈+파일별 생성이 스케일 해법으로 입증 (2026-06-16)
부품4(장비=무기·방어구·회복제단)를 모듈 베이스(rogue-p3) 위에 발주 → 11/11 cracked@10($0.020). 두 검증:
①gemma 11시도 전부 바뀐 4파일만 출력(combat·items·engine·main), 안정모듈(dungeon·chase)은 안 냄→
드라이버가 베이스서 병합. ②출력 토큰 감소(p3 ~2132 → p4 ~1937)인데 게임은 더 큼 = 파일별 생성 효과.
③모듈 추상화로 크랙률 안 떨어짐(G16 리스크 해소). 결론: 부품당 출력이 전체 크기와 무관 → 무한 확장
경로 확보. 앞으로 부품은 이 구조로 그대로 쌓는다(bank_add_roguelike_pN + driver --base 직전부품).


## G18 — gemma를 머리로: 자율 설계+자기 오라클, 합의로 검증 (2026-06-16)
사용자 직감("gemma 제대로 못 쓴다") 검증·확정. 원인 진단: 작음은 gemma 한계가 아니라 ①우리 정확일치
골든(손으로 못 쓰면 출제 못 함→작은 증분) ②소심한 주문. 설계 프로브(design_probe.py, 1콜): 야심 주문
주니 31B가 4개 맞물리는 시스템(LCG 절차생성·원소환경·상태이상·적 상태기계) 설계 — 결정성까지 스스로
챙김(고정 순회순서, Object.keys 회피). 새 작업방식 입증: oracle_design_ext.py = 31B가 베이스 위 원소
레이어를 [규칙+시나리오+레퍼런스] 자율 설계(out+think 8.6k=부품 4배), 레퍼런스로 골든 자가생성. 검증=
driver --card rogue-elem --base rogue-p4 → 독립 빌더 11/11 합의(cracked@3, $0.023), 전원 3파일만 출력
(파일별 생성 유지). **Claude는 규칙·시나리오·레퍼런스·골든 0줄**(브리프+베이스+형식만). 결론: gemma를
손→머리로 올리고 오라클을 자가설계+합의로 풀면, gemma 진짜 추론을 쓰고 Claude 개입은 실제로 급감(②).
self-bias 방어=빌더는 규칙만 보고 독립 구현→골든과 일치해야 함(규칙 안 따르는 골든오류는 불일치로 걸림).
미완: rogue-elem 시연(데모툴이 모듈 run(sc) 시그니처+grid 필드 미지원 → 데모 확장 필요).


## G19 — 정적 게이트 + 실행 격리 복원 (2026-06-17)
ARAG 무거운 파이프라인(정적게이트·도커·비평루프) 중 golem이 덜어낸 것 사용자 확인 후 핵심만 복원.
도커는 원래 없었음(golem은 node 직접 실행). 추가: static_gate.py(콜0) = node --check 구문 / require
그래프 도달성(고아 모듈=멀티파일 위장 차단) / npm 금지(빌트인·상대경로만) / Math.random 금지. grade.py
실행을 Node 권한모델(--permission --allow-fs-read=*)로 격리: 파일쓰기·자식프로세스·워커·네이티브 차단
확인(ERR_ACCESS_DENIED) + stdin DEVNULL. Docker 없이 호스트 격리. driver·oracle_design_ext가 채점/골든
생성 전 정적게이트 강제. 남은 공백: 네트워크는 권한모델이 안 막음(규칙·무npm으로 커버), required-but-unused는
미검(도달성만). 정확일치 오라클+합의가 여전히 주 게이트.

## G20 — 생산 분할(계층적 분해+인터페이스 계약) = 다음 프론티어 (2026-06-17, 사용자 아이디어)
관찰: 출력토큰 아직 ~8k(32k의 25%), 2-3배 여유. 사용자 제안: 병렬을 합의용으로만 쓰지 말고 *생산 자체*를
쪼개자 — 설계자가 전체를 A·B·C 모듈+계약으로 설계 → 모듈별 독립 빌더 분배 → 재귀 분할 → 조립. 효과:
①무한 크기(전체=Σ모듈, 각 모듈은 자기 32k 안에서만 → 출력천장 구조적 소멸) ②조립 가능성 직접 측정
(golem이 G6에서 못 잰 핵심 축) ③오케스트레이션 novelty(무료모델×오케 frontier 그 자체). 현 select-best와
차이: 같은 전체 중복생산이 아니라 다른 부분 생산→합침. 핵심 linchpin=인터페이스 계약 정밀도(모호하면 조립
실패=프론티어 데이터). 계획=Step1 PoC(설계자 manifest 확장 + 분배기/조립기 신규, --replay로 키없이 먼저),
Step2 모듈별 합의, Step3 재귀 분할. 착수 합의됨(다음 세션 시작점).

## G21 — Golem Studio Mode 문서 수정 방향 (2026-06-17)
사용자 판단: Golem Studio Mode 핵심은 유지하되 첫 구현 범위를 대폭 축소. 11개 Auth Key는 독립 인격이 아니라
역할별/관점별 `worker slot`으로 재정의한다. 다양성은 키 자체가 아니라 review_axis, temperature, 출력양식,
금지사항, 리뷰 기준에서 만들어야 하며 duplicate_issue_rate와 unique_issue_count로 측정한다. v0.1은 전체 스튜디오가
아니라 Contract Microkernel Replay로 제한한다: fake planning packet, module_manifest schema, fake build output,
import/export validator, static_gate bridge, replay report. 문서에는 질문 등급(BLOCKING/ASSUMED/DEFERRED),
변경 등급(L0~L4), DEPRECATION_REQUEST, Spec QA/Adversarial QA, JSON traceability 정본, 실패 분류별 롤백 기준을
반영한다. 과제는 산으로 가지 않게 문서 정정에 한정한다.

## G22 — Golem Studio v0.1 pending 기본값 (2026-06-17)
추가 판단: 남은 문제를 전부 상세 설계로 확장하면 문서가 다시 비대해지므로 `Pending Decisions / Known Open
Problems` 섹션으로 분리한다. 단 구현을 막는 항목은 v0.1 기본값을 고정한다. JS 모듈은 CommonJS only,
manifest는 `schema_version/module_format/entry/files[].path,exports,imports`만 사용, static_gate bridge는
`workspace_path`와 `manifest_path` 입력 및 `ok/checks/errors/warnings` 출력으로 고정한다. A/B/C 비교 기준은
임시값으로 둔다: B는 A 대비 unique_issue_count +30%, C는 B 대비 +20% 또는 추가 BLOCKING issue 1개 발견 시
유효. 10회 이상 실행 후 조정한다.

## G23 — HANDOFF 선회: 생산 분할 폐기, Contract Microkernel 우선 (2026-06-17)
사용자 지시: 기존 HANDOFF의 생산 분할 Step 1 예정분은 폐기하고, Golem Studio Mode 문서 방향으로 선회한다.
다음 작업은 11 worker slots 투입이나 분산 빌드가 아니라 v0.1 Contract Microkernel Replay다. 이유는 구현
시작 전에 module manifest와 실제 CommonJS 코드의 파일/export/import 계약을 기계적으로 검증할 수 있어야
역할 순환 구조가 무너지지 않기 때문이다. CLAUDE.md는 golem 폴더 전체 지침으로 유지하되, Golem Studio 구현
범위에서는 GolemStudioMode.md와 HANDOFF.md를 우선하도록 보강했다. CommonJS, npm 금지, Math.random 금지,
사용자 go 없는 키 런 금지는 기존 CLAUDE.md와 충돌하지 않는다.

## G24 — 문서 역할 축소 정리 (2026-06-17)
사용자 지시로 golem 문서 역할을 좁혔다. HANDOFF.md는 현재 위치와 다음 액션만, CLAUDE.md는 작업 규칙만,
GolemStudioMode.md는 새 설계 정본, context-notes.md는 결정 로그, checklist.md는 현재 활성 체크리스트를
맨 위에 두고 과거 Phase는 히스토리로 둔다. README.md는 전체 내용을 삭제하고 "개인 프로젝트 임."만 남겼다.

## G25 — Golem Studio v0.1 Contract Microkernel Replay 구현 + 사전 반박 (2026-06-17)
사용자가 "구현 전 반박부터" 요구 → 핵심 이견 정리. ① "11 slot 역할 순환"은 slot이 상태없는 샘플러라
메커니즘상 무의미한 포장(키=병렬성일 뿐), 진짜 substance는 Ambiguity Review+Traceability+FROZEN 계약.
② 헤드라인 11과 §15 실제 기본값 3 충돌 + 본체 결론(분해=차이없음, select-best가 해법)과 긴장 →
A/B/C 비교를 전체 파이프라인 짓기 전에 먼저 측정해야. ③ PENDING-002 bare-default 금지는 Step2에서
실제 gemma 코드를 거를 수 있음(의식적 결정 필요). v0.1 방향 자체(키X 계약 검증부터)는 옳음.
사용자 결정: 폴더는 src/ 유지+확장 래칫 대비, 음성 픽스처 포함.
구현: golem/studio/ 신설. contract_validator.py(checks 4종 manifest_schema/file_exists/import_export/
static_gate, PENDING-003 I/O 계약), replay.py, schema, 픽스처 5종(통과1+음성4: export불일치·파일누락·
순환·bare default). 픽스처는 fixtures/(runs/는 .gitignore라 추적 안 됨 — Step2+ 생성물용으로 비움).
static_gate.py를 rglob+경로해소로 확장(하위호환 — 평면 require는 그대로).
검증: replay 5/5 통과(API 0회), static_gate 무회귀(기존 merge-2048 attempt04 ok:true 유지, 신규 src/
워크스페이스 ok:true). 왜 이렇게: validator는 valid 입력만 보면 미검증이라 음성 픽스처로 "이빨" 증명.
다음(키 필요, go 대기): Step 2 Planning 팀만 실제 worker slot, 단 A/B/C부터 측정.

## G26 — Step 2 Planning A/B/C 측정 하니스 (키X replay 검증, 2026-06-17)
사용자 "고" → Step 2 진입. 프로젝트 검증된 2단계 패턴(준비=키X replay → 별도 go로 실발사) 유지.
이번엔 G25 권고대로 전체 6단계 짓기 전에 **Planning 한 단계 A/B/C부터** 측정하는 하니스만 만들었다.
핵심 설계결정: **A안 = lead 자기검토(self-review)**로 정의. 본체 핵심원칙(출제자=채점자 분리, self-grading
bias)에 맞춰 A/B/C가 정확히 "독립 리뷰어가 self-review를 이기나"를 측정하게 함. B=1+3, C=1+10(§15).
재사용: llm.py(LLMClient/KeyPool, 키별 페이서·429백오프·RPD 회계), driver의 키병렬 패턴. 31B=critic 역할.
구현: planning.py — arm별 run, 리뷰어 ThreadPool 키병렬, dedup 메트릭(unique_issue_count/duplicate_issue_rate/
blocking_count), §19 PENDING-004 판정(B>A +30%, C>B +20%). 스키마=§6, 10축=§2.2. fake/real caller 분리.
검증: fixtures/planning_demo/fixture.json(의도적 중복 포함)으로 replay → A2<B6<C12 unique, dup 0.077,
BLOCKING은 리뷰어에서만 1, API 0회. **plumbing 증명일 뿐 — 데이터 가짜, 리뷰어 실효는 실키 측정에서 갈림.**
다음(★키, go 대기): `planning.py --idea "..."` 실측 1회 → 독립리뷰 실효·reviewer 기본개수 판정.

## G27 — Planning A/B/C 첫 실측: 방치형게임 (2026-06-17, 키 씀)
사용자 아이디어="방치형게임"(틱 자원축적+업그레이드, 결정적 CLI로 적합). 31B 실호출.
결과: A(self) unique 6/blocking 3 → B(1+3) 11/6 → C(1+10) 27/12. B>A gain 0.83(≥0.30✓),
C>B gain 1.46(≥0.20✓). **둘 다 PENDING-004 임계 통과 = 독립리뷰가 self-review를 이기고, 10이 3을 이김.**
이슈 품질 진짜: 부동소수점 반올림(costMultiplier^level=float → 결정적 정확일치 깨는 1순위)을 리뷰어
여럿이 독립으로 잡음, '^' XOR/지수 해석 모호, 실패액션 처리(halt vs skip), 잘못된 scenario/upgrade id
처리, 최종상태 출력형식 등 — 전부 오라클 깨는 실질 모호성. self(A)는 일부만 잡음.
→ **G25의 내 회의(리뷰어 구조=죽은무게?)에 반하는 첫 실증거.** 단 두 caveat: ① N=1(§19는 ≥10 요구),
② dedup이 문자열정규화라 의미중복 못 잡음 → 같은 float반올림 이슈가 표현만 바꿔 여러 unique로 과대계상.
즉 방향(리뷰어 도움됨)은 신뢰, 크기(27 등)는 부풀려짐. 콜 비용=AI Studio 무료(api_calls 정밀집계 미연동).
다음 선택지: (a)아이디어 더 돌려 N 쌓기 (b)dedup 의미기반 개선 (c)synthesis로 진행(lead가 BLOCKING→0
정리+contract_packet). 권고=(c) 먼저(구조 실효는 정성적으로 충분히 확인) 또는 (b)로 측정 신뢰 먼저.

## G28 — Planning synthesis 실측: 방치형게임 계약 FROZEN (2026-06-17, 키 씀, 사용자 (c) 선택)
planning.py에 synthesis 추가: 초안→리뷰어10→lead가 이슈 흡수해 BLOCKING→0 + 계약 패킷(§4 핵심) 굳힘.
fake replay 검증(BLOCKING1→흡수→FROZEN) 후 실발사. 결과: 방치형게임 리뷰어 BLOCKING 11개 →
decisions 9/assumed 3/deferred 2로 전부 흡수 → 미해소 0 → **CONTRACT_STATUS: FROZEN**.
핵심 성과: 리뷰어가 잡은 부동소수점 모호성을 계약이 못박음 — **RULE-03 currentCost =
floor(baseCost*(costMultiplier**level))**. 그 외 WAIT만 턴증가, 잘못된 id 로그+스킵, energy>=1000 승리,
WON후 액션무시, 잘못된 scenario exit(1) 등 결정적 정확일치 깨던 모호점 전부 닫음. interface_contract=
2파일(main.js+engine.js, v0.1 validator의 module_manifest와 동형 → 그대로 물림), acceptance 3.
산출물: golem/studio/planning_packet/(concept/gdd/ambiguity_review/contract/acceptance_tests/questions/STATUS).
→ Golem Studio thesis(역할순환 리뷰→모호성 없는 FROZEN 계약) 실물 산출. caveat: acceptance expect가
아직 산문(정확값 아님) — golden 정확일치는 Build/오라클 단계 몫.
다음 후보: Build 단계 = FROZEN 계약을 기존 driver.py 11키 select-best에 줘 gemma 구현 → static_gate +
v0.1 contract_validator(매니페스트 정합!) + grade. 단 grade는 golden 필요 → 오라클(A방식/31B 레퍼런스) 연결 필요.

## G29 — 측정 신뢰 보강: dedup 어휘 클러스터링 + 결론 강건성 (2026-06-17, 키X)
사용자 "측정보강 나중에????" 지적 → 옳음. 게임은 도구, 측정이 본질. Build보다 측정 신뢰부터.
dedup을 정확일치 문자열 → 토큰 Jaccard 클러스터링(th=0.5, stdlib only, 불용어 제거)으로 교체.
정직한 한계: G27 실데이터 재측정 시 C 27→25(th0.5)밖에 안 줄음. 부동소수점 이슈가 "floating point
determinism"/"rounding method"/"rounding logic" 등 서로 다른 어휘로 ~3회 등장 → 어휘기반은 못 묶음.
진짜 의미 dedup = 임베딩(외부패키지=stdlib규칙 위반) or LLM 패스(키·다소 순환). → 보류.
핵심 발견(자보다 중요): 임계 0.5→0.4→0.3→0.25로 조여도 C 25→23→21→20. **A6 < B11 < C20~25,
gain 둘 다 임계 한참 위 — 어떤 자로 재도 방향 안 뒤집힘.** 즉 자는 부정확해도 "독립리뷰>self,
10>3" 결론은 강건. 효과 크기가 자의 흔들림보다 큼. caveat 남음: N=1(generalization 미검).
남은 측정 가치 = N≥10을 **서로 다른 장르 아이디어**로(모호한 게임 vs 명확한 게임에서 리뷰어 효과 다른가)
— 이게 §19의 진짜 목적(메트릭 정밀화 아니라 일반화). ★키 필요. 신규 run은 새 dedup 자동 사용.

## G30 — Build v0: FROZEN 계약 → gemma 구현 → v0.1 검증기 정합, end-to-end (2026-06-17, 키 씀)
사용자 "빌드로 전진". Build v0 스코프 = golden 정확일치(오라클) 보류, '계약대로 굴러가나'까지.
build.py: Planning 패킷의 interface_contract를 매니페스트로, data_contract를 규칙으로 gemma(31B critic)에
줘 멀티파일 구현 → 3중 게이트(static_gate + contract_validator 매니페스트 정합[v0.1 재사용!] + 스모크
node main.js --scenario 1 크래시 없이 key:value). fake build로 replay 검증 후 11키 select-best 실발사.
결과(방치형 계약): **cracked@4, 10/11 통과**. attempt04 검수=진짜(main 55+engine 66줄, 매니페스트대로
main.js+src/engine.js, GameState/GameEngine export). 실행: sc1 자원축적, sc2 에너지부족 처리, sc3 turn1000
WON — 규칙 실제 구현. 1실패=스모크 빈출력. **정직 caveat: 10개가 각각 다른 숫자(상수·시나리오 입력이
golden으로 미고정) → "10통과"=계약대로 굴러가는 게임 10개지 같은 정답 10개 아님. 정확일치=오라클(v1).**
의의: 아이디어 한 줄("방치형게임") → 리뷰→FROZEN 계약 → gemma 구현 → v0.1 매니페스트 정합 검증이
실모델로 한 줄에 꿰임. 처음 만든 v0.1 validator가 실 gemma 산출물에서 값을 함(설계 의도 실현).
build_runs/는 .gitignore(생성물). 다음: Build v1=오라클 골든으로 정확일치 채점 / or 측정 N≥10 장르확장.

## G31 — 순서 점검 + Step 3 Design 실행 (2026-06-17, 키 씀)
사용자 "문서 정독한거 맞아"·"처음부터 점검" 지적 → 옳음. §13 순서(1→2→3 Design→4 Spec QA→5 Build→6
Adv QA)를 어기고 1,2 후 5(Build)로 점프했었음. Build v0는 스파이크로 남기고 순서 복원.
점검서 design.py가 import 버그(_find_cycle은 contract_validator에 있음)로 안 돌던 것 발견·수정.
또 회귀 replay가 planning_compare.md를 가짜로 덮은 것 git restore.
design.py(§7·§8.2·§13 Step3 그대로): Planning 패킷 → lead 모듈분해+traceability → 리뷰어10 → synthesis
→ system_design.md/module_manifest.json/traceability.json/traceability_report.md. validator=모든 REQ가
≥1모듈·≥1테스트, manifest에 없는 파일/없는 test id 실패, 순환없음.
실행(방치형 계약): REQ6, **4모듈 분해**(utils 순수계산 ← state_manager 상태전이 ← engine 조율 ← main I/O),
각 모듈 책임·금지 명시, RULE-01~06 전부 추적연결, validator PASS, BLOCKING 2. **Build v0 통짜 2파일을
교정 — 진짜 멀티파일 분해**(프로젝트 핵심 "파일 간 정합성"). 산출=design_packet/.
다음(§13 순서): Step 4 Spec QA → Step 5 Build 재실행(이번엔 design 매니페스트+grade) → Step 6 Adv QA.

## G32 — Step 4 Spec QA: 채점가능 시나리오 초안 (결함 포함, 2026-06-17, 키 씀)
specqa.py: Planning/Design → lead가 산문 수용기준을 기계 시나리오로 + 오라클위험 표시 → 리뷰어10 →
synthesis. 산출 acceptance_tests_draft.json, oracle_risk_review.json. validator(§8.4)=모든 REQ ≥1 시나리오.
fake replay 검증(REQ6 커버, SCN-004 오라클위험 표시, PASS) 후 실행.
실행(방치형): 11시나리오, 전부 구체 입력(constants/initialState/actions)+정확 expected, RULE-01~06 커버,
validator PASS. 모델이 multiplier를 정수로 골라 float 회피→오라클위험 0(일리 있음).
**정직한 결함(점검서 발견)**: ① SCN-006 expected gameStatus "ACTIVE" — 계약엔 PLAYING뿐(모델이 없는
상태 지어냄=TEST_ORACLE_ERROR) ② RULE-03 float floor을 정수 multiplier로 테스트→정작 float 경로 미검
③ SCN-011 빈 시나리오(커버 0) ④ BLOCKING 5 떴는데 specqa 하니스가 synthesis 해소 추적 안 함(§13은 0
요구, planning은 추적했음) → 0 증명 못 함. **validator가 헐거움 — 커버리지만 보고 의미결함 못 잡음.**
사용자 결정: 초안으로 두고 Step 5 진행(draft는 Step 6 Adv QA가 다듬는 게 §11 설계, ACTIVE는 Step5
빌드-합의가 잡음). backlog: specqa validator 강화(계약 외 상태값 거부 + BLOCKING 해소 추적).
다음: Step 5 Build 재실행 — design 4모듈 manifest + specqa 시나리오 + 합의 채점(특권 golden 아님).

## G33 — Step 5 Build v1: 합의 채점이 "스펙 아직 안 빡빡"을 잡아냄 (2026-06-17, 키 씀)
build_graded.py: Build v0(2파일 스파이크)와 달리 ① Design 4모듈 manifest를 목표로, ② Spec QA 시나리오를
scenarios.json으로 공통 제공, ③ 정답을 특권 golden이 아니라 **빌드 다수합의**로 잼(사용자 산출물축소
우려 반영 — 오라클=자, not 우리). 오라클위험 시나리오는 채점 제외.
**발견1 — validator가 빌드엔 과하게 빡셈**: 첫 실행 0/11. 원인=정확-import-엣지 conformance가 멀쩡한
빌드(attempt02: 4모듈 정확, 단 main이 utils 한 번 더 import)를 거부. v0.1엔 맞지만 자유구현엔 과함.
→ contract_validator에 strict 파라미터 추가(기본 True=v0.1 정확일치 유지, 5/5 무회귀). Build는 strict=False
(선언 export는 있어야/추가 허용, 매니페스트 내부 추가 엣지 허용, 매니페스트 밖 import만 금지).
**발견2(핵심) — 합의 0.36**: 느슨 모드 재실행 3/11 게이트 통과(나머지=출력 안 함·고아 등 진짜 버그).
통과 3개도 거의 모든 시나리오에서 불일치. 원인 점검: SCN-001에서 attempt02 `gameStatus: undefined`(버그),
07 `levels:{}/productionRate:1`, 11 `gameStatus:PLAYING` — **무슨 key를 찍을지조차 제각각**. 즉 FROZEN
계약·Design·Spec QA를 다 거쳤어도 **출력 계약(정확한 key 집합·형식)이 안 박혀** 빌드가 안 모임.
**이게 합의 채점의 값**: 특권 golden 없이 "스펙이 아직 안 빡빡하다"를 정량화(0.36)+원인(출력계약 미고정) 지목.
다음: 출력 계약을 시나리오별 expected key 집합으로 못박기(Spec QA/계약 강화) → 그 뒤 합의 재측정.
Build v0(build.py)은 스파이크로 잔존. build_runs/는 gitignore.

## G34 — 한 변수 실험: 출력 계약 고정 → 합의 0.36→0.66 (2026-06-17, 키 씀)
build_graded 프롬프트에 **고정 출력계약**(정확히 4 key: turn/energy/productionRate/gameStatus, 같은 순서·
형식 + 상수는 시나리오 것 사용, 기본 gen1 명시) 추가. 한 변수만 바꿔 재측정(한 번에 한 변수 원칙).
결과: 게이트 3/11→**8/11**, 합의 0.36→**0.659**. → "계약을 빡빡하게 하면 싼 모델이 수렴한다" 방향 확인.
**단 정직 caveat — 0.66은 반쪽**: SCN-001 점검서 통과 8개가 둘로 갈림 — 절반 `turn:0`(액션 미실행),
절반 `turn:undefined`(파싱버그). WAIT 2회면 turn:2여야 하는데 **아무도 시나리오 액션을 실행 안 함**.
출력 key는 맞췄지만(→합의↑) **시나리오 입력 스키마(constants/initialState/actions가 이질적·일부 산문)가
미고정**이라 빌드가 입력을 못 읽음. 즉 합의 일부는 "기본값 우연 동의"=hollow.
다음 변수: **입력(시나리오) 스키마 고정** — scenarios.json 형식을 한 가지로 못박고 builds가 actions를
실제 실행하게 → 합의 재측정(진짜 수렴 보기). 이게 §11/§13 흐름상 Spec QA 강화 + Step6로 이어짐.

## G35 — 한 변수 실험: 입력 스키마 고정 → 합의 0.66→0.98 (2026-06-17, 키 씀)
G34의 반쪽 caveat(빌드가 actions 미실행) 원인 규명·제거. **원인 = 입력 스키마 미고정으로 액션 키 추측**:
시나리오 데이터는 `{"action":"WAIT"}`·`{"action":"UPGRADE","id":...}`인데 빌드 9개 전부 `action.type`/
`action.generatorId`를 읽음 → 어떤 액션도 매칭 안 됨 → turn:0 no-op에 다같이 모인 것이 0.66의 정체.
상수 키도 시나리오 `multiplier` vs 계약(RULE-03) `costMultiplier` 불일치.
**고친 것(한 변수=입력 스키마)**: build_graded 프롬프트에 INPUT CONTRACT 추가 — 액션 형식(verb=`action`,
gen=`id`, NOT type/generatorId), 상수 키(`costMultiplier`), 캐노니컬 디폴트(turn0/energy0/levels0/PLAYING,
productionRate는 입력서 안 받고 RULE-04로 도출). 시나리오 상수 multiplier→costMultiplier 통일(값 동일,
expected 불변). 출력계약·설계·모델은 G34 그대로 고정.
**결과**: 게이트 8/11→**9/11**, 합의 0.659→**0.98**. 그리고 **진짜 수렴 확인**(no-op 아님): SCN-001
turn2/energy6/productionRate6(업그레이드 실제 적용), SCN-002 "Insufficient energy"+energy0, SCN-007
turn2/energy2 — 전부 expected 일치. 액션이 실제로 돈다.
**남은 0.02 = 진짜 명세 구멍(no-op 잔재 아님)**: SCN-009/010만 합의 8/9로 갈림. 승리판정(RULE-05/06)
**타이밍** 미고정 — SCN-010(시작 energy1000+WAIT): 다수 빌드는 WAIT 먼저 적용(turn1/energy1001/WON),
expected는 시작 시점 WON→이후 액션 무시(turn0/energy1000). "액션 처리 전에 승리체크 하느냐"가 계약에
안 박힘. 이건 Step6 Adversarial QA / specqa가 메울 자리(RULE-05/06에 평가시점 명문화).
**결론**: 입력+출력 스키마 둘 다 못박으면 31B가 0.36→0.66→0.98로 거의 완전 수렴. "계약 빡빡→싼 모델
수렴" 방향 정량 확정. 다음 frontier = 명세의 평가시점 같은 엣지를 계약에 박는 것.

## G36 — 계약 명문화(승리판정 평가시점) → 합의 0.98→1.0 (2026-06-17, 키 씀, Step6 PhaseA)
G35가 남긴 구멍(SCN-009/010 합의 8/9 = RULE-05/06 평가시점 미고정)을 계약 한 곳에서 닫음.
빌드 프롬프트가 contract.json의 rules를 그대로 받으므로 **계약이 단일 레버**. 수정:
- RULE-05: "시나리오 시작 시점(액션 전) AND 각 액션 적용 직후에 승리체크" 명문화.
- RULE-06: "WON 되는 즉시 중단, 이후 액션 미처리, 현재 turn/energy 확정" 명문화.
- SCN-006 expected.gameStatus "ACTIVE"→"PLAYING"(계약 enum 위반 오라클오류 교정. 합의엔 무영향
  — consensus는 build-vs-build라 expected 미사용. 순수 스펙 correctness 픽스).
**결과**: 게이트 9/11→**11/11**, 합의 0.98→**1.0**. 그리고 올바른 쪽 수렴 확인: SCN-010
turn0/energy1000/WON(시작 체크로 WAIT 스킵=expected), SCN-003 turn1/energy1000/WON(WAIT후 도달=expected).
**의미**: "계약 빡빡→싼 모델 수렴" 사다리 완성 — 0.36(미고정)→0.66(출력)→0.98(입력)→1.0(평가시점).
명세 구멍을 계약에 박을 때마다 31B가 한 칸씩 수렴. 합의 채점이 "어디가 안 박혔나"를 매번 정확히 지목.
다음(Step6 PhaseB): Adversarial QA 팀 모듈(adversarial.py) — 모델이 깨는 edge_cases를 능동 탐색.

## G37 — Adversarial QA 실측: 깨는 edge 둘 발견 (2026-06-17, 키 씀, Step6 PhaseB)
adversarial.py(§13 Step6) 실행: 31B 팀(lead+리뷰어 8축+synthesis)이 edge_cases 13 + acceptance 5 생성,
validator PASS. 골든을 계약 대비 손검증 → EDGE-001~010·013 계약과 일치(EDGE-008 "32bit overflow"
설명만 JS float64엔 틀림, 골든은 맞음).
**핵심 — 새 키 0으로 수렴한 11빌드(graded-042747)에 edge를 먹여 실측**(관측 우선):
- EDGE-001~010·013: **합의 11/11, golden 일치**. 경계(999/1000/1005)·다중제너레이터·floor·insufficient
  경계까지 수렴 빌드가 동일·정확 처리. → 계약이 그만큼 빡빡하다는 직접 증거.
- **EDGE-011(빈입력 {}) : 10/11 크래시**. actions 키 부재를 대부분 못 버팀(캐노니컬 디폴트 1개만).
- **EDGE-012(미지 generator id) : 5 크래시 / 6 무변화·무로그 / 골든 로그 0개**. 계약 침묵 영역 → 빌드 갈림.
**의미**: §8.5 "구현을 깨는 edge_cases" 충족 — 단순 충족이 아니라 다음 명세 구멍 둘을 정확 지목:
① actions 부재 시 []로 디폴트(빈입력 견고성) ② 미지 generator id 처리(무변화+로그 명문화).
EDGE-012 골든은 계약에 없던 동작이라 synthesis가 BLOCKING 해소로 제안한 **계약 확장 후보**(notes 기록).
**다음 사다리(rung5)**: 이 둘을 계약에 박고 build_graded로 합의가 1.0 유지+크래시 소거되나 재측정.
adversarial_packet/은 커밋(packet=정본). build_runs/는 gitignore.

## G38 — rung5: adversarial 구멍 둘 계약 명문화 → 크래시 소거 (2026-06-17, 키 씀)
G37이 찾은 두 구멍을 계약에 박음(각 제자리): ① 빌드 프롬프트 INPUT CONTRACT에 "actions 부재 시 []
디폴트, 빈 {}도 캐노니컬 상태, 절대 크래시 금지" ② contract.json에 RULE-07 신설("미지 generator id =
무변화 + 'Invalid generator ID' 로그"). acceptance 시나리오는 안 건드림 → 무회귀 확인용.
**재측정(graded-044906)**: acceptance 합의 **1.0 유지**(7/7, 게이트 7/11=빌드변동성). 새 빌드에 edge 실측:
- EDGE-011(빈 {}): 유효 7빌드 **7/7 골든 일치(turn0/energy0/PLAYING). 크래시 10/11→0**.
- EDGE-012(미지 id): **7/7 무변화 수렴(energy 불변/PLAYING). 크래시 5→0**. 단 "Invalid generator ID"
  로그는 4줄 출력계약상 안 노출(2/11만) — RULE-07 상태동작은 수렴, **로그 검증은 출력계약 한계**(백로그).
**결론**: adversarial이 찾은 구멍을 계약에 박을 때마다 싼 모델이 그 엣지에서도 수렴. 사다리 검증 완결 —
이 방치형 카드는 계약이 빡빡+adversarial-robust. 다음: §13 Step7 Integration(최종 workspace 선정 +
static_gate/grade + final_report) 또는 장르확장. 로그-채점 갭은 출력계약에 로그줄 추가 시 해소(백로그).

## G39 — 출력계약에 logs 줄 추가 → RULE-07 로그 채점 가능 (2026-06-17, 키 씀)
G38이 남긴 백로그(로그가 4줄 출력계약에 없어 채점 불가) 해소. 한 변수=출력계약에 5번째 줄 추가:
`logs: <JSON 배열>`(발생 순서, 빈 건 []). 로그 문구 고정 — "Insufficient energy"(RULE-02 거부),
"Invalid generator ID"(RULE-07). 바트 라인 금지(logs: 배열 한 줄로만). 오라클(_norm_output)은 logs 값을
json 라운드트립으로 정규화(공백·따옴표 차 무시, 순서 보존) — 하네스 탓 헛갈림 방지.
**재측정(graded-045740)**: acceptance 합의 **1.0 유지**(6/6, 로그 포함하고도 무회귀). 유효 6빌드 실측:
- SCN-002·EDGE-008·EDGE-009: 6/6 `["Insufficient energy"]` 골든 일치.
- EDGE-012(미지 id): 6/6 **`["Invalid generator ID"]`** 정확 수렴 — 이전 2/11 비노출 → 채점가능·수렴.
**결론**: 출력계약에 로그면을 박으니 싼 모델이 로그 문구·순서까지 정확히 수렴. RULE-07이 상태+로그 모두
채점·수렴. 채점 표면(output contract)이 곧 측정 가능 범위 — 재고 싶은 건 출력에 넣어야 잰다(교훈).
다음: §13 Step7 Integration 또는 장르확장.

## G40 — Step7 Integration: 파이프라인 E2E 완주, 최종 산출물 채점 (2026-06-17, 키0)
integration.py(§13 Stage6) 작성. 기존 수렴 빌드 재사용(키0): 유효 빌드 중 '케이스별 다수합의 일치 최다'
빌드를 최종으로 선정 → static_gate + golden 채점 + final_workspace 복사 + final_report.md.
채점 표면 = 출력계약 키(turn/energy/productionRate/gameStatus/logs)뿐 — golden의 levels는 미출력이라
'출력표면밖(OUTPUT_SURFACE_SKIP)'으로 정직 표기(G39 교훈 재적용).
**결과(graded-045740 재사용)**: 최종=attempt01(4모듈 main+engine+state_manager+utils), static_gate PASS,
**채점 24/24 PASS**(acceptance 11 + edge 13 전부 golden 일치), CRASH/FAIL 0, NO_GRADEABLE 0.
→ `studio/integration_packet/`(final_workspace + static_gate_result + grade_result + final_report).
**의미**: 아이디어 한 줄("방치형")로 Step1~7 전 파이프라인이 실제 완주 — 설계→구현→QA→adversarial→통합까지
무료 31B 오케스트레이션으로 채점된 멀티파일 산출물 도달. 이 카드는 계약이 빡빡+robust+E2E검증 완료.
다음: 장르/형태 확장(같은 파이프라인이 더 어려운 카드에서도 도나, PLAN frontier) 또는 levels 등 출력표면
확장 검토(backlog).

## G41 — 발열(결합) 카드: 하네스 일반화 + 합의 1.0이나 oracle 갈림 2개 (2026-06-17, 키 씀, 다리실험)
방치형 v1 → "발열/과열 억제" 카드로 장르 확장(다리실험: 두 시스템 맞물려도 사다리 버티나). v2는 *_packet_heat.
**하네스 일반화(사용자 결정)**: build_graded가 idle 계약 하드코딩이라 발열에 안 돌아감(OUTPUT=turn/energy/
productionRate/gameStatus, INPUT=constants/initialState/actions[{action,id}]). → 계약구동으로 일반화:
OUTPUT은 contract.state_shape에서 도출(스칼라+logs, config 등 dict 제외), INPUT은 실제 시나리오 예시 주입,
scenarios.json엔 채점메타(id/expected/oracle_risk/covers_reqs) 뺀 전체. 한 하네스로 두 장르.
발열 시나리오 형식: {setup:{energy,heat,generatorLevel,config(8개 명시)}, input:[액션문자열], expected}.
config가 시나리오마다 명시돼 디폴트 고민 불필요(idle와 다른 점).
**측정(graded-085044)**: 게이트 6~8/11(나머지=고아모듈), **합의 1.0**(유효 8빌드, 13시나리오 전부 8/8).
첫 런에서, 사다리 없이. 단 expected 대조 시 **2개 갈림**(성격 다름):
- SCN-008: 빌드 STALLED가 **정확**(COOL실패→throttle생산0→R-07 STALL조건 충족). SpecQA expected RUNNING은
  R-07을 빠뜨린 **oracle 버그**. 빌드>oracle.
- SCN-011(heat==임계 경계): **진짜 틱 순서 모호성**. 빌드 8/8 = "R-04 발열(+2→102) 먼저 → R-05 throttle이
  102>100로 걸림 → energy 안 늚". expected = "턴시작 heat 100, 안 걸림 → +5". 계약이 throttle이 *어느 시점
  heat*를 읽는지 안 박음(R-04를 R-05 앞에 나열만).
**방법론 결론**: ① 맞물림이 빌드 합의를 안 떨어뜨림 — "결합=어렵다" 단순가설 기각. 31B는 결합로직도 1.0 수렴.
② 난이도가 이동 — 합의가 못 보는 스펙 모호성(SCN-011: 전원 한 읽기로 합의하나 oracle와 불일치) + oracle 버그
(SCN-008). **합의 1.0은 필요조건이지 충분조건 아님 — 결합 카드는 독립 oracle 대조 필수, oracle도 틀릴 수 있음**
(하네스-우선 명제 재확인). 병목이 "모델이 만드나"→"스펙·oracle을 모호함 없이 맞게 쓰나"로 이동.
다음: SCN-008 oracle 교정(STALLED) + SCN-011 throttle 시점을 계약에 명문화(사용자 결정 대기) → 재측정.

## G42 — 발열 사다리: 합의 A→B로 끌려옴(핵심) + cascade 모호성 (2026-06-17, 키 씀)
G41의 두 갈림 처리. R-05에 "throttle은 턴 시작 heat로 판정(R-04 발열은 다음 턴부터)=열 관성"(사용자 결정)
명문화 + SCN-008 oracle 교정(RUNNING→STALLED).
**재측정(graded-090733)**: 합의 0.99. **SCN-011 빌드 10/10이 A(energy100)→B(energy105)로 이동, expected 일치.**
완전 수렴한 결합 카드 합의를 *계약 한 줄*로 의도한 읽기로 옮김 = **사다리가 맞물린 시스템에서도 작동(핵심 증명).**
SCN-008도 10/10 STALLED 일치(빌드가 옳았던 oracle 버그 해소).
**그러나 SCN-003 새 갈림(9 vs 1)**: COOL(heat110→80) 후 throttle이 *턴시작 heat110*(9빌드,energy95)냐
*COOL후 heat80*(1빌드+버그oracle,energy100)냐. 내 R-05가 "START of turn"과 "before R-04"를 같이 써 COOL이
끼면 갈림. SpecQA expected(100)도 throttle 누락한 **또 다른 oracle 버그**(다수 9빌드가 정답).
**결론(frontier 실체)**: 결합 시스템은 한 모호성을 박을 때마다 *기능 교차점*(COOL×throttle 시점)에서 더 미세한
모호성이 cascade. "맞물림=빌드 어려움"이 아니라 "맞물림=스펙·oracle을 모호함 없이 쓰기가 어려움". oracle이
반복적으로 틀림(SCN-008·003) → 합의-vs-oracle 대조 필수, 틀리는 쪽은 주로 oracle. 다음 결정: COOL 타이밍
(즉시 완화 vs 관성) 명문화 → SCN-003 oracle 교정 → 재측정 → 발열 E2E 마무리.

## G43 — 발열 COOL 타이밍 B2 명문화 → 골든 13/13 (2026-06-17, 키 씀)
SCN-003 cascade 해소(사용자 결정=즉시 완화 B2: 능동 COOL은 그 턴 throttle 즉시 해제, 수동 발열만 관성).
R-05 재명문화: "throttle은 *이번 턴 액션 후, R-04 발열 전* heat로 판정"(COOL 반영). SCN-003 expected(100)는
이미 B2값이라 시나리오 수정 불필요 — 계약 문구만 모호함 없이.
**재측정(graded-092758)**: 합의 **1.0**, **골든 13/13 PASS**. SCN-003 빌드 8/8이 B1(95)→B2(100) 이동.
SCN-011(105)·SCN-008(STALLED) 유지. 발열 카드가 idle과 같은 종착(전 시나리오 합의=골든) 도달.
**다리실험 종합**: 결합 카드도 사다리로 수렴 가능. 단 idle(0.36→1.0, 출력/입력 계약)과 달리 발열은 *틱 순서
모호성 2개*(관성·즉시)를 명문화해야 했고, 매번 계약 한 줄로 완전수렴 합의를 의도값으로 이동시킴. oracle 버그
2개도 합의-vs-oracle 대조로 검출. 설계 = 능동 즉시 / 수동 관성(일관). 다음: integration.py 계약구동 일반화 →
발열 E2E 마무리(키0).

## G44 — 자동 해소 루프 reconcile.py: 수작업(합의-vs-oracle diff·진단·라우팅) 자동화 (2026-06-17)
사용자 지적("하나하나 손으로 박는 건 자동화가 아니다") 수용. 이번 세션 내가 매 런 손으로 한 일을 코드로:
- **diff(키0)**: graded 런의 게이트통과 빌드 합의를 시나리오 golden과 자동 대조 → 불일치 시나리오·키 추출.
- **resolve(★키)**: 각 불일치를 31B에 되먹여 진단(CONTRACT_AMBIGUOUS/ORACLE_BUG/BUILD_BUG) + 분류
  (AUTO/ESCALATE). 계약이 진실 — 규칙이 박았으면 어느 쪽이 맞는지, 안 박았으면 contract_fix 제안.
- **apply(키0, --apply)**: AUTO만 자동 적용(ORACLE_BUG=expected 교정, CONTRACT_AMBIGUOUS+AUTO=규칙 교체).
  **ESCALATE는 절대 자동 적용 안 함** — 게임 거동 갈리는 진짜 설계 fork만 사람에게.
**검증(키0)**: diff — 깨끗한 런(092758) 불일치 0, 옛 런(085044) SCN-011 정확 검출. resolve — replay로
008=ORACLE_BUG/AUTO·011=CONTRACT_AMBIGUOUS/ESCALATE 분류 확인. apply — 단위테스트로 AUTO 적용·ESCALATE
보존 확인. **두 종류 수작업 구분**: ① 하네스 코드 하드코딩=일회성(build_graded/integration 계약구동화로 끝,
새 카드 코드변경 0) ② 틱 모호성 해소=reconcile이 자동화(사람은 ESCALATE만). 자동화가 모호성 cascade를
없애진 못하나, "사람이 매번 손편집"→"모델이 고르고 문서화, 사람은 fork만"으로 전환.
다음: 실제 모델 resolve 1건 검증(현재 pinned 계약+SCN-011 옛빌드 불일치 → BUILD_BUG 진단하나) → 그 뒤
파이프라인에 Build 후 reconcile 자동 호출 연결.

## G45 — 외부 지적 수용분(회귀 하드닝) 반영 (2026-06-17, 키0)
다른 에이전트 지적 검토 결과 절반은 이미 구현/명세, 결론("v0.1 동결")은 시점 안 맞아 정정. 수용분(병렬 하드닝)만 반영:
- **#1 합의-vs-oracle 자동 diff**: build_graded가 매 빌드 후 다수합의 vs golden을 자동 대조·출력 + consensus.json에
  golden_diffs 저장(키0). 내 수작업 diff 제거. (resolve/apply 자동연결=키 들어 다음.)
- **#2 fixture 6종 추가**: parent_path_escape·unreachable(고아, 실측 반복실패)·npm_import·math_random·
  module_exports_prop·multiline_object. replay 5/5→**11/11**.
- **#2.6 실버그 발견·수정**: contract_validator가 `module.exports.run = run`(prop 패턴)을 export로 인식 못 해
  export 누락 오판하던 버그 → `_MODULE_PROP` 추가로 수정(fixture가 회귀 잠금).
- **#3 lexical 라벨**: planning_compare.md에 unique_issue_count는 토큰 Jaccard lexical heuristic(의미 아님),
  격차 크기 과신 금지 캡션.
- **#4 정본 명시**: validator가 manifest 계약 정본, schema.json은 참고. validate()가 schema required를 읽어
  정본과 어긋나면 warning(참고문서 거짓化 방지). schema에 $comment.
- **#5 path escape guard**: manifest path·require 모두 워크스페이스 밖(../·절대경로) 명시 차단(_escapes).
- **#6 questions 영속화**: planning이 assumptions.json(소비처=Build)·backlog.json(소비처=다음 카드 planning) 분리 출력.
- **#7 FAILURE_TAXONOMY.md**: 제안 6분류 ↔ reconcile 3진단 ↔ plan2 5라벨 ↔ 롤백대상 매핑. reconcile는
  Build↔oracle 슬라이스만 덮음을 명시(분류 난립 금지).
남은 수용분(키 필요): reconcile resolve/apply를 파이프라인에 자동 연결, 장르 N≥3.

## G46 — 적용 가드레일 못박기 (2026-06-17, 외부 합의 반영)
외부 에이전트와 합의된 운영 원칙. 다음 세션/에이전트는 이걸 전제로 한다.
- **v0.1 동결 아님. 확장은 유지한다.** 하드닝은 확장의 전제조건이 아니라 병렬 보험.
- **우선순위: T0(reconcile 자동연결) 즉시 → T1(장르 N≥3 측정) T0 직후 → T2(하드닝) 병렬/배치.**
  T2가 T0/T1을 막지 않게 한다.
- **live build path = build_graded.py** (build.py는 v0 스파이크 잔존, 경로 아님).
- **reconcile은 Build↔oracle 슬라이스만 닫는다.** 전체 failure taxonomy를 추가하기 전에 plan2 5라벨+reconcile
  3진단으로 충분한지 먼저 판정(난립 금지). #7은 "매핑표"가 아니라 "통합 인벤토리"로 재구성(FAILURE_TAXONOMY.md).
  판정 결과: MANIFEST/SPEC/ORACLE/IMPL은 기존 라벨로 충분, INTEGRATION_ERROR·SCOPE_BLOAT만 도입 후보.
- **A/B/C unique_issue_count는 lexical heuristic** — 방향성만 보고 magnitude는 신뢰 안 함(planning_compare 캡션).
- **--apply는 AUTO만. ESCALATE 자동적용 금지**(사람 결정 대기) — reconcile에 이미 그렇게 구현됨.
- **T1 지표(결합 frontier)**: 카드당 ESCALATE 수 / oracle 버그 수 / BUILD_BUG 자동해소율 / ESCALATE cascade 여부.
  "통과했나"만 보지 않는다.

## G47 — T0: reconcile를 build_graded에 연결 (2026-06-17, 코드 키0)
build_graded에 --reconcile/--apply 플래그 추가. 빌드 후 골든 diff가 있으면:
diff(키0) → reconcile.resolve(★키, 진단) → --apply면 AUTO만 자동적용(ESCALATE 제외) → ESCALATE/BUILD_BUG 리포트
(base/reconcile_report.json). _golden_diff에 resolve용 input 포함. 늦은 import로 순환 방지. 기본 off라 키0.
가드레일대로 --apply는 AUTO만, ESCALATE는 사람 대기, BUILD_BUG는 "재빌드 권장"만(자동 루프 금지).
검증: 파싱·import 순환없음·플래그·체인 함수 확인(키0). 전체 체인 라이브 e2e는 불일치 나는 빌드 필요 →
다음 T1 새 카드 빌드(--reconcile)가 T0 검증+T1 측정을 동시에 한다.

## G48 — T1 일반화 실험 설계 확정 (2026-06-17, 외부 합의 최종)
G46 가드레일 위에 T1 측정 설계를 정밀화. 두 큰 수정: ① 낮은 ESCALATE≠Green ② Green 다음≠UI.
- **카드 선택은 장르가 아니라 결합밀도 축**(저/중/고). 최소 1장은 **고결합 필수**(한 틱에 이동·환경·상태이상·
  적행동·자원·승패가 동시 맞물림, 예: 조립카드 T-000012류). 저결합 3장으로 가짜 Green 금지.
- **1순위 지표 = AUTO 정확률**(ESCALATE 아님). AUTO 정확률 정의: AUTO fix 후 ① 다운스트림 테스트 통과
  ② 이전 시나리오 안 깸 ③ 독립 oracle/사람 표본과 일치 ④ 나중 reconcile에서 되돌림 없음. confidently-wrong
  AUTO는 실패보다 위험(안 보임).
- **Green = ESCALATE 낮음 AND AUTO 정확률 높음 AND oracle 불일치 해소가 실제로 옳음.** ESCALATE만 낮으면
  Green 아니라 "의심 상태". E2E 완주(통과율)만으로 Green 아님(heat처럼 합의 통과해도 oracle 버그 숨음).
- **Red는 카드 탓 전에 하네스 탓부터**: 실패 시 HARNESS/INFRA/ORACLE인지 먼저 분리 → 하네스 갭이면 카드
  실패로 안 셈, 하네스 수정 후 재실행 → 그래도 실패면 카드/계약 난이도.
- **N=3 첫 실험 = 정성 스모크**(수렴 되긴 하나만 확인). 임계기반 정량판정은 그 뒤 multi-seed/동결합 다수 카드로.
- **지표 세트**: AUTO 정확률(1순위) / ESCALATE·ORACLE_BUG·BUILD_BUG per card / BUILD_BUG 자동해소율 /
  HARNESS·INFRA vs 카드·계약 실패비율 / 결합밀도별 성공률 / ESCALATE cascade 깊이 / AUTO 계약수정 되돌림률.
- **코어 다음 frontier = 자율 oracle(31B가 골든까지, Phase4 입증) × 고결합 카드 × reconcile calibration.**
  UI/Renderer/Asset은 채점기반을 바꾸므로(deterministic key:value → DOM/sprite/snapshot) **코어의 다음이 아니라
  별도 트랙**. 가더라도 결정적 렌더 채점법(asset_manifest 정확일치 등) 먼저 정의.

## G49 — T1 전 계측: AUTO 검증 로그 + 실패 사전분류 (2026-06-17, 코드 키0)
G48의 1순위 지표(AUTO 정확률)·"카드 탓 전에 하네스 탓부터"를 첫 카드부터 측정 가능하게 하는 사전 계측.
새 taxonomy는 안 만들고 기존 라벨을 재사용한다(G46 난립 금지).
- **`reconcile.verify_auto_fixes`(키0)** — AUTO 적용 후 게이트 아닌 *기록*. ① ORACLE_BUG: 적용한 expected가
  빌드 합의와 일치하나(다운스트림 일관성). 불일치=SUSPECT(confidently-wrong AUTO 후보, 안 보이는 위험을 가시화).
  ② CONTRACT_AMBIGUOUS: 규칙 교체는 재빌드 전엔 빌드거동 검증 불가 → `needs_rebuild_to_verify`로 정직하게 표시.
  ③ 카드별 `auto_fix_ledger.jsonl` 누적 → 같은 (id,key)를 과거와 다른 값으로 덮으면 `reverted_prior`(되돌림/불안정).
  reconcile.py·build_graded.py 양쪽 --apply 경로에서 호출, reconcile_report.json에 `auto_verification` 추가.
- **`build_graded.classify_attempt_failure`(키0)** — 게이트 실패 attempt를 INFRA/HARNESS/CARD로 사전분류.
  INFRA=plan2 INFRA_FAIL(observability.INFRA_MARKERS 재사용: api·network·429·쿼터), HARNESS=plan2 HARNESS_FAIL
  (우리 도구 크래시), CARD=plan2 MODEL_FAIL(생성코드·계약: static/contract/스모크 실패). consensus.json에
  `failure_classes`+`gate_failed_reasons` 기록.
- **worker 하드닝** — 생성 단계 예외→`infra:`, 파싱·쓰기·게이트 예외→`harness:`로 잡아 런 안 깨고 기록.
  전엔 하네스 크래시가 런 전체를 죽였음 → 이제 "하네스 갭이면 카드 실패로 안 셈"(G48)이 실제로 작동.
- **키0 검증**: classify 7케이스 PASS, verify_auto_fixes(일관성·SUSPECT·되돌림·needs_rebuild) PASS, reconcile
  replay 무회귀. 라이브 e2e는 T1 첫 카드(--reconcile --apply)가 이 계측을 동시 검증한다.
- **한계(정직히)**: 키0라 ③(독립 oracle/사람 표본 일치)은 코드로 못 잼 — ESCALATE 사람검토·자율oracle 트랙의 몫.
  verify는 내부 일관성·되돌림만 본다.

## G50 — 저합의 가드: confidently-wrong AUTO 차단 (2026-06-17, 코드 키0)
T1 고결합 첫 측정(G51) 중 실측된 위험에 대응. **저합의(다수파가 유효빌드 과반 미달) 시나리오의 AUTO를
ESCALATE로 강등**한다(`reconcile.apply_low_consensus_guard`). 근거: 합의 0.25(4빌드 중 1표)를 근거로
reconcile이 무한루프 타임아웃값(tick=1000)을 "정답"으로 채택해 oracle expected를 자동교정 = confidently-wrong.
G49 AUTO검증(downstream_consistent)이 합의 신뢰도를 안 봐서 통과시킴 → 검증 설계 갭 노출.
- diff/`_golden_diff`에 `agreement`(표수) 추가, `verify_auto_fixes`에 `consensus_rate` 기록, 양쪽 --apply
  경로에서 resolve 직후·apply 직전 가드 호출. reconcile_report에 `low_consensus_guarded` 추가.
- 방치형·발열(합의 1.0)은 과반 충족이라 영향 없음. 단위검증 PASS, replay 무회귀.
- **알려진 빈틈(미수정, 새 세션)**: 임계가 "과반(>0.5)"이라 합의 0.6(예: SCN-009 3/5)은 통과 →
  무한루프값이 AUTO로 박힘. 절대다수(예: 2/3↑)로 조이면 막힌다. 키0 작업.

## G51 — T1 고결합 첫 측정(정성 스모크): 결합밀도 저/중/고 (2026-06-17, ★키)
G48 설계대로 결합밀도 3축을 build_graded --reconcile로 측정. 첫 N=3 정성 스모크(수렴되나·계측 작동하나).

| 카드 | 결합 | 패킷 | 게이트 | 합의 | golden diff | 실패분류 |
|---|---|---|---|---|---|---|
| 방치형 | 저 | `*_packet` | 9/11 | **1.0** | 0 | CARD=2 |
| 발열/과열 | 중 | `*_packet_heat` | 8/11 | **1.0** | 0 | CARD=3 |
| 턴제 전투 | 고 | `*_packet_combat`(신규) | 6/11 | **0.567** | 12 | CARD=5 |

- **저·중결합은 완전수렴(1.0, diff 0, ESCALATE 0)** — baseline. G49 계측(실패 사전분류)이 라이브 무사 작동
  (실패 전부 CARD로 정확분류, INFRA/HARNESS 0). 검증된 카드라 --apply 없이 진단만.
- **고결합은 합의 붕괴(1.0→0.567)** — 과거 지목한 "틱·속도게이지 스케줄러 frontier"가 그대로 재현.
  빌드들이 게임 종료조건을 제각각 → 다수가 tick=1000/1001(무한루프 타임아웃)을 쏟음.
- **confidently-wrong AUTO 실측**: 1차 런(--apply)에서 합의 0.25를 근거로 reconcile이 tick=1000을 정답으로
  채택해 oracle 자동교정, AUTO검증은 "이상없음" 통과 → G48 경고("안 보이는 위험")가 라이브로 재현.
  → **G50 저합의 가드 추가** 후 재측정: 저합의 AUTO 3건(SCN-008/010/013) ESCALATE 강등 = 그 부류 차단 확인.
  ESCALATE 6 = reconcile 31B 자체 3건(SCN-003/004/005 "종료조건 없어 무한루프"라 정확 진단) + 가드 3건.
- **근본원인 = 계약 결함(종료조건 부재)**. 고결합이라기보다 계약에 "비종료/타임아웃" 규칙이 없어 빌드 제각각.
  사다리 원리(G33~38)상 그 한 줄 박으면 합의 0.567→상승 예상. reconcile ESCALATE가 정확히 이걸 지목.
- **교훈**: ESCALATE=0이 Green이 아니듯(G48), ESCALATE 6건이 *카드의 진짜 결함을 정확히 가리킨* 것 =
  측정이 제대로 작동. 1순위 지표(AUTO 정확률)는 가드로 confidently-wrong을 막아야 신뢰됨(가드 없으면 가짜 高정확률).
- **상태/주의**: `*_combat` 패킷의 specqa expected는 재측정 --apply로 AUTO 6건 적용된 *오염 상태*(비종료
  시나리오 tick이 1000/1001/등으로 덮임). 새 세션이 B(계약 종료조건+oracle 교정+재빌드)를 하려면 specqa
  재생성으로 원복하고 시작. build_runs는 .gitignore.
- **사용자 결정**: B(계약 종료조건 박고 재빌드 — 사다리 수렴 검증)와 가드 임계 강화는 **새 세션**에서.
  측정 본질로는 B가 우선(고결합도 계약 박으면 수렴하나 = frontier 핵심 질문).

## G52 — B 완료: 고결합 종료조건(RULE-10) → 합의 0.567→0.762 + repr 버그 (2026-06-17, ★키)
frontier 핵심 질문에 **긍정 답**. 계약에 종료조건 한 줄 박으니 고결합 합의가 올랐다.

- **계약 RULE-10 추가**: "tick 1000 도달 시 무승부(isGameOver=true, winner=null, tick=1000 고정)".
  reconcile 31B가 G51에서 정확히 지목한 그 수정. 빌드들의 무한루프 타임아웃(1000 vs 1001 제각각)을
  한 값으로 못박음.
- **oracle 손교정(재생성 안 함)**: 비종료 7개(SCN-003/004/005/008/009/010/013) expected를 draw(tick=1000)로.
  플랜 ①(specqa 재생성)을 **기각** — 재생성은 시나리오 입력을 바꿔 0.567 baseline과 사과-대-사과를 깬다
  (측정 1변수 원칙). 오염은 SCN-009=1001 한 곳이라 손교정이 더 정확. 변수=계약 종료규칙 하나로 고정.
- **결과: 합의 0.567 → 0.762** (게이트 5/11, CARD=6은 JS 구문오류 별개). **비종료 tick 완전 수렴**
  (oracle 대비 tick 불일치 0). 사다리 원리(G33~38) 재확인 = 고결합도 계약 한 칸 박으면 한 칸 수렴.
- **2/3 저합의 가드 라이브 검증**(곁다리, 키0 선행 커밋): SCN-003·008(둘 다 3/5=0.6)이 새 절대다수 기준
  (`3*agree<2*total`)에 걸려 ESCALATE 강등. 구 과반(>1/2) 기준이면 통과했을 값 — 빈틈(G50) 메움 실증.
- **하네스 repr 버그 발견·수정**: `_golden_diff`·`reconcile.diff`·`_stringify`가 파이썬 `str()`로 oracle
  `None`→"None", `True`→"True"를 만들어 빌드의 JS `null`/`true`와 거짓 불일치(winner 7건 전부). 31B도
  "representation error"로 정확 진단. `_js_scalar`(build_graded) 헬퍼로 None→null·bool→true/false 통일.
  재diff로 winner 7건→0, reconcile replay 회귀 통과. **measurement엔 무해**(빌드 합의는 영향 없음)했으나
  oracle 채점 표면에 None/bool이 들어오면 항상 터지던 잠복 버그 — "하네스 우선" 교훈 또 하나.
- **잔여**: 합의 0.762는 완전수렴(1.0) 아님 — 통과 5빌드 간 logs/winner 표기 잔차로 추정. 게이트 5/11(JS
  구문오류 6)은 생성 품질 별개 이슈. 다음 = 잔차 원인 분해 / 정량 판정(multi-seed·동결합 다수 카드).

## G53 — 정량 판정 1단계: B 0.762는 +2.9σ 단발이었다 (2026-06-17, ★키)
정량 판정 1순위(★키)의 1단계 = **같은 combat 카드를 시드(재실행) N=6으로 돌려 합의 분포**를 잰다.
온도 미지정(=API 기본)이라 재실행 자체가 시드. golden 무관한 빌드-간 합의만 보므로 `--reconcile/--apply`
안 씀(계약 불변). 도구 = `studio/multiseed.py`(build_graded.main 래퍼 + 평균·표준편차 집계).

- **결과(N=6)**: 합의 **0.633 ± 0.044** (값 [0.641, 0.600, 0.641, 0.565, 0.669, 0.685], min 0.565 max
  0.685). 게이트통과 5~7/11.
- **판정: G52의 0.762는 재현 안 됨** — 새 분포 평균 대비 **+2.9σ 고점(운빨 단발)**. B카드 합의의 진짜 값은
  **0.63±0.04**다. N=1 측정은 ±0.06 흔들린다 = 단발 신뢰불가가 정량 입증.
- **더 아픈 점**: multiseed **min 0.565 ≈ G52의 "RULE-10 박기 전" baseline 0.567**. 즉 "RULE-10으로
  0.567→0.762 상승"은 **과장**. 정직한 버전 = 박기전 0.567(N=1) vs 박은후 0.633±0.044(N=6) → **두 점이
  겹쳐 상승이 통계적으로 확립 안 됨**. 고결합 사다리(G52) 정성 결론을 이번 측정이 **깎았다**. baseline도
  multi-seed로 재야 "박으면 오른다"를 말할 수 있다(다음 후보).
- **분산 자체는 좁다**(std 0.044, 변동계수 ~7%) — 하네스가 미친 듯 시끄럽진 않음. 다만 게이트통과 5~7개라
  합의 투표수가 적어 합의값이 거칠다(소표본). 게이트 실패 주원인은 전부 **JS 구문오류**(생성품질, 카드 무관).
- **곁다리 인프라 버그 1건**: 승격(arag→golem 분리) 때 공유 4파일만 옮기고 `key_usage.py`(키 RPD 트래커)를
  빠뜨림. `llm.py`가 지연 import라 키 콜 직전까지 잠복 → 1차 6런 전부 INFRA 실패. arag 원본 그대로 golem
  루트에 복사(코드 0수정). PROJECT_ROOT=golem라 `runs/key_usage.json`은 arag와 별도 파일(키 경쟁·유출 없음).
  **HANDOFF "공유 4파일" → 실제 5파일**.
- **교훈**: "측정 가치는 N에 산다." 사다리 서사(G33~52)는 거의 다 N=1 단발 위에 세워졌다 — 정량 판정이
  필요한 이유가 1번 카드에서 바로 드러남. 다음 = baseline도 multi-seed로(상승 확립 여부) / Step2 동결합
  다수 카드(재현성) / Step3 결합도 스윕(임계곡선).

## G54 — 정량 판정 2단계: RULE-10 효과 결판(분포 분리, d=2.7) (2026-06-17, ★키)
G53가 깐 의문("0.567→0.762 상승이 통계적으로 확립되나")을 baseline도 multi-seed로 재서 결판냈다.
RULE-10만 뺀 baseline 패킷(`studio/planning_packet_combat_baseline`, 계약 9 rules, design/specqa는
원본 그대로 = 1변수) N=6.

- **결과**: baseline **0.421 ± 0.102** [0.269, 0.538] vs post-RULE-10 **0.633 ± 0.044** [0.565, 0.685].
  평균차 +0.213, Welch **t=4.69 (df~6.8, p≈0.002)**, Cohen **d=2.71**, **두 분포 완전 분리(겹침 0)**.
- **결론1 — 사다리 살아남음**: 계약 종료규칙 한 줄이 고결합 합의를 ~0.21 올린다(거대 효과, 분포 안 겹침).
  "계약 박으면 수렴"이 고결합에서도 정량으로 확립. G52 정성 결론의 *방향*은 옳았다.
- **결론2(보너스) — RULE-10은 분산도 5.3배 줄인다**: baseline은 종료규칙이 없어 빌드마다 루프상한을
  제멋대로 발명(불일치가 전부 tick 합의=1001·2001·10001 vs oracle 1000) → 합의가 낮고 *시끄럽다*. 규칙이
  그 발산을 한 점으로 묶어 수준↑ + **안정화**까지. 계약은 평균만이 아니라 분산을 잡는다 — 더 깊은 수확.
- **결론3 — G52 두 숫자는 둘 다 고점 운빨**: 진짜는 0.42→0.63. 0.567은 baseline 분포의 위쪽(평균 0.421,
  max 0.538 근처), 0.762는 post 분포 +2.9σ. 두 N=1이 각자 위쪽을 뽑아 상승폭(~0.21)만 우연히 비슷.
  **상승은 맞고 양 끝점이 틀린** 케이스 — N=1의 전형적 함정.
- **방법 메모**: baseline은 무한루프 빌드가 스모크 타임아웃(30s)으로 게이트 탈락 → 게이트통과 2~5(post는
  5~7). 통과 표본이 작아 합의 분산이 더 큰 것도 일부 기여. 그래도 분포 분리는 표본수로 안 깨질 만큼 큼.
- 다음 = Step2 동결합 다수 카드(0.633이 카드별 재현되나) → Step3 결합도 스윕(임계곡선).

## G55 — 정량 3단계(Step2): "고결합→합의붕괴" 재현 실패 = 결합도 가설 기각 (2026-06-17, ★키)
새 고결합 카드(eco: 틱기반 포식자-피식자 생태계)를 풀 파이프라인(planning→design→specqa, 전부 ★키
실완주, FROZEN/PASS)으로 만들어 multiseed N=6. 0.633 재현 여부를 보려던 것.

- **결과(주의: 측정 함정 있음)**: eco 합의 **0.983±0.028**, 게이트통과 **1~6/11(평균 3.5)**. 실패 전부
  JS 구문오류(생성품질). 즉 combat(0.63@게이트5~7)과 **정반대**: eco는 *대부분 컴파일 실패*하지만 컴파일된
  빌드는 *강하게 수렴*(8개 중 7개 정답, 틀린 건 SCN-004 번식 1건).
- **판정 — 결합도 가설 기각**: "결합도 크면 합의 무너진다"는 거짓. combat을 무너뜨린 건 결합도 *크기*가
  아니라 **특정 종료 모호성**. eco는 planning이 계약에 **PHASE 1~5 순서를 명시**해(combat 종료조건이 느슨했던
  것과 대조) 컴파일된 빌드가 수렴. **합의를 정하는 건 결합도가 아니라 계약 빡빡함** = G33~G54 사다리 thesis
  재확인. [[G54]] 와 같은 결: 계약 타이트가 합의를 올린다. 난이도는 또 이동(eco는 합의붕괴가 아니라 컴파일
  실패로 = 발열카드 G41~44 "난이도 이동" 반복).
- **측정 함정 2건(이래서 결론은 잠정)**:
  - **A. 합의 지표가 게이트통과 수에 오염**: 통과 1~2개면 합의 자동 1.0(자기자신 일치). eco 1~6표 vs
    combat 5~7표라 0.98 직접비교 무효. → 통과수 맞춰야(cap↑) 깔끔. **consensus에 min-voter 가드/표본수
    병기 필요**(하네스 backlog).
  - **B. repr 버그 재발(_js_scalar 사각)**: `entities`(리스트) oracle 대조가 JSON 큰따옴표 vs 파이썬
    repr 작은따옴표로 거짓 불일치 5/6건(값은 동일). G52 `_js_scalar`는 None/bool 스칼라만 고쳐 리스트/딕트
    출력은 여전히 `str()`로 샘. measurement엔 무해(빌드합의 불변), golden_diff 진단표면만 오염. **구조적
    출력값은 양쪽 json.dumps로 통일 필요**(하네스 fix 후보).
- 산출물: `*_eco`(planning/design/specqa packet). 다음 = (1) eco cap↑ 재측정으로 표본수 맞춰 0.98 검증
  / (2) repr·min-voter 하네스 fix / (3) Step3 결합도 스윕은 위 함정 해소 후.
- **하네스 fix 완료(키0, 같은 세션)**: (B) `_js_scalar`→`_canon` 일원화 — 빌드 stdout 문자열이든 oracle
  파이썬 값이든 JSON 정규화(sort_keys, 공백제거)로 통일해 스칼라+구조적 출력(entities) 거짓 불일치 차단.
  build_graded·reconcile 동시 적용, reconcile replay 회귀 불변(불일치 2건 동일). (A) consensus에 MIN_VOTERS=2
  가드 — 1표 자명합의(자기자신=1.0) 제외, 표 부족 시 overall=None, consensus.json에 `voters`(평균 투표수)
  병기, multiseed가 None 시드 제외+표본수 출력. combat/baseline(표 2~7)은 불변, eco 1표 시드만 영향.
- **eco cap=22 재측정 — 결합도 가설 기각 확정(잠정→굳힘)**: 표본수를 combat급(평균 7표)으로 맞춰
  재측정 → eco **0.925±0.054** [0.857, 0.969] vs combat **0.633±0.044** [0.565, 0.685]. Welch t=10.2,
  Cohen d=5.89, **분포 완전 분리**(eco min 0.857 ≫ combat max 0.685). 두 고결합 카드가 정반대 합의 =
  **결합도 크기는 합의를 예측 못 함**. 합의를 가른 변수는 계약 빡빡함(eco PHASE 1~5 명시 vs combat 종료
  느슨). **하네스 fix 실증**: cap11 eco 0.983 → cap22 0.925 = 작은표본 인플레 +0.057을 min-voter 가드가
  정확히 잡아냄. 다음 = Step3 결합도(=계약타이트) 스윕 / eco 잔차(0.925≠1.0, SCN-004 번식 1건) / 자율 oracle.

## G56 — 정량 Step3: 계약-타이트 스윕(같은 카드, 곡선) (2026-06-17, ★키)
같은 combat 카드를 계약 loose→tight 3럽으로 multiseed N=6, cap=11, **현재 하네스(G55 fix 후)로 셋 다
동일조건 재측정**(크로스-하네스 비교 우려 제거). design/specqa 고정 = 1변수. 도구 `studio/sweep.py`.
럽: L0 baseline(9 rules) → L1 +RULE-10 종료(10) → L2 +RULE-11 틱 PHASE 1~7 순서 명시(11, eco가
수렴한 그 장치를 combat에 이식). 산출 `build_runs/sweep-20260617-185855/`.

- **합의 곡선(raw, 단조 상승)**: L0 **0.369±0.070** [0.3, 0.5] → L1 **0.649±0.150** [0.494, 0.897] →
  L2 **0.799±0.179** [0.5, 1.0]. **계약 한 칸 박을 때마다 합의가 오른다** — 사다리 thesis(G33~G55)가
  *같은 카드 위에서* 곡선으로 재확인.
- **L0→L1(RULE-10 종료조항)**: Δ+0.280, Welch t=4.15, **p=0.004**, Cohen d=2.39. RULE-10 효과의
  **3번째 독립 재현**(G53·G54에 이어 현재 하네스로도). 절대값 0.37→0.65는 G54의 0.42→0.63과 일치
  (하네스/노이즈 범위 내). **확립.**
- **L1→L2(RULE-11 PHASE 순서)**: raw Δ+0.150, t=1.57, **p=0.148(N=6서 유의 미달)**, d=0.91, 분포 겹침.
  방향은 +지만 깨끗이 확립 안 됨. **이유 = G55 소표본 인플레 함정 재발**: L2 상위값(1.0·0.955·0.5)은
  **전부 2표 시드**(자명합의). L2가 게이트 2~7로 통과빌드↓ → 투표수↓(평균 3.78표 vs L1 5.68표)라
  0.80 직접비교 무효.
- **투표수 매칭(≥5표 시드만)**: L1 0.662(5시드) vs L2 0.758(2시드, [0.795, 0.721]). 매칭해도 L2>L1
  (Δ+0.096)이나 L2 N=2로 검정력 부족. **PHASE 순서가 올리는 *경향*은 보이나 통계 미확립.**
- **메커니즘 — "난이도가 컴파일로 이동"(G41~44·G55 반복)**: RULE-11로 계약이 길고 빡빡해지자 빌드
  **실패율↑**(failure_classes 전부 `CARD`=MODEL_FAIL=JS 생성품질, seed2는 11중 9 실패). 즉 타이트한
  계약은 컴파일된 빌드의 합의는 올리되 컴파일 *성공률*은 떨어뜨린다 = eco(드물게 컴파일·강수렴)와 동형.
- **판정**: 곡선의 단조 상승(thesis)은 재확인. 단 L1→L2 결판은 **eco가 cap=22로 해소했던 것과 똑같이
  cap↑ 재측정으로 투표수를 매칭해야** 깨끗해진다. 다음 = sweep cap↑(L2 통과표 5~7로) 재측정 / eco·combat
  잔차 / 자율 oracle.

## G57 — 외부 코드리뷰 12항목 분류 + P0 4건 수행 (2026-06-17, 코드 키0)

외부 리뷰("AUTO reconcile/합의를 얼마나 믿나" 명제)를 실제 파일 대조로 검증해 지금/나중/기각으로 분류.
리뷰 핵심 방향은 옳음(핸드오프 자율 oracle frontier와 일치). 단 절반은 "이미 있음" 또는 "과장".

- **지금 한 것(P0, 키0, 이번 세션 완료)**:
  - **#1 build.py LEGACY 경고** — 헤더에 "라이브 금지, build_graded.py가 정본" 배너. 새 세션 혼동 차단.
  - **#3 AUTO suspect 롤업 + Green 게이트** — 신규계측 아님. 이미 쌓이던 `auto_verification`(status
    downstream_consistent/SUSPECT/needs_rebuild)를 `summarize_auto_verification()`로 카운트 롤업해
    `reconcile_report.json`에 `auto_summary` 추가(reconcile.py·build_graded.py 양쪽). **하드룰**:
    `auto_suspect>0 → green_blocked=True` 출력("ESCALATE 수와 무관하게 Green 금지"). confidently-wrong이
    낮은 ESCALATE에 가려지는 게 진짜 위험이라는 리뷰 지적이 정확. accuracy_proxy=consistent/(consistent+suspect),
    needs_rebuild는 재빌드 전 검증불가라 분모서 제외.
  - **#7 planning_compare.md 경고** — 상단에 "unique_issue_count는 lexical heuristic, 수치격차 신뢰말것,
    live reviewer 정책 직접근거 금지" 배너. (G46에서 알던 것을 파일에도 명문화.)
  - **#9 schema 정본** — 리뷰 권고(A안)가 **이미 구현돼 있어 추가작업 없음**: `contract_validator.py`의
    `_schema_drift()`가 schema.json required를 읽어 정본(`_REQUIRED_FIELDS`)과 어긋나면 warning. 죽은 문서 아님.
  - 검증: `import reconcile,build_graded` OK + 헬퍼 스모크(suspect건 green_blocked=True) + reconcile replay
    회귀(fixtures/reconcile_demo) 진단 동일·크래시0 통과.

- **나중에(다음 실험 전, P1)**: **#8 실측 실패 fixture**(EDGE-011/012·고아모듈·미도달 config.js를 회귀잠금,
  상상 fixture보다 우선) / **#6 taxonomy 인벤토리**(plan2 5라벨+reconcile 3진단+gate 라벨 정리 후에만 신규도입,
  라벨별 액션 명시 — 난립 방지) / **#4 Integration 위험지표**(auto_suspect·low_consensus_guarded·output_surface_skip를
  final_report에 — 단 자율 oracle frontier가 실제 부를 때) / **#5 Spec QA expected_confidence**(소비처[reconcile/Integration]를
  **동시 배선할 때만** 추가 — 안 그러면 #10이 경고한 죽은 필드) / **#10 ASSUMED/DEFERRED 소비처**(생산자 존재 확인 후 배선).

- **기각·보류(안 함)**: **#11 전면 포맷 커밋 — 기각**. 실측결과 최장 134~162자·80자초과 22~23%로 빽빽하지만
  병리적 아님(한 줄 코드 아님). 실험 중 코드 전면 reformat은 git blame 파괴 = 비용>효용. 새 파일만 깔끔히로 대체.
  **#2 build_graded 분해 — 보류**(363줄, 지금 분해 크기 아님 — "성장 금지" 가드레일로만). **#12 package화 — 보류**
  (둥지 구조는 승격 때 코드0 위해 *의도된* 선택, 되돌릴 이유 약함, P2).

- **교훈**: 리뷰의 "필드 추가" 권고(#3·#4·#5) 다수는 **원시 데이터가 이미 있고 롤업+게이트룰만 빠진 것** =
  싼 작업. 그리고 #5(필드추가)와 #10(죽은 필드 금지)은 자기모순 — 소비처 동시 배선이 해소 조건.

## G58 — 스윕 cap=22 결판: L1→L2(RULE-11 PHASE 순서)는 상승 아님 (2026-06-17, ★키)

G56의 미확립(L1→L2 p=0.148)을 eco와 동일한 cap↑ 투표수 매칭으로 결판. 산출
`build_runs/sweep-20260617-203412/`. N=6, cap=22.

- **합의 곡선(cap=22)**: L0 **0.347±0.046**(5.66표) → L1 **0.640±0.131**(11.13표) → L2 **0.607±0.149**(5.71표).
- **L0→L1(RULE-10 종료조항)**: Δ+0.293, t=5.17, **p=0.0019**, d=2.98, **분포 분리**. 투표수 11표로 더 강한
  **4번째 독립 재현**(G53·G54·G56에 이어). 확립 재확인.
- **L1→L2(RULE-11 PHASE 순서)**: Δ**−0.033**, t=−0.41, **p=0.693**, d=−0.24, **분포 겹침**. 사실상 0(미세 음).
  **상승 아님으로 결판.**
- **G56의 0.80 = 소표본 인플레였음 확정**: cap=11 L2는 게이트로 통과빌드↓ → 평균 3.78표(상위값 1.0·0.955·0.5가
  전부 2표 자명합의). cap=22로 L2 투표수를 5.71표(전 시드 4.0~7.85, 자명합의 소거)로 매칭하자 **0.80→0.607로
  내려앉음**. eco가 cap11 0.983→cap22 0.925로 인플레 잡힌 것과 **동일 현상**(G55). 하네스 min-voter 가드의 정당성 재실증.
- **thesis 정정**: "계약 한 칸 박을 때마다 합의 상승"은 **규칙 종류에 의존**한다. 거동을 *결정짓는* 계약
  (RULE-10 종료조항: 무승부 tick)은 합의를 크게 올리고, 이미 잡힌 거동의 *세부 명세*(RULE-11 PHASE 순서)는
  combat에서 추가 상승 0. 사다리는 L0→L1 한 칸에서만 작동 — 모든 규칙이 한 칸씩 올리는 게 아니다.
- **eco는 PHASE로 수렴했는데 combat은 왜 안 오르나(backlog 가설)**: PHASE 순서는 *틱순서 모호성이 잔차
  불일치의 지배항일 때만* 효과(eco). combat은 RULE-10 박은 뒤 잔차 불일치가 PHASE 순서 문제가 아니라 다른
  곳(JS 생성품질·액션해석)이라 RULE-11이 안 닿는다. = "난이도가 컴파일로 이동"(G41~44)과 정합: L2는 계약이
  길어져 게이트만 더 떨어뜨림(통과 4~8 vs L1 8~14).
- **판정**: 정량 트랙 1~3단계 + Step3 스윕 **종결**. 확립된 것 = ① 결합도 가설 기각(eco 0.925 vs combat 0.633,
  d=5.89) ② RULE-10 효과(d≈3, 4회 재현) ③ PHASE 순서는 combat 합의 안 올림. 다음 = 자율 oracle / eco·combat 잔차.

## G59 — 외부리뷰 P1 #8: 실측 실패 fixture 회귀잠금 (2026-06-18, 키0)

리뷰 #8 = "상상 fixture보다 실제 반복 관측된 실패를 먼저 굳혀라". 회귀 러너 = `replay.py`
(`fixtures/*`에서 expected.json+module_manifest.json 가진 디렉터리 자동발견 → `contract_validator.validate`
→ 선언한 failing_check가 실제 터지는지 단언). **새 fixture = 디렉터리 하나 떨구면 자동 잠금.**

- **갭 분석**: static_gate 5검사(multifile·syntax·no_npm·deterministic·reachable) 중 음성 fixture가
  **없는 건 `syntax`(node --check 구문오류) 하나뿐**. 그런데 이게 스윕(G56·G58)에서 *가장 잦은 실측 실패*
  ("구문 오류 main.js", failure_classes 전부 CARD=JS 생성품질). 고아·미도달은 `unreachable_module`,
  결손은 `missing_file`이 이미 커버 — 리뷰가 우선순위로 든 고아/미도달은 이미 잠겨 있었음.
- **추가**: `fixtures/demo_fail_syntax_error/`(미닫힘 중괄호 = 불완전 생성 패턴, node "Unexpected end of input").
  expected failing_check=static_gate. replay **11→12 fixture, 전부 green**.
- **surgical 판단**: extra_js·multifile 등은 스윕서 미관측이라 추가 안 함(리뷰 원칙=수 늘리기 아님). 남은
  실측 갭 = "output surface 밖 키 많아 채점 누락"인데 이건 consensus 채점 fixture(build_graded)라 replay 밖
  **별도 하네스** 필요 — 백로그.

## G60 — 자율 oracle 프로브 1차: 31B가 골든을 0.879 자율 생성, 실패는 전부 계약-모호 (2026-06-18, ★키)

코어 frontier 첫 결판. "31B가 빌드 안 보고 rules+입력만으로 expected(골든)를 손계산해 낼 수 있나."
도구 `studio/auto_oracle.py`(시나리오마다 rules+input+골든키 → 31B 손실행 → 골든과 키별 _canon 일치).
방치형(골든 1.0 신뢰), 11시나리오 × 3시드 = 33콜. 산출 `build_runs/autooracle-20260618-084124/`.

- **자율 oracle 정확률 0.879**(완전정확 9/11), 평균 안정성 0.939. 결정적 산술(energy·turn·currentCost
  곱셈·productionRate)은 **11/11 전부 정답** — 모든 시나리오에서 수치 계산 무결.
- **두 실패 다 산술 아님 = 계약-모호(어휘) 불일치**:
  - SCN-006 gameStatus 0/3: 골든 `"PLAYING"` vs 31B `"IN_PROGRESS"`/`"NOT_WON"`. **의미는 정답**(미승리·진행중),
    계약이 enum 문자열을 안 박아 라벨만 다름. energy=999는 3/3. = G36서 사람이 손으로 박았던 그 모호성을 재현.
  - SCN-002 levels 2/3: 골든 `{"gen1":0}` vs seed1 `{}`. 미업그레이드 발전기를 0으로 적나 마나(빈 컬렉션 관례 미박음).
- **판정(긍정 + 정밀)**: 자율 oracle은 **가능**하다 — 31B는 결정적 계산을 완벽히 한다. "틀린" 곳은 계약이
  *진짜 안 박은* 표면(enum 라벨·빈 dict 관례)뿐이고, 이는 reconcile이 CONTRACT_AMBIGUOUS로 잡으라고 만든
  바로 그 표면. 즉 자율 oracle의 불일치 = **공짜 계약-모호 탐지기**(빌드 한 줄 없이, 사람이 G36서 손으로
  찾은 모호성을 33콜로 재발견). 리뷰 #5("oracle 후보 오염")의 실거리 = 오염은 계산오류가 아니라 미명세 어휘에
  국한 → 계약에 박으면 소거 가능(사다리와 동형).
- **다음(이 프로브 위에서)**: ① 자율 oracle을 *어휘 박은 뒤* 재측정(enum/빈컬렉션 계약 한 줄 → 0.879→?
  1.0 수렴 검증, G36 사다리의 자율판) ② 고결합 카드(eco/combat)서 자율 oracle 정확률 — 결정적 계산이 깨지는
  난이도 경계 탐색 ③ 자율 oracle을 reconcile 입력으로 배선(손-oracle 대체).

## G61 — 자율 oracle 사다리: 어휘 한 줄 박으니 0.879→1.0 수렴 (2026-06-18, ★키)

G60 프로브 후속. G60이 짚은 두 모호성(SCN-006 gameStatus enum·SCN-002 levels 빈dict)을 계약에 RULE-08
한 줄로 박고 재측정 → **0.879→1.0**. G36(빌드합의 0.98→1.0)의 자율-oracle 판.

- **진단 정밀화**: state_shape엔 `"gameStatus":"PLAYING | WON"`이 있었으나 모델에 주는 *rules*엔 'WON' 조건만
  있고 "기본값=PLAYING"·"levels 초기화={각 id:0}"가 없었다 = rules와 state_shape의 명세 갭. 변형 패킷
  `planning_packet_idle_vocab`(원본+RULE-08, 1변수, 원본 무변경)에 그 갭만 박음.
- **RULE-08**: "scenario 시작 시 gameStatus='PLAYING', levels={constants의 모든 id:0} 초기화. gameStatus는
  'PLAYING'|'WON' 리터럴. levels는 항상 모든 constants id 포함(레벨0도)."
- **결과**: 자율 oracle 정확률 **1.0**(완전정확 11/11), 안정성 0.939→**1.0**. SCN-006 gameStatus 0/3→**3/3**,
  SCN-002 levels 2/3→**3/3**. 골든은 그대로(specqa_packet 무변경) — 계약만 1줄 박아 수렴 = 1변수 인과.
- **판정(자율 oracle 사다리 확립)**: ① 싼 모델(31B)이 빌드 0줄로 oracle을 만들 수 있다. ② 그 불일치는 *공짜
  계약-모호 탐지기*다(G60). ③ 탐지된 모호성을 계약에 박으면 자율 oracle이 1.0 수렴한다(G61) — **빌드합의
  사다리(G33~38)와 동형, 이번엔 oracle 생성 표면에서**. 사람이 G36서 손으로 돈 루프(모호성 찾기→계약에 박기→
  수렴)를 33콜로 자동 완주. **자율 oracle은 viable + self-correcting.**
- **다음**: ① 고결합 카드(eco/combat) 자율 oracle — 결정적 계산이 깨지는 난이도 경계(방치형은 산술 단순) ②
  reconcile 입력에 자율 oracle 배선(손-oracle 대체, 모호탐지→계약fix 루프 자동화) ③ 어휘갭을 self-detect까지(31B가
  자기 불일치 보고 어느 계약줄 박을지 제안).

## G62 — 자율 oracle 고결합(eco): 결합 무관, 실패는 또 전부 계약-모호 (2026-06-18, ★키)

G61 다음 = 결합도가 결정적 oracle 계산을 깨나. eco(다개체 월드 시뮬: 번식·섭식·굶주림 tick 진행, 8시나리오)
자율 oracle. 산출 `build_runs/autooracle-20260618-102954/`. ★주의: **시나리오단위 0.0은 측정 아티팩트** —
uniform한 status 키가 전 시나리오를 끌어내림. 진짜 신호는 **키 이름별 정확률**(하네스에 `key_accuracy_by_name` 추가).

- **키별: entities 0.875, status 0.0.** 즉 어려운 다개체 시뮬(entities)을 31B가 **7/8 완벽 계산** — 결합은
  계산을 안 깨뜨린다(빌드합의 eco 발견과 동형). 모든 실패가 또 계약-모호:
  - **status 8/8 실패 = 순수 enum 어휘**: 골든 전부 `"FINISHED"`, 31B는 `success`×16·`completed`×3·`ok`×2·
    `complete`·`running`. 의미는 정답(끝남), rules가 리터럴 토큰 미명세. 방치형 gameStatus와 100% 동형 → 계약 한 줄.
  - **SCN-004 entities 0/3(안정 1.0) = 번식 규칙 모호**: 골든 predator 2마리 각 energy4(번식 발생) vs 31B
    1마리 energy9(번식 안 하고 누적). **빌드합의도 흔들렸던 그 SCN-004 잔차(0.925≠1.0)를 빌드 0줄로 재발견** —
    번식 임계/타이밍이 rules에 안 박힘.
- **판정(thesis 강화)**: ① **결합도는 자율 oracle 계산을 안 깨뜨린다**(eco entities 7/8, 방치형과 동급). 깨는 건
  *미명세 계약*뿐(enum 어휘 + 번식 규칙). ② 자율 oracle 불일치 = **공짜 모호 탐지기**가 고결합서도 작동 —
  SCN-004 번식 잔차(사람이 알던 eco 약점)를 정확히 재지목. ③ G60~62 통합: 자율 oracle의 실패 표면은 *항상*
  계약 모호(산술 아님)이고, 박으면 닫힌다(G61 실증). 난이도는 "계산"이 아니라 "계약 명세"에 산다(G41~44 재확인).
- **측정 교훈(하네스)**: 자율 oracle은 *키별*로 봐야 한다. 한 모호키(status)가 있으면 시나리오단위 정확률은
  0으로 붕괴해 진짜 신호(entities 0.875)를 가린다. `auto_oracle.py`에 `key_accuracy_by_name` 헤드라인 추가.
- **다음**: eco 어휘+번식 박고 재측정(G61식 사다리 → entities 8/8·status 8/8 수렴 검증) / reconcile 배선 /
  31B self-suggest(자기 불일치 → 어느 계약줄 박을지 제안).
