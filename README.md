# More Dyes for Hytale

A Hytale port of More Dyes, starting as an asset pack (no Java plugin yet).

Status: **118 dyed stone blocks.** Each one shares a single grey texture and gets its color from the BlockType `Tint` field. Tested in game on 2026-10-03: placed blocks show the right colors.

## Trying it

1. Copy the `pack/MoreDyes` folder into Hytale's `UserData/Mods` folder.
   - Windows: `%APPDATA%\Hytale\UserData\Mods\MoreDyes`
   - Linux (Flatpak): `~/.var/app/com.hypixel.HytaleLauncher/data/Hytale/UserData/Mods/MoreDyes`
2. Start Hytale, open **Worlds**, right-click a creative world and turn on **MoreDyes**.
3. Join the world and search the creative inventory for a color's hex (e.g. `E57F6C`), or look in the Rocks category. Block IDs are `MoreDyes_Stone_<HEX>`.

There are no crafting recipes yet, so the blocks are creative-only.

## Regenerating

```
pip install pillow
python3 tools/generate.py               # all 118 colors
python3 tools/generate.py --prototype   # just three, for quick tests
```

`tools/colors.json` holds the 118 colors, taken from `ColorStrings.ALL` in [moredyes_1165](https://github.com/Naverene/moredyes_1165).
