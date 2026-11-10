# More Dyes for Hytale

A Hytale port of More Dyes, starting as an asset pack (no Java plugin yet).

Status: **118 dyes and 30 dyed block types in every color** (about 3,650 items). Each full block shares one grey texture per type and gets its color from the BlockType `Tint` fields. Logs only tint their end rings and keep vanilla oak bark on the sides, like the Minecraft versions. Icons are 3D shapes rendered by the generator.

| Kind | Blocks |
| --- | --- |
| Dyes | `MoreDyes_Dye_<HEX>`, mixed from Hytale petals at the Furniture bench (Textiles), using the same mixes as the Minecraft dyes |
| Stone | stone, cobblestone, stone bricks, smooth stone, marble, sandstone, speckled granite, smooth speckled granite |
| Soil | sand, gravel, smooth clay (the Hytale stand-in for terracotta) |
| Wood and cloth | logs, planks, wool |
| Light | glowing crystal, lamp, solid lamp, all shining light in their own color |
| Shapes | slabs of stone, cobblestone, bricks, smooth stone, marble, sandstone, both granites, smooth clay, planks and wool; stone brick stairs and walls |

Slabs draw Hytale's half block model, which doesn't take a tint for certain, so each color has its own pre-colored slab texture. Stairs and walls use Hytale's own models and light vanilla textures with `Tint`; whether models take a tint still needs checking in game.

### Crafting

- **Dyes:** petals at the Furniture bench, Textiles tab, one dye per petal. For example an azure and a blue petal give two `4D73C5` dyes, and an orange and a pink petal give two `E57F6C`. Minecraft dyes that Hytale has no petal for are made of two or three petals (magenta is pink and purple, lime is green and yellow, brown is orange and black, gray is black and white, light gray is black and two whites).
- **Dyed blocks:** 8 vanilla blocks and 1 dye at the Workbench, Crafting tab, give 8 dyed blocks (wool is at the Furniture bench, Textiles tab). The vanilla blocks are Rock_Stone, Rock_Stone_Cobble, Rock_Stone_Brick, Rock_Stone_Brick_Smooth, Rock_Marble, Rock_Sandstone, Soil_Sand, Soil_Gravel, Soil_Clay_Smooth_White, Rock_Crystal_White_Block, Wood_Oak_Trunk, Wood_Softwood_Planks and Cloth_Block_Wool_White.
- **Builder's bench:** dyed stone becomes dyed bricks, smooth stone or speckled granite; speckled granite becomes smooth speckled granite; dyed logs become dyed planks; any dyed block with a slab becomes 2 slabs; dyed stone bricks become stairs or 2 walls.
- **Lamps:** a dye, a crude candle and an iron bar at the Furniture bench, Lighting tab. A lamp crafts into the solid lamp there. Use a lamp to turn it off and on (Hytale has no redstone).

## Trying it

1. Download `MoreDyes-<version>.zip` from [Releases](https://github.com/Naverene/moredyes_hytale/releases) ("Development build" is the latest `main`), and unzip it into a new `MoreDyes` folder inside Hytale's `UserData/Mods` folder, so you get `Mods/MoreDyes/manifest.json`.
   - Windows: `%APPDATA%\Hytale\UserData\Mods\MoreDyes`
   - Linux (Flatpak): `~/.var/app/com.hypixel.HytaleLauncher/data/Hytale/UserData/Mods/MoreDyes`
2. Start Hytale, open **Worlds**, right-click a creative world and turn on **MoreDyes**.
3. Join the world and search the creative inventory for a color's hex (e.g. `E57F6C`). Item IDs are `MoreDyes_<Kind>_<HEX>`, such as `MoreDyes_Stone_Brick_Half_E57F6C`.

## Building

CI builds the pack on every push and pull request, checks it with `tools/check_pack.py`, and attaches the zip to the run. Pushes to `main` update the Development build release, and pushing a tag like `v0.3.0` publishes a release and uploads it to [CurseForge](https://www.curseforge.com/hytale) project 1725010 (the tag sets the pack version, and the repo needs the `CURSEFORGE_TOKEN` secret). A release drafted on GitHub for the tag works too; CI attaches the zip to it.

The pack isn't committed; build it locally with:

```
pip install pillow
python3 tools/generate.py               # all 118 colors
python3 tools/generate.py --prototype   # just three, for quick tests
python3 tools/check_pack.py             # check references
```

That writes `pack/MoreDyes`, which you can copy straight into `UserData/Mods`.

`tools/colors.json` holds the 118 colors, taken from `ColorStrings.ALL` in [moredyes_1165](https://github.com/Naverene/moredyes_1165). `tools/dye_recipes.json` holds each color's Minecraft dye mix from the 26.3 version in [Naverene/moredyes](https://github.com/Naverene/moredyes); the generator swaps each Minecraft dye for Hytale petals.

## License

MIT, see [LICENSE](LICENSE), except the speckled granite textures, which come from GregTech 5 Unofficial and stay under the LGPL-3.0; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Hytale's own assets that the pack refers to, such as the oak bark texture, belong to Hypixel Studios and aren't included.
