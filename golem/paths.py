# 패키지 내 코드/데이터 디렉토리 위치를 한 곳에서 해석한다(레이아웃 재설계 후 경로 정본)
from pathlib import Path

PKG = Path(__file__).resolve().parent            # golem/ (패키지 루트)
REPO_ROOT = PKG.parent                           # 리포 루트(config.py·llm.py)

# 코드 서브패키지
CORE = PKG / "core"                              # 엔진·하네스(build_graded·gate·grading·계약·정적게이트·patch)
TOOLS = PKG / "tools"                            # 골렘 설계·선별·드라이버(planning·graft·card_delta·driver_autocard)
TACTICS = PKG / "tactics"                        # 전술 게임 생성기(gen_tactics_*·assets) + 데이터
VALIDATORS = PKG / "validators"                  # 검증·CI(verify_tactics·run_keyless·replay)

# 전술 데이터(tactics/ 하위)
BASES = TACTICS / "bases"                        # tactics_kernel_base·tactics_base_l7/l8/l9
PACKETS = TACTICS / "packets"                    # planning/design/specqa_packet_tactics_*
PLAY = TACTICS / "play"                          # 플레이 가능 산출물(index/play.html·levels·서사·에셋)

# 검증 데이터(validators/ 하위)
FIXTURES = VALIDATORS / "fixtures"               # replay 계약 픽스처
SCHEMAS = VALIDATORS / "schemas"                 # module_manifest.schema.json

# 생성물(gitignore 스크래치)
BUILD_RUNS = PKG / "build_runs"                  # 빌드/검증 워크스페이스·런 산출물
SCRATCH = BUILD_RUNS / "scratch"                 # 도구 기본 출력(planning/design/specqa_packet 등)
