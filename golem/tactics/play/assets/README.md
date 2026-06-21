# tactics_play/assets — 픽셀 에셋 + 골렘 비전 선택 산출물

외형도 골렘이 고른다. 클로드는 하네스(슬라이스·컨택트시트·렌더)만, **어떤 타일이냐는 골렘 비전**(`gen_assets.py select`)이 고른다. `gen_assets.py`는 팩 무관(`--pack`).

**CC0 팩(www.kenney.nl, 자유 사용·수정·배포, 크레딧 권장):**
- **Kenney "Tiny Dungeon"** — 16×16 탑다운 132타일. 현재 **캐릭터 슬롯**(hero/enemy/Hardened/Glass/Resonant) 출처.
- **Kenney "Roguelike/RPG"** — 16×16 시트(1704타일, 1px margin). 현재 **지형 슬롯**(floor/wall/conductive) 출처. 시트형이라 `gen_assets`가 개별 타일로 슬라이스.

## 추적(커밋 — 게임 자족)
- `tile_sprites.json` — 슬롯→base64 PNG data URI. **두 팩의 선택 타일을 병합**(렌더가 SVG 대신 로드). 슬롯=floor/hero/enemy/Hardened/Glass/Resonant/wall/conductive.
- `tile_mapping.json`(tiny_dungeon) · `tile_mapping_roguelike.json`(roguelike) — 슬롯→tile id. 골렘 비전이 고른 것(검증·동결).

## 미추적(gitignore·재생성 가능)
- `tiny_dungeon/`·`roguelike_rpg/`(원본 팩)·`*.zip`·`contact_sheet.png`·`contact_roguelike.png`·`tiles_index*.json`·`tile_preview*.png`.

## 재생성
```
# 1) 팩 받기(CC0) → assets/<pack>/ 로. roguelike는 단일 스프라이트시트(gen_assets가 슬라이스).
# 2) 컨택트시트(시트형 팩은 자동 슬라이스). --solid=불투명도 필터(투명 장식 제거·비전 가독성↑, 바닥/벽 권장 0.9)
python golem/gen_assets.py sheet --pack roguelike --solid 0.9
# 3) 골렘 비전 선택(★키). --slots=부분집합(생략=전체), 결과는 tile_sprites.json에 병합
python golem/gen_assets.py select --pack roguelike --slots floor,wall,conductive --solid 0.9 --scenario "<테마>"
python golem/gen_assets.py select --pack tiny_dungeon --slots hero,enemy,Hardened,Glass,Resonant --scenario "<테마>"
# 4) 렌더 반영
python golem/gen_tactics_interactive.py --level l9
```
규율: 비전은 1회 골라 동결, 검증(id 유효·전 슬롯·hero≠enemy·솔리드 필터)으로 환각 거름, 룰·렌더는 결정적.

**퀄리티 천장 = 에셋**(파이프라인 아님). 여기선 래스터 픽셀아트 생성 불가 — 좋은 에셋(AI 생성·유료 매칭팩)을 떨구면 동일 하네스가 통합한다. CC0 무료는 "되긴 되는데 밋밋".
