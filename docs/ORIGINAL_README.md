# RE:TRACE

A six-floor recording puzzle game (B6 → B1 → surface), written in Python with
pygame-ce. This final release is based on the user-approved Prototype 13. The
story and manual are in Korean.

## Play

1. Extract the complete `RETRACE_Final_Game.zip` file. Do not run the Python
   file from inside the ZIP.
2. Keep `RETRACE.py` beside its included `assets` folder.
3. With Python and pygame-ce 2.5.8 installed, open `RETRACE.py` in IDLE and
   choose **Run → Run Module**. This works the same way on a Mac or a Windows
   computer that has those prerequisites installed.
4. Press **Space** on the title screen. The animated 사용 안내 opens first; press
   **Space** again when ready to continue.

`requirements.txt` names the exact pygame-ce version. If you need to install
it from this folder, `python -m pip install -r requirements.txt` asks Python's
package installer to install the listed dependency. The game is a Python
project, not a standalone `.app` or `.exe`. To share it, send the entire ZIP.

## Controls

| Key | Action |
| --- | --- |
| W A S D | Move |
| R | Start a recording; press again to save it and return to the floor start |
| E | Use a nearby device |
| Q | Reset the current floor and erase its recordings |
| Esc | Open or close the manual; the game pauses while it is open |
| H | Show the next available hint |
| Space | Start, continue, or retry when the screen prompts you |

The manual has three tabs. The opening example shows recording, saving and
replay with B6 game art; longer rules and floor hints are available from its
other tabs. Hints unlock one minute at a time during active play, and previously
revealed hints remain available after a floor reset. A failure restart erases
all recordings on that floor. Enter and F1–F6 are not game controls. Close the
window to quit.

## Files and credits

`RETRACE.py` is the game. `assets/` contains every runtime image, font and sound.
`audio_source/` and `ART_EDIT_PROMPTS.md` document how the audio and artwork
were prepared; they are not needed to launch the game. Font and soundfont
licence notices and further authorship details are included in those folders
and `assets/ART_AND_SOUND_NOTES.txt`.

The user created and directed the project concept, puzzle and interface design,
playtests, and revisions. The code, generated artwork edits and prepared audio
were made with AI assistance under that direction. No online AI service is
needed while playing.
