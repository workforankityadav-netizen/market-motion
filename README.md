# market-motion

A [Claude Code](https://claude.com/claude-code) skill that turns a raw talking-head video or a voiceover into a finished 16:9 YouTube video in a **market motion** style: dark glass-and-glow motion graphics in market green and red, word-by-word kinetic headlines, and a calm, professional sound mix.

You share the file, Claude does the edit. **Input is either a full video (.mp4/.mov) or a recorded voiceover (.mp3/.wav).** Nothing generates a voice: you bring the recording.

The edit:
- removes every pause, retake and verbal stumble;
- opens with 5 seconds of motion graphics;
- shows the speaker's face once every 15 seconds in the first minute only, then switches to voice plus motion graphics;
- animates every sentence with charts, counters, races, timelines, documents, people and labels, timed to the spoken word, with nothing ever standing still;
- uses captions in no more than 10% of the video;
- adds sparse, quiet sound effects and an original music bed, mastered to -14 LUFS for YouTube;
- checks its own work (rules, frozen frames, loudness, words against the script) and writes a report.

## Install

macOS or Linux (on Windows, use WSL):

```bash
git clone https://github.com/<your-account>/market-motion.git
cd market-motion
./install.sh
```

The installer:
1. copies the skill to `~/.claude/skills/market-motion/`;
2. installs anything missing:
   - ffmpeg, Node.js 18+ and whisper.cpp: Homebrew on macOS, apt or dnf on Linux;
   - the Whisper speech-to-text model (~550 MB): it only listens to your recording to time every graphic to the spoken word, find retakes and cut pauses; it does not make voices;
   - the Hyperframes renderer, which downloads itself.

Options:
- `./install.sh --allow` also lets Claude Code run the pipeline's commands without asking each time.
- `./install.sh --no-deps` copies the skill only.

**Before you start:**
- **macOS:** [Homebrew](https://brew.sh) must be installed.
- **Linux:** the installer uses `sudo` for packages.

Expect about 3 GB of disk space, and an internet connection when rendering.

## Use

Open Claude Code in any folder and say, for example:

> Edit `~/Downloads/raw.mp4` in market motion style.

> Make a market motion video from `voiceover.mp3`. The script is in `script.txt`.

Claude creates a project folder, shows you snapshots of the frames before rendering, and delivers `export/<title>.mp4` with a `report.txt`.

To change anything afterwards, say what and when:

> At 1:12, make the chart red and slow the line down.

> Fewer sound effects in the second half.

> Use my track `music/calm.mp3` instead of the built-in music.

## What's inside

```
install.sh                         one-command installer
skill/market-motion/
  SKILL.md                         the editing rules Claude follows
  engine/
    mm.py                          pipeline: new, cut, faces, build, snap, render, mix, check
    lib.py                         motion-graphic building blocks (charts, counters, lanes, timelines, ...)
    template.html                  look and animation engine (GSAP, rendered by Hyperframes)
    music.py                       original calm music generator (no samples)
    check_setup.py, tools.py       dependency checker / installer, tool finder
    sfx/                           calm sound kit (see CREDITS.md)
    examples/                      video.py template and a full worked example
```

## Requirements

Python 3.9+ (standard library only), ffmpeg, Node.js 18+, whisper.cpp with `ggml-large-v3-turbo-q5_0.bin` (speech-to-text for word timings), internet at render time. No text-to-speech is included or needed. Everything except Python and Homebrew is installed by `install.sh`.

## Licence

MIT. See `LICENSE`. Sound-effect credits are in `skill/market-motion/engine/sfx/CREDITS.md`.

Use only footage, music, logos and images that you own or are licensed to use.
