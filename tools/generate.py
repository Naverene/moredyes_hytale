#!/usr/bin/env python3
"""Generate the More Dyes Hytale asset pack.

Every dyed block shares one light grey texture per block type and gets its
color from the BlockType "Tint" fields, the same idea as the tinted blocks in
the 1.16.5 mod. Logs only tint their end rings; the bark stays vanilla oak.

    python3 tools/generate.py               # all 118 colors
    python3 tools/generate.py --prototype   # just three, for quick tests
    python3 tools/generate.py --version 0.4.0   # set the manifest version (CI uses the tag)

Needs Pillow (pip install pillow). Output goes to pack/MoreDyes/.
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack" / "MoreDyes"
COLORS = json.loads((ROOT / "tools" / "colors.json").read_text())
PROTOTYPE_COLORS = ["e57f6c", "4d73c5", "b2d926"]
SIZE = 32
ICON = 64

MANIFEST = {
    "Group": "Naverene",
    "Name": "MoreDyes",
    "Version": "0.3.0",
    "Description": "118 extra dye colors: dyed stone, logs, planks and wool.",
    "Authors": [{"Name": "Naverene"}],
    "Website": "https://github.com/Naverene/moredyes_hytale",
    "ServerVersion": "*",
    "Dependencies": {},
    "OptionalDependencies": {},
    "DisabledByDefault": False,
}

# Vanilla texture used for the untinted log sides.
OAK_BARK = "BlockTextures/Wood_Trunk_Oak_Side.png"


# --- Textures -------------------------------------------------------------
# All grey and light, so the multiplied tint stays bright.

def gray(fn, seed):
    rng = random.Random(seed)
    img = Image.new("L", (SIZE, SIZE))
    for y in range(SIZE):
        for x in range(SIZE):
            img.putpixel((x, y), max(0, min(255, int(fn(x, y, rng)))))
    return img.convert("RGBA")


def stone_texture():
    def px(x, y, rng):
        v = rng.randint(212, 244)
        return v - 28 if x in (0, SIZE - 1) or y in (0, SIZE - 1) else v
    return gray(px, 1165)


def planks_texture():
    """Four horizontal boards with grain, seams and staggered board ends."""
    grain = [random.Random(7 + b).uniform(-6, 6) for b in range(SIZE)]
    ends = {0: 11, 1: 25, 2: 4, 3: 18}

    def px(x, y, rng):
        board, row = divmod(y, 8)
        if row == 7:
            return 168
        if x == ends[board]:
            return 182
        return 222 + grain[(x * 3 + board * 5) % SIZE] + grain[y] * 0.5 + rng.uniform(-5, 5)
    return gray(px, 21)


def log_top_texture():
    """End grain: growth rings around the centre and a darker bark rim."""
    c = (SIZE - 1) / 2

    def px(x, y, rng):
        if min(x, y, SIZE - 1 - x, SIZE - 1 - y) < 2:
            return 160 + rng.uniform(-8, 8)
        d = math.hypot(x - c, y - c)
        return 225 - 22 * (math.sin(d * 1.6) > 0.55) + rng.uniform(-5, 5)
    return gray(px, 33)


def wool_texture():
    """Soft fluffy noise with a faint weave."""
    def px(x, y, rng):
        weave = 6 if (x + y) % 4 == 0 else 0
        return 236 - weave + rng.uniform(-9, 7)
    return gray(px, 44)


def bark_preview_texture():
    """Brown stand-in for vanilla oak bark, only used to draw log icons."""
    rng = random.Random(55)
    img = Image.new("RGBA", (SIZE, SIZE))
    for y in range(SIZE):
        for x in range(SIZE):
            groove = 0.6 if (x + rng.randint(0, 1)) % 5 == 0 else 1.0
            s = rng.uniform(0.85, 1.05) * groove
            img.putpixel((x, y), (int(110 * s), int(74 * s), int(48 * s), 255))
    return img


def tinted(img, color):
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            v, _, _, a = px[x, y]
            px[x, y] = (v * r // 255, v * g // 255, v * b // 255, a)
    return out


# --- Icons ----------------------------------------------------------------

def shade(img, f):
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)
    return out


def face(tex, origin, eu, ev):
    """Map tex onto the parallelogram origin + u*eu + v*ev (u, v in texels)."""
    det = eu[0] * ev[1] - eu[1] * ev[0]
    a, b = ev[1] / det, -ev[0] / det
    d, e = -eu[1] / det, eu[0] / det
    c = -(a * origin[0] + b * origin[1])
    f = -(d * origin[0] + e * origin[1])
    return tex.transform((ICON, ICON), Image.AFFINE, (a, b, c, d, e, f), Image.NEAREST)


def cube_icon(top, side):
    """Isometric cube in the same three-quarter view as vanilla block icons."""
    s = 1.0 / SIZE
    half, quarter = ICON / 2 - 2, (ICON / 2 - 2) / 2
    top_pt, left, bottom = (ICON / 2, 2), (2, 2 + quarter), (ICON / 2, 2 + 2 * quarter)
    right = (ICON - 2, 2 + quarter)
    down = (0, (ICON - 4 - 2 * quarter) * s)
    icon = Image.new("RGBA", (ICON, ICON))
    for layer in (
        face(top, top_pt, (half * s, quarter * s), (-half * s, quarter * s)),
        face(shade(side, 0.82), left, (half * s, quarter * s), down),
        face(shade(side, 0.64), bottom, (half * s, -quarter * s), down),
    ):
        icon.alpha_composite(layer)
    return icon


# --- Block definitions ----------------------------------------------------

def stone(bid, color):
    return {
        "TranslationProperties": {"Name": "server." + bid + ".name"},
        "MaxStack": 100,
        "Icon": "Icons/ItemsGenerated/" + bid + ".png",
        "Categories": ["Blocks.Rocks"],
        "PlayerAnimationsId": "Block",
        "Set": "Rock_Stone",
        "BlockType": {
            "Material": "Solid",
            "DrawType": "Cube",
            "Group": "Stone",
            "Flags": {},
            "Gathering": {"Breaking": {"GatherType": "Rocks", "ItemId": bid}},
            "BlockParticleSetId": "Stone",
            "Textures": [{"All": "BlockTextures/MoreDyes_Stone.png"}],
            "Tint": ["#" + color],
            "ParticleColor": "#" + color,
            "BlockSoundSetId": "Stone",
            "BlockBreakingDecalId": "Breaking_Decals_Rock",
        },
        "ResourceTypes": [{"Id": "Rock"}],
    }


def log(bid, color):
    # Inherits rotation, sounds, support and stripping from vanilla oak.
    return {
        "TranslationProperties": {"Name": "server." + bid + ".name"},
        "Parent": "Wood_Oak_Trunk",
        "Icon": "Icons/ItemsGenerated/" + bid + ".png",
        "BlockType": {
            "Textures": [{
                "Sides": OAK_BARK,
                "UpDown": "BlockTextures/MoreDyes_Log_Top.png",
                "Weight": 1,
            }],
            "TintUp": ["#" + color],
            "TintDown": ["#" + color],
            "Gathering": {
                "Breaking": {"ItemId": bid, "GatherType": "Woods"},
                "Physics": {"ItemId": bid},
            },
            "ParticleColor": "#" + color,
        },
    }


def planks(bid, color):
    return {
        "TranslationProperties": {"Name": "server." + bid + ".name"},
        "Parent": "Wood_Softwood_Planks",
        "Icon": "Icons/ItemsGenerated/" + bid + ".png",
        "Recipe": {
            "Input": [{"ItemId": "MoreDyes_Log_" + color.upper(), "Quantity": 1}],
            "BenchRequirement": [{
                "Id": "Builders",
                "Type": "StructuralCrafting",
                "Categories": ["WoodPlanks"],
            }],
            "OutputQuantity": 1,
        },
        "BlockType": {
            "Textures": [{"All": "BlockTextures/MoreDyes_Planks.png", "Weight": 1}],
            "Tint": ["#" + color],
            "Gathering": {"Breaking": {"GatherType": "Woods", "ItemId": bid}},
            "ParticleColor": "#" + color,
        },
    }


def wool(bid, color):
    # Standalone copy of vanilla white cloth: inheriting from it would also
    # inherit its wool-bolt recipe. No recipe until there are dye items.
    return {
        "TranslationProperties": {"Name": "server." + bid + ".name"},
        "Icon": "Icons/ItemsGenerated/" + bid + ".png",
        "ItemLevel": 2,
        "Categories": ["Blocks.Rocks"],
        "PlayerAnimationsId": "Block",
        "BlockType": {
            "Material": "Solid",
            "DrawType": "Cube",
            "Group": "Cloth",
            "Flags": {},
            "Gathering": {"Breaking": {"GatherType": "SoftBlocks", "ItemId": bid}},
            "BlockParticleSetId": "Dust",
            "Textures": [{"All": "BlockTextures/MoreDyes_Wool.png", "Weight": 1}],
            "Tint": ["#" + color],
            "BlockSoundSetId": "Cloth",
            "ParticleColor": "#" + color,
        },
        "Tags": {"Type": ["Cloth"]},
        "ItemSoundSetId": "ISS_Items_Cloth",
    }


def main():
    colors = PROTOTYPE_COLORS if "--prototype" in sys.argv else COLORS
    if "--version" in sys.argv:
        MANIFEST["Version"] = sys.argv[sys.argv.index("--version") + 1]
    if PACK.exists():
        shutil.rmtree(PACK)
    textures = PACK / "Common" / "BlockTextures"
    icons = PACK / "Common" / "Icons" / "ItemsGenerated"
    items = PACK / "Server" / "Item" / "Items"
    lang = PACK / "Server" / "Languages" / "en-US"
    for d in (textures, icons, items, lang):
        d.mkdir(parents=True)
    (PACK / "manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")

    stone_tex, planks_tex = stone_texture(), planks_texture()
    log_tex, wool_tex = log_top_texture(), wool_texture()
    bark = bark_preview_texture()
    for name, tex in (("Stone", stone_tex), ("Planks", planks_tex),
                      ("Log_Top", log_tex), ("Wool", wool_tex)):
        tex.save(textures / ("MoreDyes_" + name + ".png"))

    # (id prefix, display name, definition, icon top, icon side, side tinted?)
    kinds = [
        ("Stone", "Stone", stone, stone_tex, stone_tex, True),
        ("Log", "Log", log, log_tex, bark, False),
        ("Planks", "Planks", planks, planks_tex, planks_tex, True),
        ("Wool", "Wool", wool, wool_tex, wool_tex, True),
    ]
    lines = []
    for prefix, name, define, top, side, side_tinted in kinds:
        for color in colors:
            bid = "MoreDyes_" + prefix + "_" + color.upper()
            (items / (bid + ".json")).write_text(json.dumps(define(bid, color), indent=2) + "\n")
            icon_side = tinted(side, color) if side_tinted else side
            cube_icon(tinted(top, color), icon_side).save(icons / (bid + ".png"))
            lines.append(bid + ".name = " + color.upper() + " " + name)
    (lang / "server.lang").write_text("\n".join(lines) + "\n")
    print("Wrote %d blocks to %s" % (len(lines), PACK.relative_to(ROOT)))


if __name__ == "__main__":
    main()
