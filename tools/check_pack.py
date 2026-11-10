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
VANILLA_ITEMS = {
    "Wood_Oak_Trunk", "Wood_Softwood_Planks", "Rock_Stone", "Rock_Stone_Cobble", "Rock_Stone_Brick",
    "Rock_Stone_Brick_Smooth", "Rock_Marble", "Rock_Sandstone", "Soil_Sand", "Soil_Gravel",
    "Soil_Clay_Smooth_White", "Rock_Crystal_White_Block", "Cloth_Block_Wool_White",
    "Furniture_Crude_Candle", "Ingredient_Bar_Iron", "Plant_Petals_White", "Rock_Stone_Brick_Stairs",
    "Rock_Stone_Brick_Wall",
    "Storage_Drawer_Softwood",  # Wan's Storage Drawers, only in --drawers builds
} | {"Plant_Petals_" + c for c in (
    "Azure", "Black", "Blood", "Blue", "Cyan", "Green", "Orange", "Pink", "Purple", "Red", "Storm", "Yellow")}
VANILLA_TEXTURES = {
    "BlockTextures/Wood_Trunk_Oak_Side.png",
    "Blocks/Structures/Stairs/Stairs_Textures/Rock_Chalk_Brick_Stairs.png",
    "Blocks/Structures/Walls/Wall_Rock_Brick_Marble.png",
    "Resources/Plants/Petal_Textures/White.png",
}

errors = []


def error(msg):
    errors.append(msg)


def textures_of(block_type):
    """Every texture a block type or any of its states draws."""
    states = [block_type] + list(block_type.get("State", {}).get("Definitions", {}).values())
    for state in states:
        for entry in (state.get("Textures") or []) + (state.get("CustomModelTexture") or []):
            for key, value in entry.items():
                if key != "Weight":
                    yield value


def recipes_of(item):
    recipe = item.get("Recipe", [])
    return recipe if isinstance(recipe, list) else [recipe]


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
        for recipe in recipes_of(item):
            if not recipe.get("BenchRequirement"):
                error("%s: recipe has no bench" % f.name)
            for ingredient in recipe.get("Input", []):
                needed = ingredient.get("ItemId")
                if needed and needed not in ids | VANILLA_ITEMS:
                    error("%s: recipe needs unknown item %s" % (f.name, needed))
        light = block.get("Light")
        if light and not (isinstance(light.get("Color"), str) and len(light["Color"]) == 4):
            error("%s: light color should be #RGB like vanilla, got %s" % (f.name, light.get("Color")))
        patterns = block.get("ConnectedBlockRuleSet", {}).get("TemplateShapeBlockPatterns", {})
        for target in patterns.values():
            if target.lstrip("*").split("_State_")[0] not in ids:
                error("%s: connects to unknown block %s" % (f.name, target))

    for e in errors:
        print("error:", e)
    print("Checked %d items: %d errors" % (len(files), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
