# Finds the command-line tools on macOS, Linux and Windows, and holds shared helpers.
import json, os, re, shutil, subprocess, sys

HOME = os.path.expanduser("~")
ENGINE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(HOME, ".market-motion")


def find(name, extra=()):
    env = os.environ.get(name.upper().replace("-", "_"))
    if env and os.path.exists(env):
        return env
    p = shutil.which(name) or shutil.which(name + ".exe") or shutil.which(name + ".cmd")
    if p:
        return p
    for d in extra:
        for n in (name, name + ".exe"):
            q = os.path.join(d, n)
            if os.path.exists(q):
                return q
    return None


FFMPEG = find("ffmpeg") or "ffmpeg"
FFPROBE = find("ffprobe") or "ffprobe"
NPX = find("npx") or "npx"
WHISPER = find("whisper-cli", [os.path.join(TOOLS_DIR, "whisper.cpp", "build", "bin"),
                               os.path.join(TOOLS_DIR, "whisper.cpp", "build", "bin", "Release")]) or "whisper-cli"
MODEL = os.environ.get("WHISPER_MODEL", os.path.join(HOME, ".whisper-models", "ggml-large-v3-turbo-q5_0.bin"))
HF = [NPX, "--yes", "hyperframes@0.9.7"]


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)


def duration(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def has_video(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return "video" in out and not path.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".flac"))


def silences(path, db=-35, d=0.3):
    log = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-af", f"silencedetect=noise={db}dB:d={d}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    return list(zip(st, en))


def lufs(path):
    log = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[0-9.]+) LUFS", log)
    p = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", log)
    return (float(i[-1]) if i else None, float(p[-1]) if p else None)


def transcribe(wav, out_json, lang="auto"):
    """Word timings in ~15 s windows that start inside pauses (whole-file runs drift and smear retakes)."""
    if not os.path.exists(MODEL):
        sys.exit(f"Whisper model not found: {MODEL}  (run the installer, or set WHISPER_MODEL)")
    mids = [(a + b) / 2 for a, b in silences(wav, -36, 0.07)]
    dur = duration(wav)
    cuts = [0.0]
    while dur - cuts[-1] > 19:
        c = [m for m in mids if cuts[-1] + 11 <= m <= cuts[-1] + 18]
        cuts.append(c[-1] if c else cuts[-1] + 15)
    cuts.append(dur)
    words, tmp = [], out_json + ".tmp"
    for a, b in zip(cuts, cuts[1:]):
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", wav,
             "-ar", "16000", "-ac", "1", tmp + ".wav"])
        subprocess.run([WHISPER, "-m", MODEL, "-f", tmp + ".wav", "-l", lang, "-mc", "0", "-ml", "1", "-sow", "-ojf",
                        "-of", tmp, "-np", "-t", "8"], capture_output=True)
        j = json.loads(open(tmp + ".json", "rb").read().decode("utf-8", "replace"))
        for s in j["transcription"]:
            w = s["text"].strip()
            if w and not w.startswith("["):
                words.append({"t0": round(a + s["offsets"]["from"] / 1000, 2), "t1": round(a + s["offsets"]["to"] / 1000, 2), "w": w})
    for f in (tmp + ".wav", tmp + ".json"):
        if os.path.exists(f):
            os.remove(f)
    json.dump(words, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    txt = out_json[:-5] + ".txt"
    with open(txt, "w", encoding="utf-8") as fw:
        row, cur = [], 0
        for x in words:
            if int(x["t0"] // 5) != cur and row:
                fw.write(f"[{cur * 5:>5}s] " + " ".join(row) + "\n")
                row = []
            cur = int(x["t0"] // 5)
            row.append(f"{x['t0']:.2f}:{x['w']}")
        if row:
            fw.write(f"[{cur * 5:>5}s] " + " ".join(row) + "\n")
    return words
