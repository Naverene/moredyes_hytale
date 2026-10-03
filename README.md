# More Dyes for Hytale

A Hytale port of More Dyes, starting as an asset pack (no Java plugin yet).

Status: **118 colors each of dyed stone, logs, planks and wool** (472 blocks). Each block type shares one grey texture and gets its color from the BlockType `Tint` fields. Logs only tint their end rings and keep vanilla oak bark on the sides, like the Minecraft versions. Icons are 3D cubes rendered by the generator.

Tinted stone was tested in game on 2026-10-03. Logs, planks and wool inherit from Hytale's own oak log, softwood planks and white cloth definitions.

## Trying it

1. Copy the `pack/MoreDyes` folder into Hytale's `UserData/Mods` folder.
   - Windows: `%APPDATA%\Hytale\UserData\Mods\MoreDyes`
   - Linux (Flatpak): `~/.var/app/com.hypixel.HytaleLauncher/data/Hytale/UserData/Mods/MoreDyes`
2. Start Hytale, open **Worlds**, right-click a creative world and turn on **MoreDyes**.
3. Join the world and search the creative inventory for a color's hex (e.g. `E57F6C`), or look in the Rocks and Plants categories. Block IDs are `MoreDyes_<Stone|Log|Planks|Wool>_<HEX>`.

Dyed planks are crafted from their dyed log at the Builder's bench. Everything else is creative-only until dye items exist.

## Regenerating

```
pip install pillow
python3 tools/generate.py               # all 118 colors
python3 tools/generate.py --prototype   # just three, for quick tests
```

`tools/colors.json` holds the 118 colors, taken from `ColorStrings.ALL` in [moredyes_1165](https://github.com/Naverene/moredyes_1165).
