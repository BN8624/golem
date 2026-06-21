# 전술 SRPG SVG 에셋팩(코드 저작·CC0급 원본) — 변칙검술 성채 테마. 렌더러가 엔티티/지형별로 그림(읽기전용·결정적)
"""클로드가 직접 만든 벡터 스프라이트 카탈로그. 래스터 아트 대신 SVG(텍스트)라 키0·결정적·라이선스 자유.
키: hero / enemy(기본 적) / Hardened·Glass·Resonant(unit_type별) / wall·conductive(지형). 모두 viewBox 0 0 100 100.
gen_tactics_interactive·gen_tactics_play가 import해 HTML에 주입, canvas가 data URI 이미지로 그린다."""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

SPRITES = {
    # 변칙검사 — 어두운 검사 + 청록 변칙 검광
    "hero": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<defs><radialGradient id='hg' cx='50%' cy='40%'><stop offset='0%' stop-color='#7fd4ff'/><stop offset='100%' stop-color='#2b6fb0'/></radialGradient></defs>
<circle cx='50' cy='52' r='34' fill='url(#hg)' stroke='#0d2a44' stroke-width='3'/>
<path d='M50 22 L58 50 L50 60 L42 50 Z' fill='#0d2a44'/>
<rect x='66' y='18' width='6' height='52' rx='3' fill='#bfefff' transform='rotate(20 69 44)'/>
<rect x='64' y='60' width='12' height='8' rx='2' fill='#0d2a44' transform='rotate(20 70 64)'/>
<circle cx='50' cy='46' r='6' fill='#eaffff'/></svg>""",
    # 기본 적 — 붉은 졸병
    "enemy": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<circle cx='50' cy='52' r='32' fill='#d63b48' stroke='#5a0f16' stroke-width='3'/>
<path d='M30 40 L42 46 M70 40 L58 46' stroke='#5a0f16' stroke-width='4' stroke-linecap='round'/>
<path d='M40 64 Q50 58 60 64' stroke='#5a0f16' stroke-width='4' fill='none' stroke-linecap='round'/></svg>""",
    # Hardened — 강철 갑주(방패·리벳)
    "Hardened": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<path d='M50 18 L80 30 V56 Q80 78 50 88 Q20 78 20 56 V30 Z' fill='#8893a3' stroke='#3a414d' stroke-width='4'/>
<path d='M50 30 V78 M32 38 H68' stroke='#3a414d' stroke-width='3'/>
<circle cx='32' cy='34' r='3' fill='#3a414d'/><circle cx='68' cy='34' r='3' fill='#3a414d'/></svg>""",
    # Glass — 투명 유리 결정(면 분할)
    "Glass": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<polygon points='50,16 78,40 66,82 34,82 22,40' fill='#7fe9e0' fill-opacity='0.55' stroke='#1aa79b' stroke-width='3'/>
<path d='M50 16 L50 82 M22 40 L78 40 M34 82 L50 40 L66 82' stroke='#d8fffb' stroke-width='2' fill='none'/></svg>""",
    # Resonant — 보랏빛 잔향(이중 윤곽 메아리)
    "Resonant": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<circle cx='50' cy='52' r='32' fill='none' stroke='#b06bff' stroke-width='2' stroke-opacity='0.5'/>
<circle cx='50' cy='52' r='25' fill='#6b2fb0' stroke='#d8b0ff' stroke-width='3'/>
<circle cx='50' cy='52' r='14' fill='none' stroke='#e5d8ff' stroke-width='2'/>
<circle cx='50' cy='48' r='4' fill='#eaccff'/></svg>""",
    # Wall — 돌 블록
    "wall": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<rect x='6' y='6' width='88' height='88' rx='6' fill='#4a4f5e' stroke='#2a2e38' stroke-width='4'/>
<path d='M6 50 H94 M50 6 V50 M30 50 V94 M70 50 V94' stroke='#2a2e38' stroke-width='3'/></svg>""",
    # Conductive — 룬 에너지 타일(청록 발광)
    "conductive": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
<rect x='6' y='6' width='88' height='88' rx='6' fill='#0c3b3a' stroke='#21d3c8' stroke-width='4'/>
<path d='M50 20 L40 52 H56 L46 80' stroke='#7ffff4' stroke-width='5' fill='none' stroke-linecap='round' stroke-linejoin='round'/>
<circle cx='50' cy='50' r='40' fill='none' stroke='#21d3c8' stroke-width='1.5' stroke-opacity='0.5'/></svg>""",
}
