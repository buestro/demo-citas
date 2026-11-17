"""Original cozy lo-fi track for the demo video: Rhodes-style chords, swung drums, vinyl crackle. Synthesized, no samples."""
import math, random, struct, wave

SR, DUR = 44100, 49.6
BPM = 76
BEAT = 60 / BPM
BAR = BEAT * 4
SWING = 0.62          # 8th-note swing: the off-beat lands at 62 % of the beat
random.seed(11)
TAU = 2 * math.pi
n = int(SR * DUR)
L = [0.0] * n
R = [0.0] * n

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def rhodes(start, dur, m, amp, pan=0.0):
    """Electric-piano-ish tone: sine + soft harmonic, a short 'tine' partial, slow decay, light tape wobble."""
    f = hz(m); i0 = int(start * SR); ln = int(dur * SR)
    for k in range(ln):
        i = i0 + k
        if i >= n: break
        t = k / SR
        wob = 0.0025 * math.sin(TAU * 0.55 * t + m)
        env = min(1.0, t / 0.006) * math.exp(-t / 1.1) * min(1.0, (dur - t) / 0.35)
        ph = TAU * f * t
        v = math.sin(ph + wob * 40) + 0.28 * math.sin(2 * ph) + 0.10 * math.sin(3 * ph)
        v += 0.35 * math.sin(TAU * f * 4 * t) * math.exp(-t / 0.07)   # tine attack
        v *= amp * env * (1 + 0.08 * math.sin(TAU * 4.2 * t))        # gentle tremolo
        L[i] += v * (1 - pan); R[i] += v * (1 + pan)

def bass(start, dur, m, amp):
    f = hz(m); i0 = int(start * SR); ln = int(dur * SR)
    for k in range(ln):
        i = i0 + k
        if i >= n: break
        t = k / SR
        env = min(1.0, t / 0.01) * math.exp(-t / 0.55) * min(1.0, (dur - t) / 0.1)
        v = (math.sin(TAU * f * t) + 0.18 * math.sin(TAU * 2 * f * t)) * amp * env
        L[i] += v; R[i] += v

def kick(start, amp):
    i0 = int(start * SR)
    for k in range(int(0.28 * SR)):
        i = i0 + k
        if i >= n: break
        t = k / SR
        f = 50 + 90 * math.exp(-t / 0.035)
        v = math.sin(TAU * f * t) * math.exp(-t / 0.11) * amp
        L[i] += v; R[i] += v

def snare(start, amp):
    i0 = int(start * SR)
    for k in range(int(0.22 * SR)):
        i = i0 + k
        if i >= n: break
        t = k / SR
        v = (random.uniform(-1, 1) * 0.8 + math.sin(TAU * 185 * t) * 0.5) * math.exp(-t / 0.07) * amp
        L[i] += v * 0.9; R[i] += v * 1.1

def hat(start, amp):
    i0 = int(start * SR); prev = 0.0
    for k in range(int(0.06 * SR)):
        i = i0 + k
        if i >= n: break
        t = k / SR
        x = random.uniform(-1, 1)
        v = (x - prev) * math.exp(-t / 0.018) * amp   # crude high-pass
        prev = x
        L[i] += v * 1.1; R[i] += v * 0.9

# Cmaj9 - Am9 - Dm9 - G13 (jazzy voicings, MIDI)
CH = [[52, 59, 62, 67, 71], [57, 60, 64, 67, 71], [53, 57, 60, 64, 69], [53, 59, 62, 64, 69]]
ROOT = [36, 33, 38, 31]
bars = int(DUR / BAR) + 1
for b in range(bars):
    t0 = b * BAR
    ch = CH[b % 4]
    # chord hits: beat 1 (long) and the "and" of beat 2 (short), slightly strummed and humanised
    for hit, (off, ln, a) in enumerate([(0.0, BEAT * 2.4, 0.034), (BEAT * (1 + SWING), BEAT * 1.3, 0.026), (BEAT * 3, BEAT * 0.9, 0.018)]):
        for j, m in enumerate(ch):
            rhodes(t0 + off + j * 0.012 + random.uniform(0, 0.008), ln, m, a * random.uniform(0.9, 1.05), pan=(j - 2) * 0.1)
    bass(t0, BEAT * 1.6, ROOT[b % 4], 0.11)
    bass(t0 + BEAT * (2 + SWING), BEAT * 1.2, ROOT[b % 4] + (7 if b % 2 else 0), 0.08)
    # drums
    kick(t0, 0.5); kick(t0 + BEAT * (1 + SWING), 0.34); kick(t0 + BEAT * 2.0, 0.28 if b % 2 else 0.0)
    snare(t0 + BEAT * 1, 0.20); snare(t0 + BEAT * 3, 0.22)
    for e in range(8):
        pos = (e // 2) + (SWING if e % 2 else 0.0)
        hat(t0 + BEAT * pos, (0.10 if e % 2 else 0.065) * random.uniform(0.7, 1.1))

# vinyl crackle: faint hiss + sparse pops
for i in range(n):
    h = random.uniform(-1, 1) * 0.0035
    L[i] += h; R[i] += h * random.uniform(0.7, 1.0)
for _ in range(int(DUR * 7)):
    i = random.randrange(n - 200); a = random.uniform(0.01, 0.045)
    for k in range(random.randint(8, 40)):
        v = random.uniform(-1, 1) * a * math.exp(-k / 9)
        L[i + k] += v; R[i + k] += v

def echo(x, delay, fb):
    d = int(delay * SR)
    for i in range(d, n): x[i] += x[i - d] * fb
echo(L, BEAT * 0.75, 0.22); echo(R, BEAT * 0.5, 0.22)

peak = max(max(abs(v) for v in L), max(abs(v) for v in R))
g = 0.8 / peak
fi, fo = int(1.5 * SR), int(3.0 * SR)
with wave.open("lofi.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    out = bytearray()
    for i in range(n):
        f = min(1.0, i / fi) * min(1.0, (n - i) / fo)
        out += struct.pack("<hh", int(max(-1, min(1, L[i] * g * f)) * 32767), int(max(-1, min(1, R[i] * g * f)) * 32767))
    w.writeframes(bytes(out))
print("ok")
