# Synthesizes a 15s 128 BPM track whose hits line up with the reel's scene cuts.
import numpy as np, wave

SR, DUR = 48000, 15.0
B = 60 / 128; L = 4 * B
n = int(SR * DUR); mix = np.zeros((n, 2))
rng = np.random.default_rng(3)
t_ = lambda d: np.arange(int(SR * d)) / SR

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= n: return
    sig = sig[: n - i] * gain
    mix[i:i + len(sig), 0] += sig * (1 - pan) ** .5
    mix[i:i + len(sig), 1] += sig * (1 + pan) ** .5

def onepole(x, a):  # a: scalar or per-sample lowpass coefficient
    y = np.empty_like(x); s = 0.0; a = np.broadcast_to(a, x.shape)
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y

def kick(d=.45, f0=160, f1=42):
    t = t_(d); ph = np.cumsum(f1 + (f0 - f1) * np.exp(-t * 30)) / SR * 2 * np.pi
    return np.tanh(2.2 * np.sin(ph) * np.exp(-t * 7))

def noise(d): return rng.uniform(-1, 1, int(SR * d))
def clap(): t = t_(.25); x = noise(.25); x = x - onepole(x, .15); return x * (np.exp(-t * 22) + .5 * np.exp(-((t - .012) % .011) * 400) * (t < .035))
def hat(d=.05): t = t_(d); x = noise(d); return (x - onepole(x, .5)) * np.exp(-t * 90)
def tick(): t = t_(.06); return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120)
def blip(f): t = t_(.18); return np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 30)) * np.exp(-t * 18)

def whoosh(d, rev=False):
    t = t_(d); env = np.sin(np.pi * t / d) ** 2; sweep = (t / d) if not rev else 1 - t / d
    return onepole(noise(d), .01 + .25 * sweep ** 2) * env * 3

def saw(f, d):
    t = t_(d); return sum(((t * f * det) % 1) * 2 - 1 for det in (1, 1.006, .994)) / 3

# --- intro (bar 0): dot pop, letter ticks, no beat yet
add(kick(.6, 90, 40), 0.0, .5)
for i in range(8): add(tick(), .64 + i * .035 + .06, .35, (i - 3.5) / 5)
add(whoosh(.5), 1.35, .5)
add(kick(.8, 200, 38), .9, .7)

# --- drums: bars 1..6, drop out before the outro impact
for beat in range(4, 28):
    at = beat * B
    add(kick(), at, .9)
    if beat % 2: add(clap(), at, .45, .1)
    add(hat(), at + B / 2, .22, .3)
    add(hat(.03), at + B * .75, .1, -.3)
for beat in range(24, 28):  # bar 6 (HUD): 16th hats build
    for s in range(4): add(hat(.025), beat * B + s * B / 4, .12 + .04 * s, .4)

# --- bass: root per bar, pumping 8ths
roots = [0, 55.0, 43.65, 49.0, 41.2, 55.0, 43.65, 36.7]
for bar in range(1, 7):
    for e in range(8):
        at = bar * L + e * B / 2; d = B / 2; t = t_(d)
        env = (1 - np.exp(-t * 40)) * np.exp(-t * 4)
        s = onepole(saw(roots[bar], d), .08) * 1.6 + np.sin(2 * np.pi * roots[bar] * t) * .8
        add(s * env, at, .5)

# --- pad chord (sidechained feel via envelope)
chords = {1: [220, 261.6, 329.6], 2: [174.6, 220, 261.6], 3: [196, 246.9, 293.7], 4: [164.8, 207.7, 246.9], 5: [220, 277.2, 329.6], 6: [174.6, 220, 293.7]}
for bar, ch in chords.items():
    t = t_(L); duck = 1 - .7 * np.exp(-((t % B)) * 12)
    pad = onepole(sum(saw(f, L) for f in ch), .04) * duck * np.minimum(1, t * 20) * np.minimum(1, (L - t) * 20)
    add(pad, bar * L, .22, 0)

# --- sfx synced to picture
for k in range(1, 4): add(blip(880 * 2 ** (k / 12 * 3)), L + k * B, .25, .3 * (k - 2))
add(whoosh(1.1), 3 * L, .6)                      # particle vortex
add(whoosh(.6, rev=True), 3 * L + 1.4, .35)      # text -> sphere
add(whoosh(.55), 5 * L - .55, .7)                # fly-through
for k in range(8): add(blip(660 + 110 * k), 5 * L + k * .05, .12, (k - 4) / 5)
riser_d = L; t = t_(riser_d)                       # riser into outro
add(np.sin(2 * np.pi * np.cumsum(200 + 1400 * (t / riser_d) ** 3) / SR) * (t / riser_d) ** 2 * .5
    + onepole(noise(riser_d), .02 + .5 * (t / riser_d) ** 3) * (t / riser_d) ** 2 * 1.5, 6 * L, .5)

# --- outro impact + tail
imp = 7 * L
add(kick(1.4, 220, 32), imp, 1.3)
add(onepole(noise(1.2), .3) * np.exp(-t_(1.2) * 5), imp, .5)
t = t_(1.9); add(np.sin(2 * np.pi * 36.7 * t) * np.exp(-t * 1.6), imp, .8)
for i, f in enumerate([220, 329.6, 440, 554.4]): add(np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) * np.minimum(1, t * 30), imp + .3 + i * .04, .12, (i - 1.5) / 3)
for i in range(14): add(tick(), imp + .7 + i * .028, .12, (i - 7) / 8)
add(whoosh(.4, rev=True), 14.55, .4)
add(kick(.5, 120, 45), 14.95, .0)

# --- reverb (FFT convolution with decaying noise IR) + master
ir_t = t_(1.2); ir = rng.normal(0, 1, (len(ir_t), 2)) * np.exp(-ir_t * 5)[:, None]
sz = 1 << int(np.ceil(np.log2(n + len(ir_t))))
wet = np.stack([np.fft.irfft(np.fft.rfft(mix[:, c], sz) * np.fft.rfft(ir[:, c], sz), sz)[:n] for c in (0, 1)], 1)
out = mix + wet * .012
out = np.tanh(out * 1.1)
fade = np.minimum(1, (DUR - np.arange(n) / SR) / .08)[:, None]
out = out * fade / np.max(np.abs(out)) * .89
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('ok', out.shape)
