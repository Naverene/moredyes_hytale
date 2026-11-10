#!/usr/bin/env python3
"""Generate the More Dyes Hytale asset pack.

Every dyed block shares one light grey texture per block type and gets its
color from the BlockType "Tint" fields, the same idea as the tinted blocks in
the Minecraft versions. Logs only tint their end rings; the bark stays vanilla
oak. Half slabs draw a 3D model, so they get one pre-colored texture per color
instead of a tint.

    python3 tools/generate.py               # all 118 colors
    python3 tools/generate.py --prototype   # just three, for quick tests
    python3 tools/generate.py --version 0.4.0   # set the manifest version (CI uses the tag)
    python3 tools/generate.py --drawers     # also dyed Wan's Storage Drawers (test build)

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
BASE = ROOT / "tools" / "base"
COLORS = json.loads((ROOT / "tools" / "colors.json").read_text())
DYE_RECIPES = json.loads((ROOT / "tools" / "dye_recipes.json").read_text())
PROTOTYPE_COLORS = ["e57f6c", "4d73c5", "b2d926"]
SIZE = 32
ICON = 64

MANIFEST = {
    "Group": "Naverene",
    "Name": "MoreDyes",
    "Version": "0.4.0",
    "Description": "118 extra dye colors: dyes, dyed stone, bricks, wood, wool, sand, granite, "
                   "slabs and lamps with colored light.",
    "Authors": [{"Name": "Naverene"}, {"Name": "kg6jay"}],
    "Website": "https://github.com/Naverene/moredyes_hytale",
    "ServerVersion": "*",
    "Dependencies": {},
    "OptionalDependencies": {},
    "DisabledByDefault": False,
}

# Vanilla texture used for the untinted log sides.
OAK_BARK = "BlockTextures/Wood_Trunk_Oak_Side.png"
# Light vanilla textures for the shapes that use Hytale's own models. These get
# the dye color from Tint, which still needs checking in game for models.
STAIRS_TEXTURE = "Blocks/Structures/Stairs/Stairs_Textures/Rock_Chalk_Brick_Stairs.png"
WALL_TEXTURE = "Blocks/Structures/Walls/Wall_Rock_Brick_Marble.png"
PETAL_TEXTURE = "Resources/Plants/Petal_Textures/White.png"

# Minecraft dyes in the More Dyes mixing recipes, as Hytale petals.
PETALS = {
    "white": ["White"], "orange": ["Orange"], "magenta": ["Pink", "Purple"],
    "light_blue": ["Azure"], "yellow": ["Yellow"], "lime": ["Green", "Yellow"],
    "pink": ["Pink"], "gray": ["Black", "White"], "light_gray": ["Black", "White", "White"],
    "cyan": ["Cyan"], "purple": ["Purple"], "blue": ["Blue"], "brown": ["Orange", "Black"],
    "green": ["Green"], "red": ["Red"], "black": ["Black"],
}

WORKBENCH = [{"Id": "Workbench", "Type": "Crafting", "Categories": ["Workbench_Crafting"]}]
TEXTILES = [{"Id": "Furniture_Bench", "Type": "Crafting", "Categories": ["Furniture_Textiles"]}]
LIGHTING = [{"Id": "Furniture_Bench", "Type": "Crafting", "Categories": ["Furniture_Lighting"]}]


def builders(category):
    return [{"Id": "Builders", "Type": "StructuralCrafting", "Categories": [category]}]


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


def cobble_texture():
    """Rounded stones with dark gaps, from the nearest of a few random centres."""
    rng = random.Random(77)
    seeds = [(rng.uniform(0, SIZE), rng.uniform(0, SIZE), rng.randint(200, 240)) for _ in range(14)]

    def px(x, y, r):
        dists = []
        for sx, sy, v in seeds:
            dx = min(abs(x - sx), SIZE - abs(x - sx))
            dy = min(abs(y - sy), SIZE - abs(y - sy))
            dists.append((math.hypot(dx, dy), v))
        dists.sort()
        (d1, v), (d2, _) = dists[0], dists[1]
        if d2 - d1 < 1.3:
            return 150 + r.uniform(-8, 8)
        return v - d1 * 1.5 + r.uniform(-6, 6)
    return gray(px, 78)


def brick_texture():
    """Four rows of bricks with mortar lines, every other row offset."""
    def px(x, y, rng):
        row, ry = divmod(y, 8)
        bx = (x + (8 if row % 2 else 0)) % 16
        if ry == 7 or bx == 15:
            return 168
        edge = 10 if ry == 0 or bx == 0 else 0
        return 230 + edge - (8 if ry == 6 or bx == 14 else 0) + rng.uniform(-6, 6)
    return gray(px, 91)


def smooth_texture():
    def px(x, y, rng):
        if x in (0, SIZE - 1) or y in (0, SIZE - 1):
            return 196
        return 232 + rng.uniform(-3, 3)
    return gray(px, 92)


def marble_texture():
    """Pale stone with a few soft darker veins."""
    rng = random.Random(93)
    veins = [(rng.uniform(0, 6.28), rng.uniform(0.15, 0.35), rng.uniform(0, SIZE)) for _ in range(3)]

    def px(x, y, r):
        v = 240 + r.uniform(-4, 4)
        for phase, freq, off in veins:
            line = off + 6 * math.sin(x * freq + phase)
            d = abs((y - line + SIZE / 2) % SIZE - SIZE / 2)
            if d < 1.2:
                v -= 26
            elif d < 2.2:
                v -= 10
        return v
    return gray(px, 94)


def sandstone_texture():
    """Horizontal layers, with a cap band at the top."""
    bands = [random.Random(95 + i).uniform(-8, 8) for i in range(SIZE)]

    def px(x, y, rng):
        if y < 3:
            return 238 + rng.uniform(-3, 3)
        if y == 3:
            return 200
        return 226 + bands[y // 3] + rng.uniform(-4, 4)
    return gray(px, 96)


def sand_texture():
    def px(x, y, rng):
        return 232 + rng.choice((-14, -6, 0, 0, 0, 4, 8)) + rng.uniform(-3, 3)
    return gray(px, 97)


def gravel_texture():
    """Small pebbles of different shades."""
    rng = random.Random(98)
    pebbles = [(rng.uniform(0, SIZE), rng.uniform(0, SIZE), rng.uniform(1.8, 3.6), rng.randint(170, 240))
               for _ in range(60)]

    def px(x, y, r):
        v = 150
        for sx, sy, rad, shade in pebbles:
            if math.hypot(x - sx, y - sy) < rad:
                v = shade
        return v + r.uniform(-6, 6)
    return gray(px, 99)


def clay_texture():
    """Smooth clay, the Hytale stand-in for terracotta: flat with faint speckles."""
    def px(x, y, rng):
        return 224 + (-14 if rng.random() < 0.05 else 0) + rng.uniform(-3, 3)
    return gray(px, 100)


def crystal_texture():
    """Faceted crystal, bright with darker facet lines."""
    def px(x, y, rng):
        d = (x + y) % 16
        e = (x - y) % 16
        v = 236 + rng.uniform(-4, 4)
        if d in (0, 1) or e in (0, 1):
            v -= 34
        if x in (0, SIZE - 1) or y in (0, SIZE - 1):
            v -= 20
        return v
    return gray(px, 101)


def lamp_texture(lit):
    """A frame around four glowing panes; the unlit one is dark."""
    def px(x, y, rng):
        frame = x in (0, 1, SIZE - 2, SIZE - 1) or y in (0, 1, SIZE - 2, SIZE - 1) or x in (15, 16) or y in (15, 16)
        if frame:
            return (150 if lit else 60) + rng.uniform(-6, 6)
        cx, cy = x % 16 - 7.5, y % 16 - 7.5
        glow = 255 - 2.0 * math.hypot(cx, cy)
        return (glow if lit else glow * 0.32) + rng.uniform(-3, 3)
    return gray(px, 102 if lit else 103)


def solid_lamp_texture(lit):
    """One color on every side, like Project Red lamps."""
    def px(x, y, rng):
        edge = x in (0, SIZE - 1) or y in (0, SIZE - 1)
        v = (232 if edge else 252) if lit else (66 if edge else 78)
        return v + rng.uniform(-2, 2)
    return gray(px, 104)


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


def base_texture(name):
    """A grey texture from tools/base, scaled up to the pack's texture size."""
    img = Image.open(BASE / name).convert("RGBA")
    return img.resize((SIZE, SIZE), Image.NEAREST)


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


def light_color(color):
    """The color a lamp shines: brightened so its strongest channel is full, as #RGB like vanilla lights."""
    rgb = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
    top = max(rgb) or 1
    return "#" + "".join("%x" % round(c * 255 / top / 17) for c in rgb)


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


HALF = ICON / 2 - 2
QUARTER = HALF / 2
HEIGHT = ICON - 4 - 2 * QUARTER


def project(x, y, z):
    """Screen point of a block-space point (x to the front right, z to the front left, y up)."""
    return (ICON / 2 + (x - z) * HALF, 2 + (x + z) * QUARTER + (1 - y) * HEIGHT)


def box_faces(icon, box, top, side):
    """Draw the three visible faces of an axis-aligned box in the vanilla three-quarter view."""
    x0, y0, z0, x1, y1, z1 = box

    def crop(tex, u0, v0, u1, v1):
        part = tex.crop((int(u0 * SIZE), int(v0 * SIZE), max(int(u0 * SIZE) + 1, int(u1 * SIZE)),
                         max(int(v0 * SIZE) + 1, int(v1 * SIZE))))
        return part

    def put(tex, origin, end_u, end_v):
        eu = ((end_u[0] - origin[0]) / tex.width, (end_u[1] - origin[1]) / tex.width)
        ev = ((end_v[0] - origin[0]) / tex.height, (end_v[1] - origin[1]) / tex.height)
        icon.alpha_composite(face(tex, origin, eu, ev))

    t = crop(top, x0, z0, x1, z1)
    put(t, project(x0, y1, z0), project(x1, y1, z0), project(x0, y1, z1))
    left = crop(shade(side, 0.82), x0, 1 - y1, x1, 1 - y0)
    put(left, project(x0, y1, z1), project(x1, y1, z1), project(x0, y0, z1))
    right = crop(shade(side, 0.64), 1 - z1, 1 - y1, 1 - z0, 1 - y0)
    put(right, project(x1, y1, z1), project(x1, y1, z0), project(x1, y0, z1))


SHAPES = {
    "cube": [(0, 0, 0, 1, 1, 1)],
    "half": [(0, 0, 0, 1, 0.5, 1)],
    "stairs": [(0, 0, 0, 1, 0.5, 1), (0, 0.5, 0, 1, 1, 0.5)],
    "wall": [(0.25, 0, 0, 0.75, 0.8, 1)],
}


def shape_icon(shape, top, side):
    icon = Image.new("RGBA", (ICON, ICON))
    for box in SHAPES[shape]:
        box_faces(icon, box, top, side)
    return icon


def dye_icon(color):
    """A small heap of colored powder."""
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    icon = Image.new("RGBA", (ICON, ICON))
    px = icon.load()
    rng = random.Random(color)
    cx, cy = ICON / 2, ICON * 0.62
    for y in range(ICON):
        for x in range(ICON):
            dx, dy = (x - cx) / 26, (y - cy) / 16
            dome = abs(dx) < 1 and dy < 0 and -dy < 1.5 * (1 - dx * dx)
            if dx * dx + dy * dy <= 1 or dome:
                light = 1.15 - 0.35 * (x - cx + (y - cy)) / ICON + rng.uniform(-0.06, 0.06)
                if dx * dx + dy * dy > 0.86 and dy > 0:
                    light *= 0.7
                px[x, y] = (min(255, int(r * light)), min(255, int(g * light)), min(255, int(b * light)), 255)
    return icon


# --- Block definitions ----------------------------------------------------

def name_of(bid):
    return {"Name": "server." + bid + ".name"}


def icon_of(bid):
    return "Icons/ItemsGenerated/" + bid + ".png"


def cube(bid, color, kind, recipe):
    """A full block that takes its color from Tint."""
    block = {
        "Material": "Solid",
        "DrawType": "Cube",
        "Group": kind["group"],
        "Flags": {},
        "Gathering": {"Breaking": {"GatherType": kind["gather"], "ItemId": bid}},
        "BlockParticleSetId": kind["particles"],
        "Textures": [{"All": kind["texture_path"], "Weight": 1}],
        "Tint": ["#" + color],
        "ParticleColor": "#" + color,
        "BlockSoundSetId": kind["sound"],
    }
    block.update(kind.get("block", {}))
    item = {
        "TranslationProperties": name_of(bid),
        "MaxStack": 100,
        "Icon": icon_of(bid),
        "Categories": [kind["category"]],
        "PlayerAnimationsId": "Block",
        "Recipe": recipe,
        "BlockType": block,
        "Tags": {"Type": [kind["tag"]]},
        "ItemSoundSetId": kind["item_sound"],
    }
    if "light" in kind:
        block["Light"] = {"Color": light_color(color)}
        if kind["light"]:
            lamp(block, kind)
    return item


def lamp(block, kind):
    """Lamps turn off and on when used, and show a dark shade of their color when off."""
    block["Interactions"] = {"Use": {"Interactions": [
        {"Type": "ChangeState", "Changes": {"default": "Off", "On": "Off", "Off": "On"}}]}}
    block["InteractionHint"] = "server.interactionHints.turnoff"
    block["State"] = {"Definitions": {
        "On": {},
        "Off": {
            "InteractionHint": "server.interactionHints.turnon",
            "Light": None,
            "Textures": [{"All": kind["light"], "Weight": 1}],
        },
    }}


def log(bid, color, recipe):
    # Inherits rotation, sounds, support and stripping from vanilla oak.
    return {
        "TranslationProperties": name_of(bid),
        "Parent": "Wood_Oak_Trunk",
        "Icon": icon_of(bid),
        "Recipe": recipe,
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


def half(bid, color, kind, texture, recipe):
    """Half slab drawn with Hytale's half block model; two placed together make a full block."""
    return {
        "TranslationProperties": name_of(bid),
        "MaxStack": 100,
        "Icon": icon_of(bid),
        "Categories": [kind["category"]],
        "PlayerAnimationsId": "Block",
        "Interactions": {"Secondary": {
            "Interactions": [{"Parent": "Half_Block", "Matchers": [
                {"Block": {"Id": bid, "State": "default"}, "Face": "Up", "StaticFace": False}]}],
            "Cooldown": {"Id": "BlockInteraction", "Cooldown": 0.3, "ClickBypass": True},
            "Settings": {"Creative": {"AllowSkipChainOnClick": True}},
        }},
        "Recipe": recipe,
        "BlockType": {
            "Material": "Solid",
            "DrawType": "Model",
            "CustomModel": "Blocks/Structures/Base_Shapes/HalfBlock.blockymodel",
            "CustomModelTexture": [{"Texture": texture, "Weight": 1}],
            "Group": kind["group"],
            "HitboxType": "Block_Half",
            "Flags": {},
            "Gathering": {"Breaking": {"GatherType": kind["gather"]}},
            "VariantRotation": "DoublePipe",
            "BlockParticleSetId": kind["particles"],
            "Supporting": {"Down": [{}]},
            "ParticleColor": "#" + color,
            "BlockSoundSetId": kind["sound"],
            "State": {"Definitions": {"Block": {
                "Material": "Solid",
                "DrawType": "Cube",
                "HitboxType": "Full",
                "Textures": [{"All": texture, "Weight": 1}],
                "Supporting": {"BlockSides": [{}]},
            }}},
        },
        "Tags": {"Type": [kind["tag"]]},
        "ItemSoundSetId": kind["item_sound"],
    }


def stairs(bid, color, recipe):
    """Vanilla stone brick stairs with a light texture and Tint (needs an in-game check)."""
    return {
        "TranslationProperties": name_of(bid),
        "Parent": "Rock_Stone_Brick_Stairs",
        "Icon": icon_of(bid),
        "Recipe": recipe,
        "BlockType": {
            "CustomModelTexture": [{"Texture": STAIRS_TEXTURE, "Weight": 1}],
            "Tint": ["#" + color],
            "Gathering": {"Breaking": {"GatherType": "Rocks", "ItemId": bid}},
            "ParticleColor": "#" + color,
        },
    }


def wall(bid, color, recipe):
    """Vanilla brick wall with the marble wall texture and Tint (needs an in-game check)."""
    corner = "*" + bid + "_State_Definitions_Corner"
    return {
        "TranslationProperties": name_of(bid),
        "Parent": "Rock_Stone_Brick_Wall",
        "Icon": icon_of(bid),
        "Recipe": recipe,
        "BlockType": {
            "CustomModelTexture": [{"Texture": WALL_TEXTURE, "Weight": 1}],
            "Tint": ["#" + color],
            "Gathering": {"Breaking": {"GatherType": "Rocks", "ItemId": bid}},
            "ParticleColor": "#" + color,
            "State": {"Definitions": {"Corner": {
                "CustomModelTexture": [{"Texture": WALL_TEXTURE, "Weight": 1}],
                "CustomModel": "Blocks/Structures/Walls/Wall_Rock_Brick_Corner.blockymodel",
                "HitboxType": "Fence_Corner",
                "Gathering": {"Breaking": {"ItemId": bid, "GatherType": "Rocks"}},
            }}},
            "ConnectedBlockRuleSet": {
                "Type": "CustomTemplate",
                "TemplateShapeAssetId": "WallConnectedBlockTemplate",
                "TemplateShapeBlockPatterns": {"Straight": bid, "Corner": corner},
            },
        },
    }


def dye(bid, color, recipe):
    """Dyes are petals in Hytale, so ours are colored petals mixed at the furniture bench."""
    return {
        "TranslationProperties": name_of(bid),
        "Parent": "Plant_Petals_White",
        "Icon": icon_of(bid),
        "Recipe": recipe,
        "BlockType": {
            "CustomModelTexture": [{"Texture": PETAL_TEXTURE, "Weight": 1}],
            "Tint": ["#" + color],
            "ParticleColor": "#" + color,
        },
        "Tags": {"Type": ["Plant"], "Family": ["Petals", "MoreDyes_Dye"]},
    }


def dye_recipe(color):
    """The More Dyes mixing recipe, with each Minecraft dye swapped for Hytale petals."""
    counts = {}
    for mc_dye in DYE_RECIPES[color]:
        for petal in PETALS[mc_dye]:
            counts[petal] = counts.get(petal, 0) + 1
    inputs = [{"ItemId": "Plant_Petals_" + p, "Quantity": n} for p, n in sorted(counts.items())]
    return {"Input": inputs, "OutputQuantity": sum(counts.values()), "BenchRequirement": TEXTILES}


def dyeing(vanilla, dye_id, bench):
    """Eight vanilla blocks and one dye make eight dyed blocks, as in Minecraft."""
    return {
        "Input": [{"ItemId": vanilla, "Quantity": 8}, {"ItemId": dye_id, "Quantity": 1}],
        "OutputQuantity": 8,
        "BenchRequirement": bench,
    }


def from_block(source, category, count=1):
    """A Builder's bench recipe that reshapes one dyed block."""
    return {"Input": [{"ItemId": source, "Quantity": 1}], "OutputQuantity": count,
            "BenchRequirement": builders(category)}


ROCK = {"group": "Stone", "gather": "Rocks", "particles": "Stone", "sound": "Stone",
        "category": "Blocks.Rocks", "tag": "Rock", "item_sound": "ISS_Blocks_Stone",
        "block": {"BlockBreakingDecalId": "Breaking_Decals_Rock"}}
SOIL = {"group": "Sand", "gather": "Soils", "particles": "Sand", "sound": "Sand",
        "category": "Blocks.Soils", "tag": "Soil", "item_sound": "ISS_Blocks_Gravel",
        "block": {"Support": {"Down": [{"FaceType": "Full"}]}}}
WOOD = {"group": "Wood", "gather": "Woods", "particles": "Wood", "sound": "Wood",
        "category": "Blocks.Rocks", "tag": "Wood", "item_sound": "ISS_Blocks_Wood"}
CLOTH = {"group": "Cloth", "gather": "SoftBlocks", "particles": "Dust", "sound": "Cloth",
         "category": "Blocks.Rocks", "tag": "Cloth", "item_sound": "ISS_Items_Cloth"}
GLASSY = {"group": "Stone", "gather": "Rocks", "particles": "Crystal", "sound": "Crystal",
          "category": "Blocks.Rocks", "tag": "Rock", "item_sound": "ISS_Blocks_Stone"}


def kinds():
    """Every tinted block kind: id prefix, display name, texture, vanilla source, recipes."""
    def k(base, **fields):
        out = dict(base)
        out.update(fields)
        return out
    return [
        k(ROCK, prefix="Stone", name="Stone", tex=stone_texture(), vanilla="Rock_Stone", half=True),
        k(ROCK, prefix="Cobble", name="Cobblestone", tex=cobble_texture(), vanilla="Rock_Stone_Cobble", half=True),
        k(ROCK, prefix="Stone_Brick", name="Stone Bricks", tex=brick_texture(), vanilla="Rock_Stone_Brick",
          shaped_from=("Stone", "Bricks"), half=True, stairs=True, wall=True),
        k(ROCK, prefix="Stone_Smooth", name="Smooth Stone", tex=smooth_texture(),
          vanilla="Rock_Stone_Brick_Smooth", shaped_from=("Stone", "Smooth"), half=True),
        k(ROCK, prefix="Marble", name="Marble", tex=marble_texture(), vanilla="Rock_Marble", half=True),
        k(ROCK, prefix="Sandstone", name="Sandstone", tex=sandstone_texture(), vanilla="Rock_Sandstone", half=True),
        k(ROCK, prefix="Granite", name="Speckled Granite", tex=base_texture("speckled_granite.png"),
          shaped_from=("Stone", "Decorative"), half=True),
        k(ROCK, prefix="Granite_Smooth", name="Smooth Speckled Granite",
          tex=base_texture("smooth_speckled_granite.png"), shaped_from=("Granite", "Smooth"), half=True),
        k(SOIL, prefix="Sand", name="Sand", tex=sand_texture(), vanilla="Soil_Sand"),
        k(SOIL, prefix="Gravel", name="Gravel", tex=gravel_texture(), vanilla="Soil_Gravel",
          item_sound="ISS_Blocks_Gravel", sound="Gravel", particles="Gravel", group="Gravel"),
        k(ROCK, prefix="Clay", name="Smooth Clay", tex=clay_texture(), vanilla="Soil_Clay_Smooth_White",
          category="Blocks.Soils", half=True),
        k(GLASSY, prefix="Crystal", name="Glowing Crystal", tex=crystal_texture(),
          vanilla="Rock_Crystal_White_Block", light=None,
          block={"Opacity": "Transparent", "CubeShadingMode": "Reflective"}),
        k(ROCK, prefix="Lamp", name="Lamp", tex=lamp_texture(True), off=lamp_texture(False),
          light="BlockTextures/MoreDyes_Lamp_Off.png", lamp_recipe=True, category="Blocks.Deco"),
        k(ROCK, prefix="Lamp_Solid", name="Solid Lamp", tex=solid_lamp_texture(True),
          off=solid_lamp_texture(False), light="BlockTextures/MoreDyes_Lamp_Solid_Off.png",
          shaped_from=("Lamp", "Furniture_Lighting"), category="Blocks.Deco"),
        k(WOOD, prefix="Planks", name="Planks", tex=planks_texture(), vanilla="Wood_Softwood_Planks",
          shaped_from=("Log", "WoodPlanks"), half=True,
          parent="Wood_Softwood_Planks"),
        k(CLOTH, prefix="Wool", name="Wool", tex=wool_texture(), vanilla="Cloth_Block_Wool_White",
          bench=TEXTILES, half=True),
    ]


def drawer_side(planks):
    """The drawer front for icons: dyed planks with a darker inset panel and a handle."""
    out = planks.copy()
    px = out.load()
    for y in range(4, SIZE - 4):
        for x in range(4, SIZE - 4):
            r, g, b, a = px[x, y]
            f = 0.55 if x in (4, SIZE - 5) or y in (4, SIZE - 5) else 0.8
            if 13 <= x <= 18 and 9 <= y <= 11:
                f = 0.4
            px[x, y] = (int(r * f), int(g * f), int(b * f), a)
    return out


def drawer(bid, color, texture):
    """A dyed drawer for Wan's Storage Drawers: its drawer model and logic, our dyed planks."""
    return {
        "TranslationProperties": name_of(bid),
        "PlayerAnimationsId": "Block",
        "Categories": ["Furniture.Furniture"],
        "Icon": icon_of(bid),
        "Recipe": {
            "Input": [{"ItemId": "Storage_Drawer_Softwood", "Quantity": 8},
                      {"ItemId": "MoreDyes_Dye_" + color.upper(), "Quantity": 1}],
            "OutputQuantity": 8,
            "BenchRequirement": WORKBENCH,
        },
        "BlockType": {
            "BlockEntity": {"Components": {"container": {"Capacity": 1}, "StorageDrawers:DrawerComponent": {}}},
            "Supporting": {side: [{"FaceType": "Full"}] for side in ("Up", "Down", "North", "South", "East", "West")},
            "BlockSoundSetId": "Wood",
            "CustomModel": "Blocks/Drawers/Models/Storage_Drawer.blockymodel",
            "CustomModelTexture": [{"Texture": texture, "Weight": 0}],
            "DrawType": "Model",
            "Interactions": {"Primary": "DrawerInteraction", "Use": "DrawerInteraction"},
            "Material": "Solid",
            "Opacity": "Semitransparent",
            "CustomModelScale": 1.0,
            "VariantRotation": "NESW",
            "ParticleColor": "#" + color,
            "Gathering": {"Soft": {"IsWeaponBreakable": False}, "UseDefaultDropWhenPlaced": False},
        },
    }


def main():
    colors = PROTOTYPE_COLORS if "--prototype" in sys.argv else COLORS
    if "--version" in sys.argv:
        MANIFEST["Version"] = sys.argv[sys.argv.index("--version") + 1]
    if PACK.exists():
        shutil.rmtree(PACK)
    textures = PACK / "Common" / "BlockTextures"
    colored = textures / "MoreDyes"
    icons = PACK / "Common" / "Icons" / "ItemsGenerated"
    items = PACK / "Server" / "Item" / "Items"
    lang = PACK / "Server" / "Languages" / "en-US"
    for d in (textures, colored, icons, items, lang):
        d.mkdir(parents=True)
    (PACK / "manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")

    lines = []

    def write(bid, item, icon, display):
        (items / (bid + ".json")).write_text(json.dumps(item, indent=2) + "\n")
        icon.save(icons / (bid + ".png"))
        lines.append(bid + ".name = " + display)

    for color in colors:
        bid = "MoreDyes_Dye_" + color.upper()
        write(bid, dye(bid, color, dye_recipe(color)), dye_icon(color), color.upper() + " Dye")

    for kind in kinds():
        prefix = kind["prefix"]
        kind["texture_path"] = "BlockTextures/MoreDyes_" + prefix + ".png"
        kind["tex"].save(PACK / "Common" / kind["texture_path"])
        if "off" in kind:
            kind["off"].save(PACK / "Common" / kind["light"])
        for color in colors:
            hexid = color.upper()
            bid = "MoreDyes_" + prefix + "_" + hexid
            dye_id = "MoreDyes_Dye_" + hexid
            if "shaped_from" in kind:
                source, category = kind["shaped_from"]
                source_id = "MoreDyes_" + source + "_" + hexid
                if category.startswith("Furniture_"):
                    recipe = {"Input": [{"ItemId": source_id, "Quantity": 1}], "OutputQuantity": 1,
                              "BenchRequirement": LIGHTING}
                else:
                    recipe = from_block(source_id, category)
            elif kind.get("lamp_recipe"):
                recipe = {"Input": [{"ItemId": dye_id, "Quantity": 1},
                                    {"ItemId": "Furniture_Crude_Candle", "Quantity": 1},
                                    {"ItemId": "Ingredient_Bar_Iron", "Quantity": 1}],
                          "OutputQuantity": 1, "BenchRequirement": LIGHTING}
            else:
                recipe = dyeing(kind["vanilla"], dye_id, kind.get("bench", WORKBENCH))
            item = cube(bid, color, kind, recipe)
            if prefix == "Planks":
                # Keep the vanilla planks' behaviour, and also allow dyeing vanilla planks.
                item = {"TranslationProperties": name_of(bid), "Parent": kind["parent"], "Icon": icon_of(bid),
                        "Recipe": recipe, "BlockType": {
                            "Textures": [{"All": kind["texture_path"], "Weight": 1}],
                            "Tint": ["#" + color],
                            "Gathering": {"Breaking": {"GatherType": "Woods", "ItemId": bid}},
                            "ParticleColor": "#" + color}}
            write(bid, item, shape_icon("cube", tinted(kind["tex"], color), tinted(kind["tex"], color)),
                  hexid + " " + kind["name"])
            if kind.get("half"):
                tex_path = "BlockTextures/MoreDyes/" + prefix + "_" + hexid + ".png"
                colored_tex = tinted(kind["tex"], color)
                colored_tex.save(PACK / "Common" / tex_path)
                hid = "MoreDyes_" + prefix + "_Half_" + hexid
                write(hid, half(hid, color, kind, tex_path, from_block(bid, "HalfSlab", 2)),
                      shape_icon("half", colored_tex, colored_tex), hexid + " " + kind["name"] + " Slab")
            if kind.get("stairs"):
                sid = "MoreDyes_" + prefix + "_Stairs_" + hexid
                colored_tex = tinted(kind["tex"], color)
                write(sid, stairs(sid, color, from_block(bid, "Stairs")),
                      shape_icon("stairs", colored_tex, colored_tex), hexid + " " + kind["name"] + " Stairs")
            if kind.get("wall"):
                wid = "MoreDyes_" + prefix + "_Wall_" + hexid
                colored_tex = tinted(kind["tex"], color)
                write(wid, wall(wid, color, from_block(bid, "Wall", 2)),
                      shape_icon("wall", colored_tex, colored_tex), hexid + " " + kind["name"] + " Wall")

    # Logs keep vanilla bark on the sides, so they are not in kinds().
    log_tex, bark = log_top_texture(), bark_preview_texture()
    log_tex.save(textures / "MoreDyes_Log_Top.png")
    for color in colors:
        bid = "MoreDyes_Log_" + color.upper()
        recipe = dyeing("Wood_Oak_Trunk", "MoreDyes_Dye_" + color.upper(), WORKBENCH)
        write(bid, log(bid, color, recipe), shape_icon("cube", tinted(log_tex, color), bark),
              color.upper() + " Log")

    if "--drawers" in sys.argv:
        # Needs Wan's Storage Drawers; this build checks whether Hytale loads them without it.
        MANIFEST["OptionalDependencies"] = {"WanMine:StorageDrawers": "*"}
        (PACK / "manifest.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")
        planks_tex = planks_texture()
        for color in colors:
            hexid = color.upper()
            bid = "MoreDyes_Drawer_" + hexid
            colored_tex = tinted(planks_tex, color)
            write(bid, drawer(bid, color, "BlockTextures/MoreDyes/Planks_" + hexid + ".png"),
                  shape_icon("cube", colored_tex, drawer_side(colored_tex)), hexid + " Storage Drawer")

    (lang / "server.lang").write_text("\n".join(lines) + "\n")
    print("Wrote %d items to %s" % (len(lines), PACK.relative_to(ROOT)))


if __name__ == "__main__":
    main()
