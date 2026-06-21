# 에셋 비전 선택 파이프라인 — CC0 픽셀팩을 컨택트시트로 만들고 Gemma 비전이 시나리오에 맞는 타일을 고름(팩 무관)
"""B 경로(에셋팩 비전 선택). 룰 0·외형층. 클로드는 하네스(슬라이스·컨택트시트·렌더)만, 타일 선택은 골렘 비전이.
  sheet : 팩 타일을 번호 라벨 격자(컨택트시트) + tiles_index. 시트형 팩(roguelike)은 먼저 슬라이스. (키0, PIL)
  select: 컨택트시트+슬롯 목록을 Gemma 비전에 1콜 → 슬롯별 tile_id 매핑(★키) → 검증(id 유효·커버리지)·동결.
  sprites: 동결 매핑 → 선택 타일을 base64 data URI로 → tile_sprites.json(렌더가 SVG 대신 로드, 슬롯 병합).
규율: 비전은 1회 골라 동결, 검증으로 환각 거름, 룰·렌더는 결정적. (외형도 골렘이 — 클로드는 하네스만.)
사용: python gen_assets.py {sheet|select|sprites} [--pack tiny_dungeon|roguelike] [--slots floor,wall,...]
"""

import argparse
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "tactics_play" / "assets"
SPRITES_OUT = ASSETS / "tile_sprites.json"  # 렌더가 읽는 병합 산출(슬롯→base64). 추적·게임 자족.

# 팩 레지스트리. folder=개별 PNG 폴더(tiny_dungeon) / sheet=단일 스프라이트시트(슬라이스 필요).
PACKS = {
    "tiny_dungeon": {"dir": ASSETS / "tiny_dungeon", "sheet": None, "ts": 16, "margin": 0, "cols": 12, "legacy": True},
    "roguelike": {"dir": ASSETS / "roguelike_rpg", "sheet": "Spritesheet/roguelikeSheet_transparent.png",
                  "ts": 16, "margin": 1, "cols": 24, "legacy": False},
}

# 렌더가 채울 엔티티/지형 슬롯.
SLOTS = ["floor", "hero", "enemy", "Hardened", "Glass", "Resonant", "wall", "conductive"]
SLOT_DESC = {
    "floor": "a plain dungeon/stone FLOOR ground tile (the base tile under every cell — neutral, tileable)",
    "hero": "the player HERO — a brave knight/swordsman/adventurer (the protagonist)",
    "enemy": "a generic basic ENEMY monster (grunt)",
    "Hardened": "an ARMORED/heavily-defended enemy (knight in heavy armor, golem)",
    "Glass": "a FRAGILE/crystalline/slime enemy (glass, slime, ghost-thin)",
    "Resonant": "a SPECTRAL/undead enemy (ghost, wraith, skeleton)",
    "wall": "a solid WALL/stone block terrain tile",
    "conductive": "a special glowing/magic FLOOR or rune tile (energy/conductive)",
}


def paths(pack):
    """팩별 컨택트시트/인덱스/매핑 경로. tiny_dungeon은 레거시 파일명 유지(이미 커밋됨)."""
    p = PACKS[pack]
    if p["legacy"]:
        return {"sheet": ASSETS / "contact_sheet.png", "index": ASSETS / "tiles_index.json",
                "mapping": ASSETS / "tile_mapping.json", "preview": ASSETS / "tile_preview.png"}
    return {"sheet": ASSETS / f"contact_{pack}.png", "index": ASSETS / f"tiles_index_{pack}.json",
            "mapping": ASSETS / f"tile_mapping_{pack}.json", "preview": ASSETS / f"tile_preview_{pack}.png"}


def ensure_tiles(pack):
    """시트형 팩이면 스프라이트시트를 개별 타일 PNG(dir/Tiles/tile_NNNN.png)로 슬라이스(멱등)."""
    p = PACKS[pack]
    if not p["sheet"]:
        return
    from PIL import Image
    tiles_dir = p["dir"] / "Tiles"
    sheet = Image.open(p["dir"] / p["sheet"]).convert("RGBA")
    ts, m = p["ts"], p["margin"]
    stride = ts + m
    cols = (sheet.width + m) // stride
    rows = (sheet.height + m) // stride
    if tiles_dir.exists() and len(list(tiles_dir.glob("tile_*.png"))) >= cols * rows - cols:
        return  # 이미 슬라이스됨
    tiles_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in range(rows):
        for c in range(cols):
            x, y = c * stride, r * stride
            til = sheet.crop((x, y, x + ts, y + ts))
            if til.getbbox() is None:  # 완전 투명 타일은 건너뜀
                continue
            til.save(tiles_dir / f"tile_{r * cols + c:04d}.png")
            n += 1
    print(f"  슬라이스 {n}타일({cols}×{rows} 격자) → {tiles_dir}")


def build_sheet(pack, scale=3, label_h=14):
    from PIL import Image, ImageDraw
    p = PACKS[pack]
    ensure_tiles(pack)
    pp = paths(pack)
    cols = p["cols"]
    tiles = sorted((p["dir"] / "Tiles").glob("tile_*.png"))
    ids = [int(t.stem.split("_")[1]) for t in tiles]
    ts = p["ts"] * scale
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
    pp["sheet"].parent.mkdir(parents=True, exist_ok=True)
    sheet.save(pp["sheet"])
    pp["index"].write_text(json.dumps({tid: f"Tiles/tile_{tid:04d}.png" for tid in ids}, ensure_ascii=False),
                           encoding="utf-8")
    print(f"  컨택트시트 {len(tiles)}타일({cols}×{rows}) → {pp['sheet']}  index → {pp['index']}")
    return len(tiles)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sheet", "select", "sprites"], help="sheet=컨택트시트 / select=비전 선택 / sprites=렌더 스프라이트")
    ap.add_argument("--pack", default="tiny_dungeon", choices=list(PACKS), help="에셋 팩")
    ap.add_argument("--slots", default=None, help="선택할 슬롯 부분집합(쉼표). 생략=전체. 예: floor,wall,conductive")
    ap.add_argument("--scenario", default="변칙검술 성채 — 어두운 폐허 석조 던전, 마나 검사가 봉인의 핵으로", help="시나리오/테마(비전 선택 가이드)")
    ap.add_argument("--cap", type=int, default=3)
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    slots = [s.strip() for s in args.slots.split(",")] if args.slots else SLOTS
    bad = [s for s in slots if s not in SLOT_DESC]
    if bad:
        print(f"  알 수 없는 슬롯: {bad}"); return 1

    if args.cmd == "sheet":
        build_sheet(args.pack); return 0
    if args.cmd == "select":
        return select(args.pack, slots, args.scenario, args.cap)
    if args.cmd == "sprites":
        return sprites(args.pack, None, slots)
    return 1


def select(pack, slots, scenario, cap):
    """Gemma 비전이 컨택트시트에서 슬롯별 tile_id를 고름 → 검증(id 유효·전 슬롯·hero≠enemy)·동결·병합."""
    import os
    os.environ["GENERATOR_MODEL"] = "gemma-4-31b-it"; os.environ["CRITIC_MODEL"] = "gemma-4-31b-it"
    from config import get_api_keys
    from llm import KeyPool, LLMClient
    from planning import _extract_json
    pp = paths(pack)
    if not pp["sheet"].exists():
        build_sheet(pack)
    index = json.loads(pp["index"].read_text(encoding="utf-8"))
    valid = {int(k) for k in index}
    png = pp["sheet"].read_bytes()
    slot_lines = "\n".join(f"  {s}: {SLOT_DESC[s]}" for s in slots)
    base = (f"이 이미지는 16x16 픽셀 타일을 번호(각 타일 아래 작은 숫자=id)와 함께 격자로 배열한 컨택트시트다. "
            f"타일을 실제로 '보고', 아래 각 슬롯에 가장 잘 맞는 tile id를 하나씩 골라라. "
            f"시나리오 테마: {scenario}. 테마·역할에 어울리게, hero와 enemy류는 서로 다른 타일로.\n슬롯:\n{slot_lines}\n"
            f"JSON 오브젝트 하나만 출력(마크다운 없이): {{" + ", ".join(f'"{s}": <id>' for s in slots) + "}")
    pool = KeyPool(get_api_keys(), models=["gemma-4-31b-it"])
    feedback = ""
    for attempt in range(1, cap + 1):
        print(f"[SELECT:{pack}] 시도 {attempt}/{cap} — Gemma 비전 선택 {slots} (★키)")
        with pool.checkout() as k:
            raw = LLMClient(api_key=k).generate("generator", base + feedback, images=[png])
        try:
            m = _extract_json(raw)
        except Exception as e:  # noqa: BLE001
            feedback = f"\n직전 JSON 파싱 실패({e}). JSON 오브젝트만."; print("  파싱 실패"); continue
        errs = []
        for s in slots:
            v = m.get(s)
            if not isinstance(v, int) or v not in valid:
                errs.append(f"{s}={v}(무효)")
        if "hero" in slots and "enemy" in slots and m.get("hero") == m.get("enemy"):
            errs.append("hero==enemy(구분 필요)")
        if errs:
            feedback = f"\n직전 실패: {errs[:4]} — 유효 id로 다시, hero≠enemy."; print(f"  검증 실패: {errs[:4]}"); continue
        mp = {s: m[s] for s in slots}
        # 매핑 병합(팩별 파일).
        prev = json.loads(pp["mapping"].read_text(encoding="utf-8")) if pp["mapping"].exists() else {}
        prev.update(mp)
        pp["mapping"].write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  채택 — 매핑 {mp} → {pp['mapping']}")
        sprites(pack, mp, slots)
        return 0
    print(f"[SELECT:{pack}] 실패 — --cap↑ 또는 시나리오 문구 조정."); return 1


def sprites(pack, mp, slots):
    """동결 매핑 → 선택 타일을 base64 PNG data URI로 tile_sprites.json에 병합(다른 슬롯 보존) + 미리보기."""
    from PIL import Image, ImageDraw
    pp = paths(pack)
    index = json.loads(pp["index"].read_text(encoding="utf-8"))
    if mp is None:
        full = json.loads(pp["mapping"].read_text(encoding="utf-8"))
        mp = {s: full[s] for s in slots if s in full}
    out = json.loads(SPRITES_OUT.read_text(encoding="utf-8")) if SPRITES_OUT.exists() else {}
    prev_imgs = []
    for slot, tid in mp.items():
        p = PACKS[pack]["dir"] / index[str(tid)]
        out[slot] = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
        prev_imgs.append((slot, tid, p))
    SPRITES_OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    sc = 48; sheet = Image.new("RGBA", (len(prev_imgs) * (sc + 8) + 8, sc + 34), (24, 26, 38, 255))
    d = ImageDraw.Draw(sheet)
    for i, (slot, tid, p) in enumerate(prev_imgs):
        x = 8 + i * (sc + 8)
        sheet.alpha_composite(Image.open(p).convert("RGBA").resize((sc, sc), Image.NEAREST), (x, 8))
        d.text((x, sc + 12), f"{slot[:7]}", fill=(220, 224, 240)); d.text((x, sc + 22), f"#{tid}", fill=(150, 156, 180))
    sheet.save(pp["preview"])
    print(f"  tile_sprites.json 병합(이번 {len(prev_imgs)}슬롯, 총 {len(out)}) + 미리보기 {pp['preview'].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
