---
name: market-motion
description: Edit a long 16:9 YouTube video (finance, stock market, business, economy, crypto, money explainers) in the "market motion" style - dark glass-and-glow motion graphics in market green and red, Helvetica-style two-line kinetic text, calm professional sound. Use when someone shares a raw talking-head video (.mp4/.mov) or a voiceover (.mp3/.wav) and asks for this format, says "market motion", "market style", "green and red style", "stock market style video" or "long motion graphics video". Rules - 5 s motion-graphic open, pauses and retakes cut, the face once per 15 s in the first minute only, then voice plus nonstop motion graphics, captions in at most 10% of the video, sparse calm SFX.
---

# Market Motion (16:9 long-form)

A horizontal video where the picture never stops moving and every scene shows what is being said. Dark navy-to-black backgrounds, frosted glass cards, glowing lines, soft 3D "blob" people, lit in **market green** (up, growth, good) and **market red** (down, risk, loss). Text is rare; when it appears it is a two-line headline that builds word by word.

The engine lives next to this file in `engine/`. Every step is one command. `$MM` below stands for `~/.claude/skills/market-motion/engine/mm.py`; write the full path in each command, since shell variables do not carry between calls.

```bash
python3 $MM new    <project> <input> [--script script.txt] [--lang en]
python3 $MM cut    <project>
python3 $MM faces  <project>
python3 $MM build  <project>
python3 $MM snap   <project>
python3 $MM render <project>
python3 $MM mix    <project>
python3 $MM check  <project>
```

If a command says a tool is missing, run `python3 ~/.claude/skills/market-motion/engine/check_setup.py --install` (ask the user first).

---

## 1. Hard rules

| # | Rule | Checked by |
|---|---|---|
| R1 | **0:00-0:05 is pure motion graphics.** No face. It hooks with a moving chart, number or green/red event tied to the first line. | `build`, `check` |
| R2 | **Raw video: remove every pause, retake, fluff and false start**, so the audio follows the script line by line. Keep the **last** complete take of a repeated line. | `new` report, `check` word match |
| R3 | **First minute: the face once every 15 s.** One 3-4 s shot starting inside each window 5-15, 15-30, 30-45, 45-60 s. | `build`, `check` |
| R4 | **After 1:00: no face.** Voice plus motion graphics to the end. | `build`, `check` |
| R5 | **No still frame, ever.** Something visibly moves in every frame. | `check` (freezedetect) |
| R6 | **Every scene illustrates the spoken words** and lands on its word, never before it. | shot list review, `snap` |
| R7 | **Captions at most 10% of the runtime, and at most 10 s in the first minute.** | `build`, `check` |
| R8 | **Calm, sparse, professional sound.** Most visuals are silent. Max 8 cues a minute, 1.5 s apart, SFX 18-20 dB under the voice. | `mix` enforces, `check` reports |
| R9 | **Colours: market green and red** on a dark base. | template |

**Voiceover input (.mp3/.wav):** no face shots; the whole video is motion graphics. Pauses are still tightened.

**Inputs are always a recording:** a full video (.mp4/.mov) or a voiceover (.mp3/.wav). Never generate a voiceover with text-to-speech. If the user gives only a script, ask for the recording. A script alongside the recording is welcome (`--script`); it is used to check the cut word by word. Whisper in this pipeline is speech-to-text only.

**Ground rules:** finish the job and deliver a file; check with evidence and report numbers; you cannot hear, so never say how audio sounds; never invent numbers (on-screen numbers must match the voice, rounded the way they are spoken); flag script claims you cannot verify instead of changing them; use only assets the user owns or that are licensed, and never put a real company's logo or a real person's photo on screen unless the user provides it.

---

## 2. Workflow

1. **New project.** `python3 $MM new ~/Videos/<slug> <input> [--script script.txt] [--lang en]`. It links the input into `raw/`, extracts the audio, transcribes it with word timings (pause-started windows, so retakes are not smeared), and writes:
   - `work/prep_report.txt`: long pauses with the words around them, repeated phrases (retake suspects) and filler words;
   - `work/raw_words.txt`: every word with its raw time;
   - `video.py`: the file you fill in for this video.
2. **Decide the cuts.** Read the report and raw words. For each retake keep the last good take: add the raw range of the bad take to `DROPS` (start and end inside silences). Also drop fluffs and off-script asides. Then `python3 $MM cut <project>`. It removes every pause over 0.3 s (keeping 0.1 s of air), applies `DROPS`, adds click-free fades and re-transcribes the cut into `work/words.txt` (output times). Read it: no swallowed words, no repeated phrases, numbers intact.
3. **Face shots (video only).** Pick four sentence starts, one in each first-minute window, 3-4 s each, where the speaker makes a point. Set `FACES`, plus `FACE_X`/`FACE_Y` (face position in the raw frame, 0-1). `python3 $MM faces <project>` cuts them along the edit list, alternating medium and close framing.
4. **Shot list.** Fill `SCENES`, `WORLDS`, `CAPS` and `scenes()` in `video.py` with the helpers from `engine/lib.py` (section 4). Scenes plus faces must cover the whole timeline. Copy patterns from `engine/examples/example_video.py`.
5. **Build and look.** `python3 $MM build <project>` writes `index.html`, checks R1, R3, R4, R7 and coverage, and lints (0 errors required). `python3 $MM snap <project>` writes `snap/contact-sheet*.jpg`: look for overlaps, text off cards, empty frames, numbers shown before they are said. Fix and rebuild.
6. **Render.** `python3 $MM render <project>` (about 2-3 s of render per second of video; run it in the background on long videos and tell the user).
7. **Sound.** Fill `CUES` (section 6), then `python3 $MM mix <project>`. It drops any cue that breaks the calm budget, sets SFX 19 dB and music about 20 dB under the voice, ducks the music under speech, masters to -14 LUFS / -1 dBTP and exports `export/<TITLE>.mp4`.
8. **Check.** `python3 $MM check <project>` writes `export/report.txt`: rules, freeze check, loudness, calm-sound numbers and the word match. Fix every FAIL (a freeze means more idle motion or a secondary move in that scene), then re-render and re-mix.
9. **Report** the export path, length, loudness, caption %, face times, cues per minute, and what you could not check (listening, facts).

---

## 3. Timeline

| Time | Picture | Pace |
|---|---|---|
| 0:00-0:05 | Cold open graphic from the first line | new beat every 1-1.5 s |
| 0:05-1:00 | Graphics + 4 face shots | new beat every 2-3 s |
| 1:00-end | Graphics only | new beat every 3-5 s; bigger scene change every 15-25 s |
| last 2-3 s | End card (`END_CARD`): a rising green line, a CTA button if the speaker says one | |

Face shots enter and leave with a short zoom-blur; the engine adds a slow push-in and a thin green rim.

---

## 4. Words to visuals

| Spoken idea | Helper(s) in `lib.py` |
|---|---|
| Price, index or asset rising | `chart_card(...)` green line with riding dot, `bars=` for a rising wave |
| Falling, crash, sell-off | `chart_card(..., red=True)`, `WORLDS` red, `line(..., "red")` |
| A specific number or % | `bignum(x, y, at, counter(to, at, ...))`, `stat(...)` card |
| A record, a threshold being passed | `hbar(...)` growing past `threshold(..., break_at=)` |
| Competition, race, rivals | `lanes(...)` with `go_at` |
| Dates, schedule, "by June" | `timeline(...)` + `cal(...)` |
| Filing, paperwork, approval | `doc(..., stamp_word=...)` + `cursor(...)` click |
| Buying, a decision, subscribe | `button(...)` + `cursor(...)` |
| People, investors, demand | `blob(...)`, `crowd(...)` (`gr` happy, `rd` worried) |
| A named company or person | `pill(name, ..., icon)` (no logos or photos unless the user provides them) |
| Several players in one trend | `orbit(...)` |
| Risk, warning | `warn(...)`, `globe(...)`, shake a wrapper with `shake(...)` |
| Progress, preparing, building up | `progress(...)` |
| Best ever, number one | `floor()` + `line(...)` + `beam()` + `badge("#1")` |
| Short labels | `pill(text, x, y, at, kind, icon)`, `tile(...)` |

Icons: rocket hex chip cloud bank bell person up down drop mic chat search warn globe coin doc cal lock shield cart wallet.

**Motion rules (R5):** every element that lands floats 10-14 px and tilts slightly (the template does this); the camera pushes 8% per scene; light blobs and dust always drift. If a beat lasts over 4 s, add a second move on a word inside it (a pill, a counter, a line). Transitions are blur-pushes, not cuts to black; never crossfade.

---

## 5. Look

- **Palette:** green `#22e55c` (up), red `#ff2d3a` (down), ink `#f4f6fa`, dim `#9aa3b2`, backgrounds near-black to deep navy. Blue only as a faint cool accent.
- **Font:** Inter Tight. Captions: line 1 Regular 64 px, line 2 Bold 74 px, tracking -0.035em, centred near the top; a key word may be green (`*word`). Words build one by one from blur on their spoken time.
- **Cards:** frosted glass, 28 px radius, thin light border, soft shadow. **Lines:** white with a glow, area fill in green or red.
- **Layout:** 96 px side margins. Use the width: comparisons side by side, timelines left to right.

## 6. Captions (R7)

Captions are text that repeats the spoken words (`cap(...)`). Short graphic labels of three words or fewer (pills, axis labels, badges) do not count. Spend the budget on the hook line, the biggest number or claim, and the closing line. Register every caption in `CAPS` as (id, start, end).

## 7. Sound (R8): calm, sparse, professional

Sound effects are seasoning, not a beat. A sound on every pop or line pulls attention from the voice and becomes tiring. **Most visual events stay silent**: labels, word-by-word text, idle motion, line draws, counters while counting, background changes and face cuts.

Cue kinds in `CUES = [(time, kind), ...]`:

| Kind | Use for | Level |
|---|---|---|
| `swish`, `swish2` | a real section or big scene change (every 15-30 s, not every scene) | -28 dB |
| `click` | an on-screen cursor click | -22 dB |
| `bell`, `bell2` | one key number landing (max one per scene, no tick runs) | -26 dB |
| `down` | the story turns red | -26 dB |
| `rise`, `swell`, `impact` | the cold open landing and the finale only (max 3 impacts) | -22 to -28 dB |

The mixer enforces: at least 1.5 s between cues; 3 in the first 5 s, 8 in the rest of minute one, 8 per later minute; at most 3 impacts. It then sets the whole SFX bus 19 dB under the voice. **Music:** the built-in original calm bed (`MUSIC = None`, `MUSIC_VARIANT` 1-6) or the user's licensed track (`MUSIC = "path"`), about 20 dB under the voice with ducking under speech, lifting slightly on the end card.

## 8. Traps

- Whisper on a whole file can smear a retake across a pause; `new` transcribes in pause-started windows for this reason. Still read every long pause in the report.
- Floats set as a percentage barely move small pills; the template uses pixel floats. A freeze in `check` means a scene needs a second move.
- Scene and caption ids must be unique. A number must never appear before it is spoken.
- Hyperframes needs internet at render time (fonts and GSAP from CDNs). First render downloads the renderer and its browser.
- Never use another creator's watermarked image or footage.
