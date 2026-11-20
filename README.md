# RE:TRACE

A six-floor recording puzzle game (B6 → B1 → surface) by **Somin Yang**, written in
Python with pygame-ce. The story and manual are in Korean.

▶ **Play on a PC browser (keyboard):** https://somin-yang.github.io/retrace/
▶ **Play on a phone (touch, hold it sideways):** https://somin-yang.github.io/retrace/mobile/

Tap or click the screen once to start; sound begins after the first tap.

## Controls

| Key | Action |
| --- | --- |
| W A S D | Move |
| R | Start a recording; press again to save it and return to the floor start |
| E | Use a nearby device |
| Q | Reset the current floor and erase its recordings |
| Esc | Open or close the manual (pauses the game) |
| H | Show the next available hint |
| Space | Start, continue, or retry when the screen prompts you |

## Run on a computer (Mac / Windows)

```bash
cd game
python -m pip install -r requirements.txt   # installs pygame-ce 2.5.8
python main.py
```

Or open `game/RETRACE.py` (or `game/main.py`) in IDLE and choose **Run → Run Module**.

## Repository layout

```
game/                 everything the game needs at runtime (also the web build input)
  main.py             the game (pygbag requires this file name)
  RETRACE.py          desktop launcher that starts main.py
  assets/             images, fonts, OGG sounds
  favicon.png         browser tab icon
docs/                 not needed to play
  audio_source/       music scores, soundfont and the offline audio renderer
  ART_EDIT_PROMPTS.md artwork edit notes
  ORIGINAL_README.md  README of the original desktop release
.github/workflows/    builds the web version with pygbag and publishes to GitHub Pages
```

## Versions

| Version | Where | Screen | Controls |
| --- | --- | --- | --- |
| Desktop | `python main.py` on Mac/Windows | 960×720 window | keyboard |
| PC web | `/retrace/` | 960×720 | keyboard |
| Mobile web | `/retrace/mobile/` | 1440×720 (game + side panels) | on-screen pad and buttons |

All three run the same `game/main.py`. The mobile web build is the same folder with an
extra `mobile.flag` file, added automatically by the workflow — do not commit that file.

## How the web version works

`git push` to `main` → GitHub Actions runs `pygbag`, which packages `game/` with a
WebAssembly build of CPython + pygame-ce → the result is published to GitHub Pages.
Nothing runs on a server; the game runs entirely inside the player's browser.

Web-related changes from the desktop release:
- the game loop is `async` and yields to the browser every frame;
- all sounds are OGG (browsers do not play WAV reliably);
- background images are stored at the game's 960×720 render size to cut download size.

## Credits

Concept, puzzle and interface design, playtests and revisions by Somin Yang.
Code, artwork edits and audio were made with AI assistance under her direction.
Font and soundfont licences: see `game/assets/*-OFL.txt`, `game/assets/ART_AND_SOUND_NOTES.txt`
and `docs/audio_source/`.
