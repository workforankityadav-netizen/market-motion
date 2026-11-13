# Calm original music bed (no samples, no licence questions): soft pads, a gentle pluck, a light pulse.
# usage: python3 music.py out.wav SECONDS [VARIANT]
# Writes a seamless 8-bar loop and repeats it to SECONDS with a fade-out. VARIANT (1-6) changes key, tempo and pattern.
import array, math, os, random, subprocess, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import FFMPEG

out, secs = sys.argv[1], float(sys.argv[2])
v = int(sys.argv[3]) if len(sys.argv) > 3 else 1
SR = 44100
rnd = random.Random(7 + v)
PROG = [[[57, 60, 64, 67], [53, 57, 60, 64], [60, 64, 67, 71], [55, 59, 62, 67]],
        [[50, 57, 60, 65], [46, 53, 57, 62], [53, 57, 60, 64], [48, 55, 60, 64]],
        [[52, 59, 62, 67], [48, 55, 59, 64], [55, 59, 62, 66], [50, 57, 62, 66]]]
chords = PROG[(v - 1) % 3]
BPM = [86, 80, 92, 84, 88, 78][(v - 1) % 6]
beat = 60 / BPM
bar = 4 * beat
BARS = 8
N = int(BARS * bar * SR)
buf = [0.0] * N


def mid(x):
    return 440 * 2 ** ((x - 69) / 12)


def add(t0, dur, fn):
    a = int(t0 * SR)
    for i in range(int(dur * SR)):
        buf[(a + i) % N] += fn(i / SR)


def pad(t0, f, d, amp):
    add(t0, d, lambda t: amp * min(1, t / 0.9) * min(1, max(0, d - t) / 0.9) *
        (math.sin(2 * math.pi * f * t) + 0.45 * math.sin(2 * math.pi * f * 1.003 * t) + 0.2 * math.sin(4 * math.pi * f * t)))


def pluck(t0, f, amp):
    add(t0, 1.2, lambda t: amp * math.exp(-t * 4.2) * min(1, t * 300) *
        (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(4 * math.pi * f * t) * math.exp(-t * 8)))


def sub(t0, f, d, amp):
    add(t0, d, lambda t: amp * min(1, t * 60) * min(1, max(0, d - t) * 8) * math.sin(2 * math.pi * f * t))


def pulse(t0, amp):
    ph = [0.0]

    def fn(t):
        ph[0] += 2 * math.pi * (52 + 40 * math.exp(-t * 25)) / SR
        return amp * math.sin(ph[0]) * math.exp(-t * 9)
    add(t0, 0.3, fn)


def hat(t0, amp):
    st = [0.0]

    def fn(t):
        x = rnd.uniform(-1, 1)
        y = x - st[0]
        st[0] = x
        return amp * y * math.exp(-t * 90)
    add(t0, 0.05, fn)


arp = [[0, 2, 1, 3, 2, 1], [0, 1, 2, 3, 2, 1], [3, 1, 2, 0, 2, 1]][(v - 1) % 3]
for b in range(BARS):
    t = b * bar
    c = chords[b % 4]
    for p in c:
        pad(t, mid(p), bar + 0.4, 0.022)
    sub(t, mid(c[0] - 12), bar * 0.95, 0.10)
    for s, k in enumerate(arp):
        if (b + s) % 3 != 2:
            pluck(t + s * bar / 6, mid(c[k] + 12), 0.045)
    pulse(t, 0.12)
    pulse(t + 2 * beat, 0.08)
    for s in range(8):
        hat(t + s * beat / 2, 0.012 if s % 2 else 0.006)
pk = max(abs(x) for x in buf)
g = 0.6 / pk
loop = out + ".loop.wav"
w = wave.open(loop, "wb")
w.setnchannels(1)
w.setsampwidth(2)
w.setframerate(SR)
w.writeframes(array.array("h", (int(x * g * 32767) for x in buf)).tobytes())
w.close()
subprocess.run([FFMPEG, "-v", "error", "-y", "-stream_loop", "-1", "-i", loop, "-t", f"{secs:.2f}", "-af",
                f"afade=t=in:d=1.5,afade=t=out:st={max(0, secs - 2.5):.2f}:d=2.5,aformat=sample_rates=48000:channel_layouts=stereo",
                "-c:a", "pcm_s16le", out], check=True)
os.remove(loop)
print(f"music: variant {v}, {BPM} bpm, {secs:.1f} s -> {out}")
