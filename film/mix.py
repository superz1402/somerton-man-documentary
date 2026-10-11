#!/usr/bin/env python3
"""Somerton Man — score, foley and voice mix → out/mix.wav
Music synthesized per the treatment cue map (sparse documentary palette:
drone, heartbeat kick, marimba pluck motif, music-box bell, pizz bass, pads).
Foley driven by events.json (EV from the page). Voice placed from timeline.
Deterministic (seeded). 44.1 kHz stereo float32 → PCM16.
"""
import json, os, sys
import numpy as np
import soundfile as sf

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
SR = 44100
tl = json.load(open('timeline.json'))
ev = json.load(open('events.json'))['ev'] if os.path.exists('events.json') else []
DUR = tl['DUR']
N = int(DUR * SR) + SR
rng = np.random.default_rng(48)
mixL = np.zeros(N, dtype=np.float64)
mixR = np.zeros(N, dtype=np.float64)

def add(buf_l, buf_r, sound, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i < 0: return
    seg = sound[:N - i]
    gl = gain * min(1.0, 1.0 - pan); gr = gain * min(1.0, 1.0 + pan)
    mixL[i:i + len(seg)] += seg * gl
    mixR[i:i + len(seg)] += seg * gr

def env(n, a, d, sus=0.0, r=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    if sus > 0:
        e *= np.where(t < a + sus, 1, np.exp(-(t - a - sus) / max(d, 1e-3)))
    else:
        e *= np.exp(-t / max(d, 1e-3))
    rel = np.minimum(1, np.maximum(0, (n / SR - t) / max(r, 1e-4)))
    return e * rel

def sine(f, n, ph=0.0): return np.sin(2 * np.pi * f * np.arange(n) / SR + ph)

def kick(n=None, f0=110, f1=42, dur=0.32):
    n = n or int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 22)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)

def pluck(f, dur=1.2, bright=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + bright * 0.5 * np.sin(2 * np.pi * f * 3.99 * t) + 0.25 * np.sin(2 * np.pi * f * 2 * t)
    return s * np.exp(-t * 3.2) * env(n, 0.004, dur)

def bell(f, dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) + 0.18 * np.sin(2 * np.pi * f * 5.4 * t) + 0.08 * np.sin(2 * np.pi * f * 8.9 * t))
    return s * np.exp(-t * 1.55)

def noise(n): return rng.standard_normal(n)

def lowpass(x, alpha):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc); y[i] = acc
    return y

def lowpass_fft(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 2)
    return np.fft.irfft(X, len(x))

def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (1 / (1 + (lo / np.maximum(f, 1)) ** 2)) * (1 / (1 + (np.maximum(f, 1) / hi) ** 2))
    return np.fft.irfft(X, len(x))

def waves_bed(n):
    x = lowpass_fft(noise(n), 420)
    t = np.arange(n) / SR
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 11.7 + 1.3)
    return x * swell

def rain_bed(n):
    return bandpass(noise(n), 900, 5200) * 0.5

def room_bed(n):
    return lowpass_fft(noise(n), 260) * 0.5

def drone(freqs, n, detune=0.7, move=0.05):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for i, f in enumerate(freqs):
        ph = rng.uniform(0, 6.28)
        s += np.sin(2 * np.pi * (f * (1 + detune * 0.001 * np.sin(2 * np.pi * move * t / 8 + i))) * t + ph)
        s += 0.35 * np.sin(2 * np.pi * f * 0.5 * t + ph * 1.7)
    return s / (len(freqs) * 1.6)

def pad_chord(freqs, n, a=1.4, r=2.0):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        s += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t + rng.uniform(0, 6)))
        s += 0.2 * np.sin(2 * np.pi * f * 2.001 * t)
    return s / len(freqs) * env(n, a, 3.0, sus=n / SR, r=r)

def hat(n=None, dur=0.05):
    n = n or int(dur * SR)
    return bandpass(noise(n), 6000, 14000) * np.exp(-np.arange(n) / SR * 60) * 0.5

def snap(n=None):
    n = n or int(0.06 * SR)
    return bandpass(noise(n), 1400, 3600) * np.exp(-np.arange(n) / SR * 70) * 0.9

def stamp_sfx(big=False):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 9) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
    click = bandpass(noise(int(0.03 * SR)), 1500, 5200) * np.exp(-np.arange(int(0.03 * SR)) / SR * 160)
    s = boom * 0.9
    s[:len(click)] += click * 0.7
    if big:
        cr = bandpass(noise(int(0.22 * SR)), 900, 6800) * np.exp(-np.arange(int(0.22 * SR)) / SR * 17) * 0.5
        s[:len(cr)] += cr
    return s

def shutter_sfx():
    n = int(0.09 * SR)
    a = bandpass(noise(int(0.02 * SR)), 2400, 7200) * np.exp(-np.arange(int(0.02 * SR)) / SR * 120)
    b = bandpass(noise(int(0.02 * SR)), 1600, 5200) * np.exp(-np.arange(int(0.02 * SR)) / SR * 120)
    s = np.zeros(n); s[:len(a)] += a; s[int(0.045 * SR):int(0.045 * SR) + len(b)] += b
    return s * 0.9

def whoosh_sfx(dur=0.42, up=True):
    n = int(dur * SR)
    x = bandpass(noise(n), 300, 3400)
    envl = np.hanning(n) ** 1.6
    return x * envl * (1 if up else 1)

def paper_sfx(dur=0.3):
    n = int(dur * SR)
    x = bandpass(noise(n), 1500, 7500)
    return x * (np.hanning(n) ** 0.7) * 0.5

def click_sfx():
    n = int(0.025 * SR)
    return bandpass(noise(n), 2600, 8200) * np.exp(-np.arange(n) / SR * 220) * 0.55

def type_sfx():
    n = int(0.06 * SR)
    a = bandpass(noise(int(0.012 * SR)), 1800, 6000) * np.exp(-np.arange(int(0.012 * SR)) / SR * 200)
    s = np.zeros(n); s[:len(a)] += a * 0.8
    s[int(0.03 * SR):int(0.03 * SR) + len(a)] += a[::-1] * 0.45
    return s

def bell_hit(f=2093):
    return bell(f, 3.2) * 0.8

def drawer_sfx():
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    slide = lowpass_fft(noise(n), 500) * np.hanning(n) * 0.8
    thud = kick(int(0.2 * SR), 90, 45, 0.2) * 0.7
    s = slide.copy()
    s[int(0.4 * SR):int(0.4 * SR) + len(thud)] += thud
    return s

def heart(t0):
    a = kick(int(0.22 * SR), 82, 40, 0.22) * 0.5
    b = kick(int(0.18 * SR), 74, 38, 0.18) * 0.38
    add(mixL, mixR, a, t0, 0.9)
    add(mixL, mixR, b, t0 + 0.24, 0.9)

# ————————————————————— score —————————————————————
NOTE = {'A1': 55.0, 'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.0, 'A2': 110.0,
        'B2': 123.47, 'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.0, 'A3': 220.0,
        'B3': 246.94, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0,
        'B4': 493.88, 'C5': 523.25, 'E5': 659.26, 'A5': 880.0}

sec = tl['sections']
def S(x): return sec[x][0]
def E(x): return sec[x][1]

silences = tl.get('silences', [])
def in_silence(t):
    return any(a - 0.05 <= t < b for a, b in silences)

# --- S1: dark dawn — drone + waves + heartbeat ---
n1 = int((E('S1') - S('S1') + 0.5) * SR)
w = waves_bed(n1) * 0.16
add(mixL, mixR, w, S('S1'), 1.0, -0.15)
d1 = drone([NOTE['A1'], NOTE['E2'], NOTE['A2']], n1) * 0.5
add(mixL, mixR, d1, S('S1'), 0.55, 0.0)
tt = S('S1') + 2.4
while tt < S('S1') + 24:
    heart(tt); tt += 1.818
# marimba sparse on title (from sc01d ~27.9)
for i, (t0, f) in enumerate([(28.6, 'A3'), (30.0, 'C4'), (31.4, 'E4'), (34.2, 'A3'), (38.4, 'E4'), (41.2, 'D4'), (44.0, 'C4')]):
    if not in_silence(t0):
        add(mixL, mixR, pluck(NOTE[f], 1.6), t0, 0.34, (i % 3 - 1) * 0.4)
# S2: pizz procedural 88bpm
bpm = 88; beat = 60 / bpm
t = S('S2')
i = 0
while t < E('S2'):
    if not in_silence(t):
        bar = i % 8
        if bar in (0, 3, 6): add(mixL, mixR, pluck(NOTE['A2'], 0.5, 0.2), t, 0.4, -0.2)
        if bar in (2, 5): add(mixL, mixR, pluck(NOTE['E2'], 0.5, 0.2), t, 0.36, 0.2)
        if bar == 7: add(mixL, mixR, pluck(NOTE['G2'], 0.5, 0.2), t, 0.34, 0.1)
        if bar in (1, 4, 7): add(mixL, mixR, snap(), t, 0.16, (i % 2) * 0.5 - 0.25)
    t += beat / 2; i += 1
# S3: cipher motif enters (5 notes = 5 code lines)
motif = ['A3', 'C4', 'B3', 'E4', 'A4']
t = S('S3') + 0.4
k = 0
while t < E('S3') - 1:
    if not in_silence(t):
        add(mixL, mixR, pluck(NOTE[motif[k % 5]], 1.1), t, 0.3, (k % 2) * 0.5 - 0.25)
        if k % 5 == 4: add(mixL, mixR, pluck(NOTE['A2'], 0.7, 0.15), t + 0.02, 0.3, 0)
    t += beat * 1.5; k += 1
# S4: music-box + pad, 84bpm sparse
t = S('S4')
i = 0
n4 = int((E('S4') - S('S4')) * SR)
d4 = drone([NOTE['D2'], NOTE['A2'], NOTE['D3'], NOTE['F3']], n4) * 0.4
add(mixL, mixR, d4, S('S4'), 0.5)
bellsq = ['D4', 'A4', 'F4', 'D4', 'C5', 'A4', 'F4', 'E4']
while t < E('S4'):
    if not in_silence(t):
        f = bellsq[i % 8]
        add(mixL, mixR, bell(NOTE[f], 2.2), t, 0.16, (i % 2) * 0.6 - 0.3)
    t += 60 / 84 * 2; i += 1
# S5: suitcase — bass pulse + hats 100
bpm = 100; beat = 60 / bpm
t = S('S5'); i = 0
while t < E('S5'):
    if not in_silence(t):
        if i % 2 == 0: add(mixL, mixR, pluck(NOTE['A2'] if (i // 4) % 2 == 0 else NOTE['F2'], 0.4, 0.12), t, 0.42, 0)
        if i % 4 == 2: add(mixL, mixR, hat(), t, 0.5, (i % 3 - 1) * 0.4)
        if i % 8 == 6: add(mixL, mixR, snap(), t, 0.2, 0.2)
    t += beat / 2; i += 1
# S6: theories — minor pad + pizz; dark beat = bass + snaps
n6 = int((E('S6') - S('S6')) * SR)
p6 = pad_chord([NOTE['A2'], NOTE['C3'], NOTE['E3'], NOTE['G3']], n6, a=2.0) * 0.42
add(mixL, mixR, p6, S('S6'), 0.8)
t = S('S6') + (E('S7') and 0); i = 0
esp_start = tl['scenes'][63]['t0'] if len(tl['scenes']) > 63 else S('S6') + 8  # sc06b approx
while t < E('S6'):
    if not in_silence(t):
        dark = esp_start - 1 < t < esp_start + 16
        if dark:
            if i % 4 == 0: add(mixL, mixR, pluck(NOTE['A2'], 0.42, 0.1), t, 0.5, 0)
            if i % 4 == 2: add(mixL, mixR, snap(), t, 0.24, 0.15)
        else:
            if i % 4 == 0: add(mixL, mixR, pluck(NOTE['A2'], 0.5, 0.16), t, 0.34, -0.2)
            if i % 4 == 3: add(mixL, mixR, pluck(NOTE['E3'], 0.5, 0.16), t, 0.3, 0.2)
    t += beat; i += 1
# S7: DNA — rising arpeggio, crescendo to the name, then sparse
bpm = 108; beat = 60 / bpm
arp = ['A2', 'E3', 'A3', 'C4', 'E4', 'A4', 'C5', 'E5']
t = S('S7'); i = 0
name_t = lt = tl['lines'].get('L60', S('S7') + 100)
while t < E('S7'):
    if not in_silence(t):
        rise = min(1.0, (t - S('S7')) / 45)
        g = 0.16 + 0.3 * rise
        if t < name_t - 2.5:
            add(mixL, mixR, pluck(NOTE[arp[i % 8]], 0.7, 0.3), t, g, (i % 2) * 0.6 - 0.3)
            if i % 8 == 0: add(mixL, mixR, pluck(NOTE['A2'], 0.5, 0.1), t, 0.3)
        elif t < name_t + 14:
            pass  # held silence around the name — single bells come from EV
        else:
            if i % 8 in (0, 3): add(mixL, mixR, bell(NOTE[arp[(i // 8) % 8]], 2.4), t, 0.12, (i % 2) * 0.5 - 0.25)
    t += beat / 2; i += 1
# S8: ledger — near-static pad + ticks
n8 = int((E('S8') - S('S8')) * SR)
p8 = pad_chord([NOTE['A2'], NOTE['E3'], NOTE['A3']], n8, a=2.5) * 0.34
add(mixL, mixR, p8, S('S8'), 0.8)
# S9: resolution — motif on music-box, resolved
res = ['A3', 'C4', 'E4', 'A4', 'B4', 'C5', 'E5']
t = S('S9') + 0.5
for k, f in enumerate(res):
    add(mixL, mixR, bell(NOTE[f], 3.4), t + k * 0.62, 0.2, (k % 2) * 0.5 - 0.25)
# final room-tone tail
n9 = int(3.0 * SR)
add(mixL, mixR, room_bed(n9) * 0.25, DUR - 2.5)

# ————————————————————— foley from EV —————————————————————
for e in ev:
    ty, t0 = e.get('type'), float(e.get('t', 0))
    if ty == 'stamp':
        big = 'UNBROKEN' in json.dumps(e) or False
        add(mixL, mixR, stamp_sfx(big=bool(e.get('big'))), t0, 0.85, e.get('pan', 0.15))
    elif ty == 'shutter': add(mixL, mixR, shutter_sfx(), t0, 0.8, 0.1)
    elif ty == 'whoosh': add(mixL, mixR, whoosh_sfx(), t0 - 0.18, 0.5)
    elif ty == 'paper': add(mixL, mixR, paper_sfx(), t0, 0.55, e.get('pan', -0.1))
    elif ty == 'click': add(mixL, mixR, click_sfx(), t0, 0.6, e.get('pan', 0.2))
    elif ty == 'type': add(mixL, mixR, type_sfx(), t0, 0.5, e.get('pan', -0.2))
    elif ty == 'bell': add(mixL, mixR, bell_hit(e.get('f', 2093)), t0, 0.5)
    elif ty == 'drawer': add(mixL, mixR, drawer_sfx(), t0, 0.7, 0.1)

# ————————————————————— ambience beds per section —————————————————————
for a, b, kind, g, pan in [
    (S('S2') - 1, S('S2') + 26, 'room', 0.10, 0),
    (S('S4') + 11, S('S4') + 26, 'uv', 0.12, 0.2),
    (S('S6'), E('S6'), 'rain', 0.10, -0.2),
    (S('S8'), E('S8'), 'room', 0.08, 0),
]:
    n = int((b - a) * SR)
    bed = {'room': room_bed, 'rain': rain_bed, 'uv': lambda k: bandpass(noise(k), 8000, 13000) * 0.4 * (0.6 + 0.4 * np.sin(2 * np.pi * np.arange(k) / SR * 0.7))}[kind]
    add(mixL, mixR, bed(n), a, g, pan)

# ————————————————————— voice —————————————————————
dur = json.load(open('voices/dur.json'))
lines_meta = {l['id']: l for l in json.load(open('lines.json'))}
voice_gain = 1.9
for lid, t0 in sorted(tl['lines'].items(), key=lambda kv: kv[1]):
    f = f'voices/{lid}.wav'
    if not os.path.exists(f): continue
    v, sr = sf.read(f, dtype='float32')
    if v.ndim > 1: v = v.mean(axis=1)
    if sr != SR:
        import soxr
        v = soxr.resample(v, sr, SR)
    # compress: soft-knee via tanh on normalized
    peak = np.max(np.abs(v)) or 1.0
    v = np.tanh(v / peak * 1.6) * 0.72
    add(mixL, mixR, v, t0, voice_gain, 0.0)

# ————————————————————— ducking + silences —————————————————————
# voice duck envelope for music: build music-only track? simpler: global duck under voice windows
t_voice = np.zeros(N, dtype=np.float32)
for lid, t0 in tl['lines'].items():
    i0 = int(t0 * SR); i1 = min(N, i0 + int(dur[lid] * SR * 1.05))
    if i1 > i0: t_voice[i0:i1] = 1.0
# smooth duck
k = int(0.25 * SR)
kernel = np.hanning(k * 2 + 1); kernel /= kernel.sum()
duck = np.convolve(t_voice, kernel, mode='same')
music_gain = 1.0 - 0.52 * duck
# silence windows: hard duck music+foley
sil = np.ones(N, dtype=np.float32)
for a, b in silences:
    i0, i1 = int(a * SR), int(b * SR)
    i0, i1 = max(0, i0), min(N, i1)
    if i1 > i0: sil[i0:i1] = 0.0
sil = np.convolve(sil, np.hanning(int(0.3 * SR)) / int(0.3 * SR) * 1.0, mode='same')
sil = np.clip(sil, 0, 1)

# rebuild: we applied music+foley into mixL/R; voice needs no silencing.
# Separate: re-generate voice track alone
vL = np.zeros(N, dtype=np.float64)
for lid, t0 in sorted(tl['lines'].items(), key=lambda kv: kv[1]):
    f = f'voices/{lid}.wav'
    if not os.path.exists(f): continue
    v, sr = sf.read(f, dtype='float32')
    if v.ndim > 1: v = v.mean(axis=1)
    if sr != SR:
        import soxr
        v = soxr.resample(v, sr, SR)
    peak = np.max(np.abs(v)) or 1.0
    v = np.tanh(v / peak * 1.6) * 0.72
    i = int(t0 * SR); seg = v[:N - i]
    vL[i:i + len(seg)] += seg

mixL *= music_gain * sil
mixR *= music_gain * sil
mixL += vL; mixR += vL

# ————————————————————— master —————————————————————
def softclip(x):
    return np.tanh(x * 1.05) * 0.92
peak = max(np.max(np.abs(mixL)), np.max(np.abs(mixR)))
if peak > 0.99:
    mixL *= 0.99 / peak; mixR *= 0.99 / peak
mixL = softclip(mixL); mixR = softclip(mixR)
# fades
nf = int(1.2 * SR)
fade = np.ones(N); fade[:int(0.6 * SR)] = np.linspace(0, 1, int(0.6 * SR))
fade[-nf:] = np.linspace(1, 0, nf)
mixL *= fade; mixR *= fade
os.makedirs('out', exist_ok=True)
st = np.stack([mixL, mixR], axis=1).astype(np.float32)
sf.write('out/mix.wav', st, SR, subtype='PCM_16')
rms = 20 * np.log10(max(1e-9, np.sqrt(np.mean(st ** 2))))
print(f'mix.wav written: {DUR:.1f}s, RMS {rms:.1f} dBFS, peak {20 * np.log10(np.max(np.abs(st))):.1f} dBFS')
