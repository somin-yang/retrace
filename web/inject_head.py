"""Add phone-related tags to a pygbag-built index.html.

usage: python web/inject_head.py <index.html> [--homescreen]

Always added:
  iPhone plays Web Audio (which pygame uses in the browser) on the "ringer"
  channel by default, so the silent switch mutes the game. Setting the
  audio session type to "playback" (iOS 17+) makes it behave like a music or
  video app. Browsers without this API simply skip it.

--homescreen (mobile build):
  Phones cannot hide the address bar from a web page (iPhone has no Fullscreen
  API except for video). A page added to the home screen with these tags opens
  as an app, without the address bar.
"""
import sys
from pathlib import Path

AUDIO = """
<script>
try { if (navigator.audioSession) { navigator.audioSession.type = "playback"; } } catch (e) {}
</script>
"""

HOMESCREEN = """
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="RE:TRACE">
<meta name="theme-color" content="#080b0f">
"""

page = Path(sys.argv[1])
html = page.read_text(encoding="utf-8")
tags = ""
if "audioSession" not in html:
    tags += AUDIO
if "--homescreen" in sys.argv and 'rel="manifest"' not in html:
    tags += HOMESCREEN
if tags:
    # Put the tags at the very start of <head> so they run before the game's audio starts.
    if "<head>" in html:
        html = html.replace("<head>", "<head>" + tags, 1)
    elif "</head>" in html:
        html = html.replace("</head>", tags + "</head>", 1)
    else:
        html = tags + html
    page.write_text(html, encoding="utf-8")
print("tags added to", page)
