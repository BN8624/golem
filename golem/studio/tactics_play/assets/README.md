# tactics_play/assets — 픽셀 에셋 + 비전 선택 산출물

**픽셀 팩: Kenney "Tiny Dungeon" (CC0, www.kenney.nl)** — 16×16 탑다운 타일 132개. CC0라 사용·수정·배포 자유(크레딧 권장).

## 추적(커밋)
- `tile_mapping.json` — 슬롯(hero/enemy/Hardened/Glass/Resonant/wall/conductive) → tile id. Gemma 비전이 시나리오에 맞게 고른 것(검증·동결).
- `tile_sprites.json` — 위 매핑의 선택 타일을 base64 PNG data URI로(렌더가 SVG 대신 로드, 게임 자족).

## 미추적(gitignore·재생성 가능)
- `tiny_dungeon/`(원본 팩 132 PNG)·`*.zip`·`contact_sheet.png`·`tiles_index.json`·`tile_preview.png`.

## 재생성
```
# 1) 팩 받기(CC0): kenney.nl Tiny Dungeon zip → tactics_play/assets/tiny_dungeon/ 로 추출
# 2) 컨택트시트
python golem/studio/gen_assets.py sheet
# 3) Gemma 비전 선택(★키) → 매핑·tile_sprites·미리보기
python golem/studio/gen_assets.py select --scenario "<테마>"
# 4) 렌더 반영
python golem/studio/gen_tactics_interactive.py
```
규율: 비전은 1회 골라 동결, 검증(id 유효·전 슬롯·hero≠enemy)으로 환각 거름, 룰·렌더는 결정적.
