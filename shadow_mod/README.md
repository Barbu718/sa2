# Sonic Advance 2 + Shadow — native GBA build

This branch builds a real `sa2.gba` ROM for GBA hardware/emulators.

## Design

For this first native ROM implementation, the stock **Amy** character slot is repurposed as **Shadow**. This keeps the original GBA character-selector/save structures at their native five-character size while preserving Sonic, Cream, Tails, and Knuckles.

Shadow's gameplay art is generated from the user-supplied **Ultimate Shadow** sprite sheet and mapped to SA2's native shared character animation IDs. This means jump graphics are taken from true curled Shadow jump/spin frames, while the dark charge-ball sequence is reserved for Spin Dash. Crouch, brake, grind, aerial, hurt/death, handle/hanging, and turnaround-bar states are mapped separately.

The browser/WASM patch is not used here. The workflow modifies the decompilation assets before compiling the real GBA ROM.

## Build

The GitHub Actions workflow `.github/workflows/build-shadow-gba.yml` installs SAT-R/agbcc and the ARM toolchain, applies `shadow_mod/apply_shadow_mod.py`, runs `make COMPARE=0`, and uploads `sa2.gba` as the `Sonic-Advance-2-Shadow-GBA` artifact.

## Sprite credit

Ultimate Shadow sprite sheet supplied by the user; keep the original sprite-sheet creator credits with redistributed patches/mod source.
