#!/usr/bin/env python3
"""market-motion pipeline. Run from anywhere:

  python3 mm.py new    <project> <input.mp4|mp3|wav> [--script script.txt] [--lang en]
  python3 mm.py cut    <project>      # remove pauses + DROPS from video.py, re-transcribe the cut voice
  python3 mm.py faces  <project>      # cut the face shots listed in FACES (footage only)
  python3 mm.py build  <project>      # write index.html from video.py, check rules, lint
  python3 mm.py snap   <project>      # snapshot frames -> <project>/snap/contact-sheet*.jpg
  python3 mm.py render <project>      # render renders/video.mp4 (Hyperframes)
  python3 mm.py mix    <project>      # calm SFX + music + voice, master -14 LUFS, mux to export/<TITLE>.mp4
  python3 mm.py check  <project>      # every rule check, writes export/report.txt
"""
import difflib, importlib.util, json, os, re, shutil, subprocess, sys

ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ENGINE)
from tools import FFMPEG, FFPROBE, HF, duration, has_video, lufs, run, silences, transcribe  # noqa: E402

# ---------- calm sound kit (see SKILL.md section 7)
KIT = {"swish": ("swish", -28), "swish2": ("swish2", -28), "click": ("click", -22), "bell": ("bell", -26),
       "bell2": ("bell2", -26), "down": ("down", -26), "rise": ("rise", -28), "swell": ("swell", -24), "impact": ("impact", -22)}
PRIORITY = {"impact": 0, "click": 1, "bell": 2, "bell2": 2, "down": 3, "swell": 3, "rise": 4, "swish": 5, "swish2": 5}
MIN_GAP = 1.5
BUDGET = [(0, 5, 3), (5, 60, 8)]          # (from, to, max cues); every later minute: PER_MIN
PER_MIN = 8
MAX_IMPACTS = 3


def load(proj):
    sys.path.insert(0, proj)
    spec = importlib.util.spec_from_file_location("video", os.path.join(proj, "video.py"))
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)
    voice = os.path.join(proj, "work", "voice.wav")
    if getattr(v, "TOTAL", None) is None and os.path.exists(voice):
        v.TOTAL = round(duration(voice) + getattr(v, "END_CARD", 2.5), 2)
    return v


def norm(w):
    return re.sub(r"[^a-z0-9.%]", "", w.lower())


# ---------------------------------------------------------------- new
def cmd_new(proj, src, script=None, lang="auto"):
    src = os.path.abspath(src)
    for d in ("raw", "work", "assets", "renders", "export", "snap"):
        os.makedirs(os.path.join(proj, d), exist_ok=True)
    dst = os.path.join(proj, "raw", os.path.basename(src).replace(" ", "_"))
    if not os.path.exists(dst):
        try:
            os.symlink(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    if script:
        shutil.copy2(script, os.path.join(proj, "script.txt"))
    raw = os.path.join(proj, "work", "raw.wav")
    run([FFMPEG, "-v", "error", "-y", "-i", dst, "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", raw])
    words = transcribe(raw, os.path.join(proj, "work", "raw_words.json"), lang)
    vid = has_video(dst)
    # report: pauses and retake suspects
    sil = silences(raw, -35, 0.3)
    dur = duration(raw)
    lines = [f"input: {os.path.basename(dst)}  ({'video' if vid else 'audio only'}, {dur:.1f} s, {len(words)} words)",
             f"pauses over 0.3 s: {len(sil)}, total {sum(b - a for a, b in sil):.1f} s", "", "LONG PAUSES (> 1 s) - check for retakes around each:"]
    for a, b in sil:
        if b - a > 1.0:
            before = " ".join(x["w"] for x in words if a - 4 < x["t1"] <= a + 0.2)
            after = " ".join(x["w"] for x in words if b - 0.2 <= x["t0"] < b + 4)
            lines.append(f"  {a:7.2f}-{b:7.2f} ({b - a:.1f}s)  ...{before[-70:]} || {after[:70]}...")
    lines += ["", "RETAKE / FLUFF SUSPECTS (repeated phrases, fillers):"]
    nw = [norm(x["w"]) for x in words]
    seen = set()
    for i in range(len(nw)):
        for j in range(i + 3, min(len(nw), i + 45)):
            k = 0
            while j + k < len(nw) and i + k < j and nw[i + k] and nw[i + k] == nw[j + k]:
                k += 1
            if k >= 3 and words[j]["t0"] - words[i]["t0"] < 30 and (i, j) not in seen:
                seen.add((i, j))
                lines.append(f"  repeat x{k}: {words[i]['t0']:.2f} and {words[j]['t0']:.2f}: \"{' '.join(x['w'] for x in words[i:i + k])}\"")
    for x in words:
        if norm(x["w"]) in ("um", "uh", "umm", "uhh", "sorry", "oops", "again", "retake", "hmm"):
            lines.append(f"  filler/flag \"{x['w']}\" at {x['t0']:.2f}")
    rep = os.path.join(proj, "work", "prep_report.txt")
    open(rep, "w").write("\n".join(lines) + "\n")
    vp = os.path.join(proj, "video.py")
    if not os.path.exists(vp):
        t = open(os.path.join(ENGINE, "examples", "video_template.py")).read()
        t = t.replace('INPUT = ""', f'INPUT = "raw/{os.path.basename(dst)}"').replace("HAS_VIDEO = True", f"HAS_VIDEO = {vid}")
        t = t.replace('SCRIPT = None', 'SCRIPT = "script.txt"' if script else 'SCRIPT = None').replace('LANG = "auto"', f'LANG = "{lang}"')
        open(vp, "w").write(t)
    print("\n".join(lines))
    print(f"\nwrote {rep}, work/raw_words.txt and video.py. Next: set DROPS in video.py, then `mm.py cut {proj}`.")


# ---------------------------------------------------------------- cut
def cmd_cut(proj):
    v = load(proj)
    raw = os.path.join(proj, "work", "raw.wav")
    pad = getattr(v, "PAD", 0.10)
    dur = duration(raw)
    gaps = [(a + pad if a > 0 else 0.0, b - pad) for a, b in silences(raw, -35, getattr(v, "MIN_PAUSE", 0.3))]
    gaps += [tuple(x) for x in getattr(v, "DROPS", [])]
    gaps.sort()
    keep, t = [], 0.0
    for a, b in gaps:
        if a > t:
            keep.append((round(t, 3), round(a, 3)))
        t = max(t, b)
    if t < dur:
        keep.append((round(t, 3), round(dur, 3)))
    keep = [k for k in keep if k[1] - k[0] > 0.05]
    parts, labels, ot, edl = [], [], 0.0, []
    for i, (a, b) in enumerate(keep):
        d = b - a
        parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.3f}:d=0.008[a{i}]")
        labels.append(f"[a{i}]")
        edl.append({"src": [a, b], "out": [round(ot, 3), round(ot + d, 3)]})
        ot += d
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keep)}:v=0:a=1[o]"
    run([FFMPEG, "-v", "error", "-y", "-i", raw, "-filter_complex", fc, "-map", "[o]", "-c:a", "pcm_s24le",
         os.path.join(proj, "work", "voice.wav")])
    json.dump(edl, open(os.path.join(proj, "work", "edl.json"), "w"), indent=1)
    transcribe(os.path.join(proj, "work", "voice.wav"), os.path.join(proj, "work", "words.json"), getattr(v, "LANG", "auto"))
    print(f"kept {len(keep)} ranges: {dur:.2f} s -> {ot:.2f} s. Words with output times: work/words.txt")


# ---------------------------------------------------------------- faces
def cmd_faces(proj):
    v = load(proj)
    if not v.HAS_VIDEO or not v.FACES:
        print("no face shots (audio-only input or FACES empty)")
        return
    src = os.path.join(proj, v.INPUT)
    edl = json.load(open(os.path.join(proj, "work", "edl.json")))
    wh = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                        capture_output=True, text=True).stdout.strip().split(",")
    W_, H_ = int(wh[0]), int(wh[1])
    fx, fy = getattr(v, "FACE_X", 0.5), getattr(v, "FACE_Y", 0.3)
    tmp = os.path.join(proj, "work", "fc")
    os.makedirs(tmp, exist_ok=True)
    for k, (w0, w1) in enumerate(v.FACES, 1):
        w0 -= 0.3
        w1 += 0.3
        frac = 0.75 if k % 2 else 0.58          # alternate medium and close framing
        cw = int(W_ * frac) // 2 * 2
        ch = int(cw * 9 / 16) // 2 * 2
        cx = min(max(0, int(fx * W_ - cw / 2)), W_ - cw) // 2 * 2
        cy = min(max(0, int(fy * H_ - ch * 0.32)), H_ - ch) // 2 * 2
        lst = []
        for j, r in enumerate(edl):
            o0, o1 = r["out"]
            a, b = max(w0, o0), min(w1, o1)
            if b - a > 0.01:
                o = os.path.join(tmp, f"f{k}_{j}.mp4")
                run([FFMPEG, "-v", "error", "-y", "-ss", f"{r['src'][0] + a - o0:.3f}", "-i", src, "-t", f"{b - a:.3f}", "-an", "-vf",
                     f"crop={cw}:{ch}:{cx}:{cy},scale=1920:1080:flags=lanczos,fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "fast", o])
                lst.append(f"file '{os.path.abspath(o)}'")
        open(os.path.join(tmp, f"l{k}.txt"), "w").write("\n".join(lst))
        run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, f"l{k}.txt"), "-c", "copy",
             os.path.join(proj, "assets", f"face{k}.mp4")])
        print(f"face{k}: {w0 + 0.3:.2f}-{w1 - 0.3:.2f} s, {len(lst)} piece(s), crop {cw}x{ch} at {cx},{cy}")


# ---------------------------------------------------------------- rule checks shared by build/check
def rule_report(v):
    out, ok = [], True
    T = v.TOTAL
    cap = sum(b - a for _, a, b in v.CAPS)
    first = sum(max(0, min(b, 60) - a) for _, a, b in v.CAPS if a < 60)
    lim = min(0.10 * T, 1e9)
    good = cap <= lim + 1e-6 and first <= 10
    ok &= good
    out.append(f"{'OK ' if good else 'FAIL'} captions {cap:.1f} s = {100 * cap / T:.1f}% (max 10%), first minute {first:.1f} s (max 10 s)")
    if v.HAS_VIDEO and v.FACES:
        bad = []
        for a, b in v.FACES:
            if a < 5:
                bad.append(f"face at {a} is inside the 5 s motion-graphic open")
            if b > 60.01:
                bad.append(f"face at {a}-{b} runs past 1:00")
            if not 2.4 <= b - a <= 4.2:
                bad.append(f"face at {a}-{b} lasts {b - a:.1f} s (3-4 s)")
        for lo, hi in [(5, 15), (15, 30), (30, 45), (45, 60)]:
            if hi <= T:
                n = sum(1 for a, _ in v.FACES if lo <= a < hi)
                if n != 1:
                    bad.append(f"{n} face shots start in {lo}-{hi} s (need exactly 1)")
        ok &= not bad
        out.append(("OK " if not bad else "FAIL") + " face shots: " + (", ".join(f"{a}-{b}" for a, b in v.FACES) if not bad else "; ".join(bad)))
    # coverage: every moment is a scene or a face
    spans = sorted([tuple(s) for s in v.SCENES] + [tuple(f) for f in v.FACES])
    t, holes = 0.0, []
    for a, b in spans:
        if a - t > 0.3:
            holes.append(f"{t:.2f}-{a:.2f}")
        t = max(t, b)
    if T - t > 0.3:
        holes.append(f"{t:.2f}-{T:.2f}")
    ok &= not holes
    out.append(("OK " if not holes else "FAIL") + " timeline coverage" + ("" if not holes else ": empty " + ", ".join(holes)))
    return ok, out


# ---------------------------------------------------------------- build
def cmd_build(proj):
    import lib
    v = load(proj)
    open(os.path.join(proj, "index.html"), "w", encoding="utf-8").write(lib.page(v))
    ok, rep = rule_report(v)
    print(f"built index.html ({v.TOTAL} s)\n" + "\n".join(rep))
    r = subprocess.run(HF + ["lint", "."], cwd=proj, capture_output=True, text=True)
    m = re.findall(r"(\d+) error", r.stdout + r.stderr)
    print(f"lint: {m[-1] if m else '?'} error(s)")
    if m and m[-1] != "0":
        print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "✗" in l or "error" in l.lower())[:3000])


def cmd_snap(proj):
    v = load(proj)
    ts = []
    for a, b in v.SCENES:
        ts += [round(a + 0.9, 2), round((a + b) / 2, 2), round(max(a + 1, b - 0.5), 2)]
    ts += [round((a + b) / 2, 2) for a, b in v.FACES]
    ts = sorted(set(t for t in ts if t < v.TOTAL))
    run(HF + ["snapshot", ".", "--at", ",".join(map(str, ts)), "--no-end", "-o", "snap", "--timeout", "180000"], cwd=proj)
    print("look at snap/contact-sheet*.jpg")


def cmd_render(proj):
    run(HF + ["render", ".", "-o", "renders/video.mp4", "--fps", "30", "--quiet"], cwd=proj)
    print(f"rendered renders/video.mp4 ({duration(os.path.join(proj, 'renders', 'video.mp4')):.1f} s)")


# ---------------------------------------------------------------- mix
def budget(cues):
    """Calm-sound rules: priority first, 1.5 s apart, per-window caps, max 3 impacts."""
    order = sorted(cues, key=lambda c: (PRIORITY.get(c[1], 9), c[0]))
    kept, dropped = [], []
    for t, k in order:
        cap = PER_MIN
        lo, hi = 60 * int(t // 60), 60 * int(t // 60) + 60
        for a, b, n in BUDGET:
            if a <= t < b:
                cap, lo, hi = n, a, b
        n_win = sum(1 for x, _ in kept if lo <= x < hi)
        near = any(abs(x - t) < MIN_GAP for x, _ in kept)
        imp = k == "impact" and sum(1 for _, y in kept if y == "impact") >= MAX_IMPACTS
        if near or n_win >= cap or imp or k not in KIT:
            dropped.append((t, k))
        else:
            kept.append((t, k))
    return sorted(kept), sorted(dropped)


def cmd_mix(proj):
    v = load(proj)
    T = v.TOTAL
    w = os.path.join(proj, "work")
    kept, dropped = budget([tuple(c) for c in getattr(v, "CUES", [])])
    json.dump({"kept": kept, "dropped": dropped}, open(os.path.join(w, "cues.json"), "w"))
    if dropped:
        print(f"calm-sound budget dropped {len(dropped)} cue(s): " + ", ".join(f"{t}:{k}" for t, k in dropped))
    sfx = os.path.join(ENGINE, "sfx")
    # voice
    run([FFMPEG, "-v", "error", "-y", "-i", os.path.join(w, "voice.wav"), "-af",
         f"aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=80,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120:makeup=2,apad,atrim=0:{T}",
         "-c:a", "pcm_s24le", os.path.join(w, "voice_p.wav")])
    vI, _ = lufs(os.path.join(w, "voice_p.wav"))
    # sfx bus
    if kept:
        ins, parts, labs = [], [], []
        for i, (t, k) in enumerate(kept):
            f, g = KIT[k]
            ins += ["-i", os.path.join(sfx, f + ".wav")]
            parts.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=150,lowpass=f=9000,"
                         f"afade=t=in:d=0.01,volume={g}dB,adelay={int(t * 1000)}|{int(t * 1000)}[s{i}]")
            labs.append(f"[s{i}]")
        fc = ";".join(parts) + ";" + "".join(labs) + f"amix=inputs={len(kept)}:normalize=0:dropout_transition=0,apad,atrim=0:{T}[o]"
        run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[o]",
             "-c:a", "pcm_s24le", os.path.join(w, "sfx_raw.wav")])
        sI, _ = lufs(os.path.join(w, "sfx_raw.wav"))
        adj = (vI - 19) - sI if sI is not None and vI is not None else 0   # SFX bus sits 19 dB under the voice
        run([FFMPEG, "-v", "error", "-y", "-i", os.path.join(w, "sfx_raw.wav"), "-af", f"volume={adj:.2f}dB", "-c:a", "pcm_s24le",
             os.path.join(w, "sfx_bus.wav")])
    else:
        run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(T), os.path.join(w, "sfx_bus.wav")])
    # music: the user's file, or an original calm bed
    music = getattr(v, "MUSIC", None)
    mpath = os.path.join(proj, music) if music else os.path.join(w, "music_gen.wav")
    if not music:
        run([sys.executable, os.path.join(ENGINE, "music.py"), mpath, str(T), str(getattr(v, "MUSIC_VARIANT", 1))])
    voice_end = duration(os.path.join(w, "voice.wav"))
    run([FFMPEG, "-v", "error", "-y", "-stream_loop", "-1", "-i", mpath, "-af",
         f"aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{T},afade=t=in:d=0.8,afade=t=out:st={max(0, T - 1.8):.2f}:d=1.8",
         "-c:a", "pcm_s24le", os.path.join(w, "music_raw.wav")])
    mI, _ = lufs(os.path.join(w, "music_raw.wav"))
    g = (vI - 18.5) - mI
    run([FFMPEG, "-v", "error", "-y", "-i", os.path.join(w, "music_raw.wav"), "-i", os.path.join(w, "voice_p.wav"), "-filter_complex",
         f"[0:a]volume={g:.2f}dB,volume='if(gte(t,{voice_end:.2f}),1.5,1)':eval=frame[m];"
         "[m][1:a]sidechaincompress=threshold=0.03:ratio=3:attack=40:release=350[o]",
         "-map", "[o]", "-c:a", "pcm_s24le", os.path.join(w, "music_d.wav")])
    # master
    ins = ["-i", os.path.join(w, "voice_p.wav"), "-i", os.path.join(w, "music_d.wav"), "-i", os.path.join(w, "sfx_bus.wav")]
    pre = "[0:a][1:a][2:a]amix=inputs=3:normalize=0[s];[s]"
    m = subprocess.run([FFMPEG, "-hide_banner", "-y", *ins, "-filter_complex", pre + "loudnorm=I=-14:TP=-1:LRA=11:print_format=json[o]",
                        "-map", "[o]", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    run([FFMPEG, "-v", "error", "-y", *ins, "-filter_complex", pre + ln + ",aresample=48000[o]", "-map", "[o]", "-c:a", "pcm_s24le",
         os.path.join(w, "mix.wav")])
    stats = {"voice_I": vI, "sfx_I": lufs(os.path.join(w, "sfx_bus.wav"))[0], "music_I": lufs(os.path.join(w, "music_d.wav"))[0], "cues": len(kept)}
    json.dump(stats, open(os.path.join(w, "mix_stats.json"), "w"))
    vid = os.path.join(proj, "renders", "video.mp4")
    if os.path.exists(vid):
        out = os.path.join(proj, "export", f"{getattr(v, 'TITLE', 'video')}.mp4")
        run([FFMPEG, "-v", "error", "-y", "-i", vid, "-i", os.path.join(w, "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
             "-preset", "medium", "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", out])
        print(f"exported {out}")
    print(f"mix: {len(kept)} cues, voice {vI} LUFS, sfx bus {stats['sfx_I']}, music {stats['music_I']}")


# ---------------------------------------------------------------- check
def cmd_check(proj):
    v = load(proj)
    out = os.path.join(proj, "export", f"{getattr(v, 'TITLE', 'video')}.mp4")
    lines = [f"REPORT for {os.path.basename(out)}"]
    ok, rep = rule_report(v)
    lines += rep
    if os.path.exists(out):
        d = duration(out)
        log = subprocess.run([FFMPEG, "-hide_banner", "-i", out, "-vf", "freezedetect=n=-60dB:d=0.5", "-map", "0:v", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        fr = re.findall(r"freeze_start: ([0-9.]+)", log)
        lines.append(("OK " if not fr else "FAIL") + f" no still frames (freezedetect)" + ("" if not fr else ": still at " + ", ".join(fr)))
        I, P = lufs(out)
        lines.append(("OK " if I and abs(I + 14) <= 0.6 and P <= -0.9 else "FAIL") + f" loudness {I} LUFS, peak {P} dBFS (target -14 / -1)")
        lines.append(f"     length {d:.1f} s, 1920x1080 30 fps")
    else:
        lines.append("FAIL export missing: run render and mix")
    cj = os.path.join(proj, "work", "cues.json")
    if os.path.exists(cj):
        kept = json.load(open(cj))["kept"]
        T = v.TOTAL
        per = [sum(1 for t, _ in kept if m * 60 <= t < m * 60 + 60) for m in range(int(T // 60) + 1)]
        st = json.load(open(os.path.join(proj, "work", "mix_stats.json")))
        gap = st["voice_I"] - st["sfx_I"] if st.get("sfx_I") is not None else 99
        good = all(n <= (11 if i == 0 else PER_MIN) for i, n in enumerate(per)) and gap >= 17.5
        lines.append(("OK " if good else "FAIL") + f" calm sound: {len(kept)} cues, per minute {per}, SFX {gap:.1f} dB under voice (18-20), "
                     f"music {st['voice_I'] - st['music_I']:.1f} dB under voice")
    # words vs script (or vs raw transcript minus drops)
    ww = [x["w"] for x in json.load(open(os.path.join(proj, "work", "words.json")))]
    sp = getattr(v, "SCRIPT", None)
    if sp and os.path.exists(os.path.join(proj, sp)):
        ref = open(os.path.join(proj, sp), encoding="utf-8").read().split()
        what = "script"
    else:
        drops = [tuple(x) for x in getattr(v, "DROPS", [])]
        ref = [x["w"] for x in json.load(open(os.path.join(proj, "work", "raw_words.json"))) if not any(a <= x["t0"] < b for a, b in drops)]
        what = "raw transcript minus DROPS"
    sm = difflib.SequenceMatcher(None, [norm(x) for x in ref], [norm(x) for x in ww])
    lines.append(f"{'OK ' if sm.ratio() > 0.9 else 'CHECK'} words match {what}: {100 * sm.ratio():.1f}%")
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op != "equal" and (a2 - a1 > 1 or b2 - b1 > 1):
            lines.append(f"     {op}: {' '.join(ref[a1:a2])[:80]!r} -> {' '.join(ww[b1:b2])[:80]!r}")
    lines.append("NOT CHECKED: how it sounds (listen), facts in the script.")
    open(os.path.join(proj, "export", "report.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    c, proj = sys.argv[1], os.path.abspath(sys.argv[2])
    if c == "new":
        a = sys.argv[3:]
        script = a[a.index("--script") + 1] if "--script" in a else None
        lang = a[a.index("--lang") + 1] if "--lang" in a else "auto"
        cmd_new(proj, a[0], script, lang)
    else:
        {"cut": cmd_cut, "faces": cmd_faces, "build": cmd_build, "snap": cmd_snap, "render": cmd_render, "mix": cmd_mix,
         "check": cmd_check}[c](proj)
