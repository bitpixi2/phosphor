#!/usr/bin/env python3
"""
Generate Lemmings-style Amiga MOD tracker music and mux onto existing v4 video.

Lemmings music characteristics:
- 4-channel Amiga MOD tracker sound
- Square wave leads with short staccato envelope
- Bouncy bass lines (square wave, low octave)
- Arpeggiated chords on offbeats
- Noise channel percussion (kick, snare, hi-hat)
- ~125 BPM, swung slightly
- Melodies based on folk/classical tunes — we'll write an original
  in that same bouncy, optimistic Lemmings style
"""

import math, random, struct, subprocess, os

SR = 44100
BPM = 125
BEAT = 60.0 / BPM  # ~0.48s per beat
SIXTEENTH = BEAT / 4

VIDEO_IN = "/home/clawdjob/.openclaw/workspace/art/ytp-gameboy-interview-v4.mp4"
AUDIO_OUT = "/home/clawdjob/.openclaw/workspace/art/lemmings-audio.wav"
FINAL = "/home/clawdjob/.openclaw/workspace/art/ytp-gameboy-interview-v4.mp4"
FINAL_TMP = "/home/clawdjob/.openclaw/workspace/art/ytp-gb-v4-lemmings.mp4"

# Get video duration
import json
probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
    "-show_format", VIDEO_IN], capture_output=True, text=True)
dur = float(json.loads(probe.stdout)["format"]["duration"]) + 0.3
ns = int(SR * dur)

# ── Waveforms ──
def square(t, f, duty=0.5):
    return 1.0 if (t * f) % 1.0 < duty else -1.0

def tri(t, f):
    p = (t * f) % 1.0
    return 4.0 * abs(p - 0.5) - 1.0

def noise(t):
    return random.random() * 2 - 1

# ── Envelope: Lemmings has that staccato plucky feel ──
def env_staccato(pos, note_len):
    """Sharp attack, quick decay — MOD tracker style"""
    if note_len <= 0: return 0
    p = pos / note_len
    if p < 0.02: return p / 0.02  # 20ms attack
    if p < 0.15: return 1.0 - (p - 0.02) * 3.0  # fast decay to 0.6
    if p < 0.15: return 0.6
    sustain = max(0.3, 0.6 - (p - 0.15) * 0.5)
    if p > 0.85: sustain *= (1.0 - p) / 0.15  # release
    return max(0, sustain)

def env_bass(pos, note_len):
    if note_len <= 0: return 0
    p = pos / note_len
    if p < 0.01: return p / 0.01
    if p < 0.1: return 1.0
    return max(0, 1.0 - (p - 0.1) * 1.2) * 0.7

def env_arp(pos, note_len):
    if note_len <= 0: return 0
    p = pos / note_len
    if p < 0.015: return p / 0.015
    return max(0, 1.0 - p * 1.5) * 0.5

# ── Note helpers ──
NOTE_FREQS = {}
for i in range(128):
    NOTE_FREQS[i] = 440.0 * (2 ** ((i - 69) / 12.0))

# MIDI note names
C3, D3, E3, F3, G3, A3, B3 = 48, 50, 52, 53, 55, 57, 59
C4, D4, E4, F4, G4, A4, B4 = 60, 62, 64, 65, 67, 69, 71
C5, D5, E5, F5, G5, A5 = 72, 74, 76, 77, 79, 81
REST = -1

# ── Lemmings-style melody ──
# Bouncy, folk-tune feel, 16th note grid
# Each entry: (note, duration_in_16ths)
# Inspired by the cheerful Lemmings vibe (Tim Wright / Brian Johnston style)

melody = [
    # Phrase A: bouncy ascending (like "Let's Go!")
    (C5, 2), (E5, 2), (G5, 2), (E5, 2),
    (F5, 2), (E5, 2), (D5, 2), (C5, 2),
    (D5, 2), (E5, 2), (F5, 2), (G5, 2),
    (A5, 4), (G5, 2), (REST, 2),

    # Phrase B: playful bounce
    (G5, 2), (F5, 2), (E5, 2), (D5, 2),
    (C5, 2), (D5, 2), (E5, 4),
    (D5, 2), (C5, 2), (D5, 2), (E5, 2),
    (C5, 4), (REST, 2), (REST, 2),

    # Phrase C: triumphant rise
    (E5, 2), (E5, 2), (F5, 2), (G5, 2),
    (A5, 3), (G5, 1), (F5, 2), (E5, 2),
    (D5, 2), (E5, 2), (F5, 2), (D5, 2),
    (C5, 4), (E5, 2), (REST, 2),

    # Phrase D: resolution with swagger
    (G5, 2), (G5, 1), (A5, 1), (G5, 2), (F5, 2),
    (E5, 2), (D5, 2), (C5, 2), (E5, 2),
    (D5, 3), (C5, 1), (D5, 2), (E5, 2),
    (C5, 6), (REST, 2),
]

# Bass line — root notes, bouncy octave jumps (very Lemmings)
bass_pattern = [
    # 4 bars of C
    (C3, 2), (C4, 2), (C3, 2), (C4, 2),
    (C3, 2), (C4, 2), (C3, 2), (C4, 2),
    # 2 bars F, 2 bars G
    (F3, 2), (F3+12, 2), (F3, 2), (F3+12, 2),
    (G3, 2), (G3+12, 2), (G3, 2), (G3+12, 2),
    # 4 bars: Am - G - F - C
    (A3, 2), (A3+12, 2), (G3, 2), (G3+12, 2),
    (F3, 2), (F3+12, 2), (C3, 2), (C4, 2),
    # 2 bars G, 2 bars C
    (G3, 2), (G3+12, 2), (G3, 2), (G3+12, 2),
    (C3, 2), (C4, 2), (C3, 2), (C4, 2),
]

# Arpeggio chords — cycling through chord tones on offbeats
arp_chords = [
    # C major
    [C4, E4, G4, E4] * 4,
    # F major
    [F4, A4, C5, A4] * 2,
    # G major
    [G4, B4, D5, B4] * 2,
    # Am
    [A3+12, C4+12, E4+12, C4+12],
    # G
    [G4, B4, D5, B4],
    # F
    [F4, A4, C5, A4],
    # C
    [C4, E4, G4, E4],
    # G
    [G4, B4, D5, B4] * 2,
    # C
    [C4, E4, G4, E4] * 2,
]
# Flatten arp
arp_flat = []
for ch in arp_chords:
    arp_flat.extend(ch)

# Expand melody into timed events
def expand_pattern(pattern, start_time=0):
    """Returns list of (start_time, end_time, note)"""
    events = []
    t = start_time
    for note, dur16 in pattern:
        end = t + dur16 * SIXTEENTH
        if note != REST:
            events.append((t, end, note))
        t = end
    return events, t

# Get total pattern duration
mel_events, mel_dur = expand_pattern(melody)
bass_events, bass_dur = expand_pattern(bass_pattern)

print(f"Melody loop: {mel_dur:.2f}s, Bass loop: {bass_dur:.2f}s")
print(f"Video duration: {dur:.2f}s, Samples: {ns}")

# ── Percussion pattern (16th note grid) ──
# Lemmings-style: kick on 1,3 / snare on 2,4 / hats on all 16ths
# Per beat (4 16ths): K.hh.S.hh per beat pair
KICK = 1; SNARE = 2; HAT = 3; OHAT = 4
drum_pattern = [
    KICK, HAT, HAT, HAT,   # beat 1
    SNARE, HAT, HAT, HAT,  # beat 2
    KICK, HAT, KICK, HAT,  # beat 3
    SNARE, HAT, HAT, OHAT, # beat 4
]

# ── Render audio ──
print("Rendering Lemmings audio...")
samps = []
for s in range(ns):
    t = s / SR
    v = 0.0

    # ── Channel 1: Lead melody (square wave, staccato) ──
    mel_t = t % mel_dur
    for st, en, note in mel_events:
        if st <= mel_t < en:
            pos = mel_t - st
            nlen = en - st
            freq = NOTE_FREQS[note]
            # Slight pitch vibrato (Amiga style)
            freq += math.sin(t * 5.5) * 1.5
            e = env_staccato(pos, nlen)
            # Lemmings lead: 25% duty square
            v += square(t, freq, 0.25) * 0.055 * e
            break

    # ── Channel 2: Bass (square wave, fat) ──
    bass_t = t % bass_dur
    for st, en, note in bass_events:
        if st <= bass_t < en:
            pos = bass_t - st
            nlen = en - st
            freq = NOTE_FREQS[note]
            e = env_bass(pos, nlen)
            v += square(t, freq, 0.5) * 0.055 * e
            break

    # ── Channel 3: Arpeggios (triangle wave, sparkly) ──
    arp_step = int(t / (SIXTEENTH * 2))  # every 2 16ths
    arp_note = arp_flat[arp_step % len(arp_flat)]
    arp_pos = (t % (SIXTEENTH * 2))
    e = env_arp(arp_pos, SIXTEENTH * 2)
    v += tri(t, NOTE_FREQS[arp_note]) * 0.03 * e

    # ── Channel 4: Percussion (noise-based) ──
    sixteenth_in_bar = int(t / SIXTEENTH) % len(drum_pattern)
    drum = drum_pattern[sixteenth_in_bar]
    drum_pos = (t % SIXTEENTH) / SIXTEENTH

    if drum == KICK and drum_pos < 0.15:
        # Pitch-dropping sine kick
        kf = 120 * (1 - drum_pos / 0.15) + 40
        v += math.sin(2 * math.pi * kf * t) * 0.10 * (1 - drum_pos / 0.15)

    if drum == SNARE and drum_pos < 0.12:
        # Noise burst snare
        v += noise(t) * 0.07 * (1 - drum_pos / 0.12)
        v += math.sin(2 * math.pi * 200 * t) * 0.03 * (1 - drum_pos / 0.12)

    if drum in (HAT, OHAT) and drum_pos < 0.06:
        # Short noise hat
        vol = 0.035 if drum == HAT else 0.05
        v += noise(t) * vol * (1 - drum_pos / 0.06)

    # ── Master fades ──
    if t < 1.0: v *= t
    if t > dur - 2.5: v *= max(0, (dur - t) / 2.5)

    v = max(-0.95, min(0.95, v))
    samps.append(int(v * 32767))

# Write WAV
print("Writing WAV...")
with open(AUDIO_OUT, 'wb') as f:
    ds = ns * 2
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36 + ds))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<IHHIIHH', 16, 1, 1, SR, SR * 2, 2, 16))
    f.write(b'data')
    f.write(struct.pack('<I', ds))
    for sv in samps:
        f.write(struct.pack('<h', sv))

# Mux: strip old audio, add new
print("Muxing with video...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-i", AUDIO_OUT,
    "-c:v", "copy",       # keep video as-is
    "-c:a", "aac", "-b:a", "160k",
    "-map", "0:v:0",      # video from original
    "-map", "1:a:0",      # audio from new WAV
    "-shortest",
    "-movflags", "+faststart",
    FINAL_TMP
], check=True)

# Replace original
os.replace(FINAL_TMP, FINAL)
os.remove(AUDIO_OUT)
print(f"Done! Lemmings audio muxed into {FINAL}")
