#!/usr/bin/env python3
"""Check the generated pack for mistakes Hytale would reject or hide.

There is no headless Hytale to load the pack in CI, so this checks what can
be checked offline: every JSON parses, every texture, icon and translation an
item points at exists, and every Parent or recipe input is either one of our
items or a known vanilla one.

    python3 tools/check_pack.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack" / "MoreDyes"

# Vanilla assets the pack refers to. Add to these when using new ones.
VANILLA_ITEMS = {"Wood_Oak_Trunk", "Wood_Softwood_Planks"}
VANILLA_TEXTURES = {"BlockTextures/Wood_Trunk_Oak_Side.png"}

errors = []


def error(msg):
    errors.append(msg)


def textures_of(block_type):
    for entry in block_type.get("Textures", []):
        for key, value in entry.items():
            if key != "Weight":
                yield value


def main():
    manifest = json.loads((PACK / "manifest.json").read_text())
    for field in ("Name", "Version"):
        if not manifest.get(field):
            error("manifest.json: missing %s" % field)

    lang = {}
    for line in (PACK / "Server/Languages/en-US/server.lang").read_text().splitlines():
        if line.strip():
            key, _, value = line.partition(" = ")
            if key in lang:
                error("server.lang: duplicate key %s" % key)
            lang[key] = value

    files = sorted((PACK / "Server/Item/Items").glob("*.json"))
    ids = {f.stem for f in files}
    for f in files:
        try:
            item = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            error("%s: invalid JSON (%s)" % (f.name, e))
            continue
        parent = item.get("Parent")
        if parent and parent not in ids | VANILLA_ITEMS:
            error("%s: unknown Parent %s" % (f.name, parent))
        name = item.get("TranslationProperties", {}).get("Name", "")
        if name.removeprefix("server.") not in lang:
            error("%s: no server.lang entry for %s" % (f.name, name))
        icon = item.get("Icon")
        if not icon or not (PACK / "Common" / icon).is_file():
            error("%s: missing icon %s" % (f.name, icon))
        block = item.get("BlockType", {})
        for tex in textures_of(block):
            if tex not in VANILLA_TEXTURES and not (PACK / "Common" / tex).is_file():
                error("%s: missing texture %s" % (f.name, tex))
        drop = block.get("Gathering", {}).get("Breaking", {}).get("ItemId")
        if drop and drop not in ids | VANILLA_ITEMS:
            error("%s: drops unknown item %s" % (f.name, drop))
        for ingredient in item.get("Recipe", {}).get("Input", []):
            needed = ingredient.get("ItemId")
            if needed and needed not in ids | VANILLA_ITEMS:
                error("%s: recipe needs unknown item %s" % (f.name, needed))

    for e in errors:
        print("error:", e)
    print("Checked %d items: %d errors" % (len(files), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
