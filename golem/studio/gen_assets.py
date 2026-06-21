# 에셋 비전 선택 파이프라인 — CC0 픽셀팩(Tiny Dungeon)을 컨택트시트로 만들고 Gemma 비전이 시나리오에 맞는 타일을 고름
"""B 경로(에셋팩 비전 선택). 룰 0·외형층.
  build-sheet: 132타일을 번호 라벨 격자(컨택트시트)로 + tiles_index.json(id→파일). (키0, PIL)
  select: 컨택트시트+엔티티 목록을 Gemma 비전에 1콜 → 엔티티별 tile_id 매핑(★키) → 검증(id 유효·커버리지)·동결.
  build-sprites: 동결 매핑 → 선택 타일을 base64 data URI로 → tile_sprites.json(렌더가 SVG 대신 로드).
규율: 비전은 1회 골라 동결, 검증으로 환각 거름, 룰·렌더는 결정적.
사용: python gen_assets.py sheet | select | sprites
"""

import argparse
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE / "tactics_play" / "assets" / "tiny_dungeon"
TILES = PACK / "Tiles"
OUT = HERE / "tactics_play" / "assets"
SHEET = OUT / "contact_sheet.png"
INDEX = OUT / "tiles_index.json"
MAPPING = OUT / "tile_mapping.json"

# 렌더가 채울 엔티티 슬롯(엔진 엔티티/지형 → 픽셀 타일).
SLOTS = ["floor", "hero", "enemy", "Hardened", "Glass", "Resonant", "wall", "conductive"]
SLOT_DESC = {
    "floor": "a plain dungeon FLOOR/ground tile (the base tile under every cell — neutral, tileable)",
    "hero": "the player HERO — a brave knight/swordsman/adventurer (the protagonist)",
    "enemy": "a generic basic ENEMY monster (grunt)",
    "Hardened": "an ARMORED/heavily-defended enemy (knight in heavy armor, golem)",
    "Glass": "a FRAGILE/crystalline/slime enemy (glass, slime, ghost-thin)",
    "Resonant": "a SPECTRAL/undead enemy (ghost, wraith, skeleton)",
    "wall": "a solid WALL/stone block terrain tile",
    "conductive": "a special glowing/magic FLOOR or rune tile (energy/conductive)",
}


def build_sheet(cols=12, scale=4, label_h=14):
    from PIL import Image, ImageDraw
    tiles = sorted(TILES.glob("tile_*.png"))
    ids = [int(t.stem.split("_")[1]) for t in tiles]
    ts = 16 * scale
    cell_w, cell_h = ts + 6, ts + label_h + 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell_w + 4, rows * cell_h + 4), (24, 26, 38, 255))
    d = ImageDraw.Draw(sheet)
    for i, (t, tid) in enumerate(zip(tiles, ids)):
        cx, cy = 4 + (i % cols) * cell_w, 4 + (i // cols) * cell_h
        im = Image.open(t).convert("RGBA").resize((ts, ts), Image.NEAREST)
        sheet.alpha_composite(im, (cx + 3, cy + 2))
        d.rectangle([cx + 2, cy + 1, cx + ts + 3, cy + ts + 2], outline=(60, 66, 90))
        d.text((cx + 3, cy + ts + 3), str(tid), fill=(220, 224, 240))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET)
    INDEX.write_text(json.dumps({tid: f"Tiles/tile_{tid:04d}.png" for tid in ids}, ensure_ascii=False), encoding="utf-8")
    print(f"  컨택트시트 {len(tiles)}타일({cols}×{rows}) → {SHEET}  index → {INDEX}")
    return len(tiles)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sheet", "select", "sprites"], help="sheet=컨택트시트 / select=비전 선택 / sprites=렌더 스프라이트")
    ap.add_argument("--scenario", default="변칙검술 성채 — 어두운 폐허 석조 던전, 마나 검사가 봉인의 핵으로", help="시나리오/테마(비전 선택 가이드)")
    ap.add_argument("--cap", type=int, default=3)
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    if args.cmd == "sheet":
        build_sheet()
        return 0
    if args.cmd == "select":
        return select(args)
    if args.cmd == "sprites":
        return sprites()
    return 1


def select(args):
    """Gemma 비전이 컨택트시트에서 슬롯별 tile_id를 고름 → 검증(id 유효·전 슬롯·hero≠enemy)·동결."""
    import os
    os.environ["GENERATOR_MODEL"] = "gemma-4-31b-it"; os.environ["CRITIC_MODEL"] = "gemma-4-31b-it"
    from config import get_api_keys
    from llm import KeyPool, LLMClient
    from planning import _extract_json
    if not SHEET.exists():
        build_sheet()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    valid = {int(k) for k in index}
    png = SHEET.read_bytes()
    slot_lines = "\n".join(f"  {s}: {SLOT_DESC[s]}" for s in SLOTS)
    base = (f"이 이미지는 16x16 픽셀 타일 132개를 번호(각 타일 아래 작은 숫자=id)와 함께 격자로 배열한 컨택트시트다. "
            f"타일을 실제로 '보고', 아래 각 슬롯에 가장 잘 맞는 tile id를 하나씩 골라라. "
            f"시나리오 테마: {args.scenario}. 테마·역할에 어울리게, hero와 enemy류는 서로 다른 타일로.\n슬롯:\n{slot_lines}\n"
            f"JSON 오브젝트 하나만 출력(마크다운 없이): {{" + ", ".join(f'"{s}": <id>' for s in SLOTS) + "}")
    pool = KeyPool(get_api_keys(), models=["gemma-4-31b-it"])
    feedback = ""
    for attempt in range(1, args.cap + 1):
        print(f"[SELECT] 시도 {attempt}/{args.cap} — Gemma 비전 선택 (★키)")
        with pool.checkout() as k:
            raw = LLMClient(api_key=k).generate("generator", base + feedback, images=[png])
        try:
            m = _extract_json(raw)
        except Exception as e:  # noqa: BLE001
            feedback = f"\n직전 JSON 파싱 실패({e}). JSON 오브젝트만."; print("  파싱 실패"); continue
        errs = []
        for s in SLOTS:
            v = m.get(s)
            if not isinstance(v, int) or v not in valid:
                errs.append(f"{s}={v}(무효)")
        if isinstance(m.get("hero"), int) and m.get("hero") == m.get("enemy"):
            errs.append("hero==enemy(구분 필요)")
        if errs:
            feedback = f"\n직전 실패: {errs[:4]} — 유효 id(0~131)로 다시, hero≠enemy."; print(f"  검증 실패: {errs[:4]}"); continue
        mp = {s: m[s] for s in SLOTS}
        MAPPING.write_text(json.dumps(mp, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  채택 — 매핑 {mp} → {MAPPING}")
        sprites(mp)
        return 0
    print("[SELECT] 실패 — --cap↑ 또는 시나리오 문구 조정."); return 1


def sprites(mp=None):
    """동결 매핑 → 선택 타일을 base64 PNG data URI로 tile_sprites.json + 미리보기 시트."""
    from PIL import Image, ImageDraw
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    if mp is None:
        mp = json.loads(MAPPING.read_text(encoding="utf-8"))
    out, prev_imgs = {}, []
    for slot, tid in mp.items():
        p = PACK / index[str(tid)]
        out[slot] = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
        prev_imgs.append((slot, tid, p))
    (OUT / "tile_sprites.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    sc = 48; sheet = Image.new("RGBA", (len(prev_imgs) * (sc + 8) + 8, sc + 34), (24, 26, 38, 255))
    d = ImageDraw.Draw(sheet)
    for i, (slot, tid, p) in enumerate(prev_imgs):
        x = 8 + i * (sc + 8)
        sheet.alpha_composite(Image.open(p).convert("RGBA").resize((sc, sc), Image.NEAREST), (x, 8))
        d.text((x, sc + 12), f"{slot[:7]}", fill=(220, 224, 240)); d.text((x, sc + 22), f"#{tid}", fill=(150, 156, 180))
    sheet.save(OUT / "tile_preview.png")
    print(f"  tile_sprites.json + tile_preview.png 작성(슬롯 {len(out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
