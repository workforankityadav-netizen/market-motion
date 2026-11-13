# video.py: everything specific to one video. `mm.py new` writes this file; Claude fills it in.
# Times are OUTPUT seconds (the cut voice, see work/words.txt) except DROPS, which are RAW seconds (work/raw_words.txt).
# Coordinates are pixels on a 1920x1080 frame. See examples/example_video.py for a full worked video.
from lib import *  # noqa: F401,F403  helpers: cap pill glass chart_card counter bignum stat line bar hbar threshold lanes
#                   cal timeline doc blob crowd cursor button tile progress orbit warn globe badge floor beam ico

TITLE = "My video"           # export file name
INPUT = ""                   # set by `mm.py new`
HAS_VIDEO = True             # False for an mp3/wav voiceover: no face shots
SCRIPT = None                # "script.txt" if a script was given; used to check the cut word by word
LANG = "auto"                # whisper language: en, hi, auto ...

# ---- step 1: cut (mm.py cut)
DROPS = []                   # RAW-time ranges to remove: retakes (keep the last good take), fluffs, off-script asides
PAD = 0.10                   # air kept each side of speech, so pauses shrink to about 0.2 s
MIN_PAUSE = 0.3

# ---- step 2: face shots (footage only, mm.py faces)
FACE_X, FACE_Y = 0.5, 0.3    # where the face is in the raw frame (0-1); used to frame the crops
FACES = []                   # exactly one 3-4 s shot starting in each window 5-15, 15-30, 30-45, 45-60 s; none after 1:00

# ---- step 3: picture
TOTAL = None                 # None = voice length + END_CARD
END_CARD = 2.5
SCENES = []                  # (start, end) of each motion-graphic scene; scenes + faces must cover the whole timeline
WORLDS = [(0, "g")]          # background mood changes: (time, "g" green | "r" red | "n" neutral navy)
CAPS = []                    # (caption id, start, end); total <= 10% of TOTAL and <= 10 s in the first minute


def scenes():
    """Return {scene index: html}. Every element appears on its spoken word (times from work/words.txt)."""
    S = {}
    return S


CUSTOM_JS = """"""           # optional extra GSAP moves: tl.to("#id", {...}, time);

# ---- step 4: sound (mm.py mix). Calm and sparse: the mixer enforces 1.5 s gaps, <= 8 cues a minute, <= 3 impacts.
CUES = []                    # (time, kind): swish | swish2 (section change), click (on-screen cursor click),
#                              bell | bell2 (one key number lands), down (story turns red), rise | swell | impact (open + finale)
MUSIC = None                 # path to your own licensed track, or None for the built-in original calm bed
MUSIC_VARIANT = 1            # 1-6, changes key, tempo and pattern of the built-in bed
