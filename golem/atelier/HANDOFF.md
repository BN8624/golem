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

## ⚠ 진행 중 이슈 — 한국어 synthesis가 빈 패킷 반환 (미해결)

`planning.py` 프롬프트에 "로그라인과 같은 언어로 써라"(LANGUAGE 줄)를 박은 뒤, **한국어** 로그라인으로
synthesize하면 synth가 빈 dict를 반환해 `decisions/canon 0 → OPEN → exit 1`. **영어 출력일 땐 정상(FROZEN)**.

- 유력 원인: 한국어 synthesis JSON(긴 premise+canon+decisions)이 **출력 토큰 상한에 잘려** brace 매칭 실패.
- 진단 계측 추가됨(미커밋 아님, 커밋됨): `RealCaller.synth`가 파싱 실패 시 `runs/_synth_raw.txt`에
  raw 응답(len·head·tail)을 덤프한다.

### 다음 액션 (순서대로)

1. **재실행 + 원인 확정**: `python planning.py --idea "전쟁에서 왼팔을 잃은 검사와 그의 여동생이 죽은 왕의 비밀을 좇는다." --synthesize --out runs/bible_packet_ko`
   → 실패하면 `runs/_synth_raw.txt`를 읽는다. `len`이 상한 근처고 `tail`이 JSON 중간에서 끊겼으면 **잘림 확정**.
2. **고치기** (잘림이면): `lib/llm.py` generate config에 `max_output_tokens` 상향, 또는 synthesis를
   2콜로 분할(canon 따로), 또는 synthesis JSON을 줄인다(terms/scope 생략). 가장 싼 건 출력 상한 상향.
3. 고쳐서 한국어 FROZEN 바이블이 나오면 **진단 덤프(synth raw) 코드 제거**.
4. **end-to-end 1회**(★키): 생성된 한국어 바이블의 canon 일부를 일부러 위반하는 초고 + `cases.json`을 만들어
   `python canon_check.py --fixtures <그 폴더> --n 3` → planning→QA 사슬을 실콜로 증명.

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
