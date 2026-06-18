# 키0 검증 스위트를 한 번에 돌려 CI 게이트로 쓴다(API 콜0, Python+Node만 필요)
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent  # 내부 golem 패키지 디렉토리

# (이름, 스크립트) — 전부 키0. 게이트/역산은 Node 필요.
# _derive_l4_goldens는 _validate_l4_keyless가 읽는 참조 산출물(build_runs, gitignore)을 키0으로 재생성한다.
TESTS = [
    ("contract replay", "replay.py"),
    ("레버4 골든 역산(setup)", "_derive_l4_goldens.py"),
    ("레버4 selective keyless", "_validate_l4_keyless.py"),
    ("레버4 patch keyless", "_validate_l4_patch_keyless.py"),
    ("게이트 전 시나리오 검사(외부리뷰 #2)", "_gate_allscenarios_keyless.py"),
    ("FROZEN BLOCKING 흡수(외부리뷰 #1)", "_freeze_blocking_keyless.py"),
]


def main():
    try:
        sys.path.insert(0, str(PKG.parent))  # 루트에 config.py
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    env = {**os.environ, "PYTHONUTF8": "1"}
    results = []

    r = subprocess.run([sys.executable, "-m", "compileall", "-q", str(PKG)], env=env)
    results.append(("compileall", r.returncode == 0))

    for name, script in TESTS:
        print(f"\n----- {name} ({script}) -----")
        r = subprocess.run([sys.executable, script], cwd=str(HERE), env=env)
        results.append((name, r.returncode == 0))

    print("\n===== 키0 스위트 =====")
    allok = True
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        allok = allok and ok
    print("RESULT:", "ALL PASS" if allok else "FAIL")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
