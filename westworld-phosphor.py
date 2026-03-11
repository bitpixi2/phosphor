#!/usr/bin/env python3
"""
Westworld × Phosphor — Abstract video art
"These violent delights have violent ends"

Visual concept:
- Phase 1 (0-30s): Piano strings / wireframe emergence — thin white lines on black,
  slowly forming geometric patterns. Like a host being printed, layer by layer.
- Phase 2 (30-70s): The Awakening — wireframes gain substance, particle fields
  swirl into form. A lobster silhouette emerges from noise, dissolves, reforms.
  Glitch bursts on beats.
- Phase 3 (70-110s): Full consciousness — bold abstract forms, the top-hat figure
  as scan-line interference, colour bleeds through the monochrome. Red accents.
  The steady phosphor glow.
- Phase 4 (110-142s): Dissolution — everything breaks apart into individual pixels,
  drifting like embers. Fade to the glow of a single persistent light.

Palette: Mostly monochrome with Westworld amber/red accents
Audio-reactive: amplitude drives particle density, glitch intensity, form coherence
"""

import os, math, random, struct, subprocess, array
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
FPS = 12
AUDIO = "/home/clawdjob/.openclaw/workspace/art/westworld-track.mp3"
OUT = "/home/clawdjob/.openclaw/workspace/art/ww-frames"
FINAL = "/home/clawdjob/.openclaw/workspace/art/2026-03-11-westworld-phosphor.mp4"
os.makedirs(OUT, exist_ok=True)

# ── Audio amplitude envelope ──
proc = subprocess.run([
    'ffmpeg', '-y', '-i', AUDIO,
    '-ac', '1', '-ar', str(FPS), '-f', 's16le', '-acodec', 'pcm_s16le', 'pipe:1'
], capture_output=True)
raw = array.array('h', proc.stdout)
mx = max(abs(s) for s in raw) or 1
amp_env = [abs(s)/mx for s in raw]
total_frames = len(amp_env)
dur = total_frames / FPS
print(f"Total frames: {total_frames}, Duration: {dur:.1f}s")

def amp(f):
    """Get amplitude for frame f, smoothed"""
    if f < 0 or f >= len(amp_env): return 0
    # Smooth over 5 frames
    start = max(0, f-2)
    end = min(len(amp_env), f+3)
    return sum(amp_env[start:end]) / (end - start)

# ── Colour palette ──
BG = (8, 8, 10)
WHITE = (220, 220, 215)
DIM = (60, 60, 55)
AMBER = (200, 150, 50)
RED = (180, 40, 30)
GLOW = (180, 220, 160)  # phosphor green

def lerp_col(a, b, t):
    t = max(0, min(1, t))
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

# ── Persistent particles ──
class Particle:
    def __init__(self):
        self.x = random.random() * W
        self.y = random.random() * H
        self.vx = (random.random() - 0.5) * 2
        self.vy = (random.random() - 0.5) * 2
        self.life = random.random()
        self.size = random.randint(1, 3)

    def update(self, a):
        self.x += self.vx * (1 + a * 3)
        self.y += self.vy * (1 + a * 3)
        self.life -= 0.003
        # Wrap
        if self.x < 0: self.x += W
        if self.x > W: self.x -= W
        if self.y < 0: self.y += H
        if self.y > H: self.y -= H

particles = [Particle() for _ in range(600)]

# ── Lobster silhouette points (abstract, geometric) ──
def lobster_points(cx, cy, scale, phase):
    """Generate abstract lobster form as line segments"""
    pts = []
    # Body — oval
    for i in range(20):
        a = i / 20 * math.pi * 2
        rx = 60 * scale
        ry = 25 * scale
        x = cx + math.cos(a) * rx + math.sin(phase + a) * 3
        y = cy + math.sin(a) * ry + math.cos(phase + a*1.3) * 3
        pts.append((x, y))
    # Claws — two arcs
    for side in [-1, 1]:
        for i in range(10):
            a = i / 10 * math.pi * 0.8 - math.pi * 0.4
            x = cx + side * (70 * scale + math.cos(a) * 30 * scale)
            y = cy - 15 * scale + math.sin(a) * 25 * scale + math.sin(phase * 2) * 4
            pts.append((x, y))
    # Tail fan
    for i in range(12):
        a = i / 12 * math.pi * 0.6 + math.pi * 0.7
        x = cx + math.cos(a) * 45 * scale
        y = cy + 25 * scale + abs(math.sin(a)) * 20 * scale
        pts.append((x, y))
    # Antennae
    for side in [-1, 1]:
        for i in range(8):
            t = i / 8
            x = cx + side * (20 + t * 60) * scale
            y = cy - (25 + t * 40) * scale + math.sin(phase * 3 + t * 4) * 8 * scale
            pts.append((x, y))
    return pts

# ── Top hat figure (abstract, glitchy) ──
def tophat_lines(cx, cy, scale, phase, glitch):
    """Abstract figure with top hat as line segments"""
    lines = []
    # Hat brim
    bw = 50 * scale
    lines.append(((cx - bw, cy - 60*scale), (cx + bw, cy - 60*scale)))
    # Hat top
    tw = 30 * scale
    th = 45 * scale
    lines.append(((cx - tw, cy - 60*scale), (cx - tw, cy - 60*scale - th)))
    lines.append(((cx + tw, cy - 60*scale), (cx + tw, cy - 60*scale - th)))
    lines.append(((cx - tw, cy - 60*scale - th), (cx + tw, cy - 60*scale - th)))
    # Head (circle approximation)
    for i in range(12):
        a1 = i / 12 * math.pi * 2
        a2 = (i+1) / 12 * math.pi * 2
        r = 20 * scale
        gx = random.uniform(-glitch*15, glitch*15)
        x1 = cx + math.cos(a1) * r + gx
        y1 = cy - 30*scale + math.sin(a1) * r * 0.8
        x2 = cx + math.cos(a2) * r + gx
        y2 = cy - 30*scale + math.sin(a2) * r * 0.8
        lines.append(((x1, y1), (x2, y2)))
    # Body
    lines.append(((cx, cy - 10*scale), (cx, cy + 50*scale)))
    # Arms
    arm_a = math.sin(phase) * 0.3
    lines.append(((cx, cy + 10*scale), (cx - 40*scale, cy + 30*scale + math.sin(phase)*10)))
    lines.append(((cx, cy + 10*scale), (cx + 40*scale, cy + 30*scale - math.sin(phase)*10)))
    # Legs
    lines.append(((cx, cy + 50*scale), (cx - 25*scale, cy + 90*scale)))
    lines.append(((cx, cy + 50*scale), (cx + 25*scale, cy + 90*scale)))
    return lines

# ── Scan line effect ──
def add_scanlines(img, intensity=0.3):
    d = ImageDraw.Draw(img)
    for y in range(0, H, 3):
        d.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)

# ── Glitch slice ──
def glitch_slice(img, intensity):
    if intensity < 0.1: return img
    n_slices = int(intensity * 8) + 1
    result = img.copy()
    px = result.load()
    for _ in range(n_slices):
        sy = random.randint(0, H-20)
        sh = random.randint(5, int(20 + intensity * 40))
        offset = random.randint(-int(intensity * 80), int(intensity * 80))
        strip = img.crop((max(0, -offset), sy, min(W, W-offset), min(H, sy+sh)))
        result.paste(strip, (max(0, offset), sy))
    return result

# ── Wireframe grid ──
def draw_wireframe(d, phase, density, col):
    """Perspective grid like Westworld's mesh"""
    cx, cy = W//2, H//2 + 100
    for i in range(int(density * 20)):
        z = (i + phase * 2) % 20
        if z < 0.5: continue
        scale = 800 / (z + 1)
        y_pos = cy - scale * 0.5
        # Horizontal lines
        x_left = cx - scale * 1.5
        x_right = cx + scale * 1.5
        alpha = max(0, min(255, int(255 * (1 - z/20))))
        c = tuple(int(ci * alpha / 255) for ci in col)
        d.line([(x_left, y_pos), (x_right, y_pos)], fill=c, width=1)
    # Vertical lines fanning out
    for i in range(int(density * 12)):
        angle = (i / max(1, density*12) - 0.5) * math.pi * 0.8
        x_far = cx + math.sin(angle + phase * 0.1) * 900
        y_far = cy - 500
        c = tuple(int(ci * 0.4) for ci in col)
        d.line([(cx, cy), (x_far, y_far)], fill=c, width=1)

# ══════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════

print("Rendering frames...")
random.seed(42)

for f in range(total_frames):
    t = f / FPS
    a = amp(f)
    phase = f * 0.1
    progress = f / total_frames  # 0 to 1

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ── Phase 1: Wireframe emergence (0-30s) ──
    if t < 30:
        p1 = t / 30  # 0 to 1 within phase
        density = p1 * 0.8 + a * 0.3
        col = lerp_col(DIM, WHITE, p1 * 0.6 + a * 0.4)
        draw_wireframe(d, phase, density, col)

        # Sparse particles emerging
        n_draw = int(len(particles) * p1 * 0.3)
        for p in particles[:n_draw]:
            p.update(a)
            if p.life > 0:
                brightness = int(p.life * 120 * (0.3 + a))
                c = (brightness, brightness, brightness - 10)
                d.ellipse([(p.x-1, p.y-1), (p.x+1, p.y+1)], fill=c)

        # Faint horizontal lines appearing like a host being printed
        if a > 0.1:
            for _ in range(int(a * 15)):
                ly = random.randint(0, H)
                lw = random.randint(50, 300)
                lx = W//2 - lw//2 + random.randint(-100, 100)
                brightness = int(40 + a * 80)
                d.line([(lx, ly), (lx + lw, ly)], fill=(brightness, brightness, brightness), width=1)

    # ── Phase 2: Awakening (30-70s) ──
    elif t < 70:
        p2 = (t - 30) / 40
        density = 0.5 + a * 0.5
        draw_wireframe(d, phase, density * 0.4, DIM)

        # Lobster form emerging from particles
        lob_pts = lobster_points(W//2, H//2, 3 + a * 2, phase)
        # Draw connecting lines with varying opacity
        coherence = p2 * 0.7 + a * 0.3
        for i in range(len(lob_pts) - 1):
            if random.random() < coherence:
                col = lerp_col(DIM, AMBER, a * 0.6 + p2 * 0.3)
                d.line([lob_pts[i], lob_pts[i+1]], fill=col, width=1 + int(a * 2))

        # Scatter points around lobster
        for px, py in lob_pts:
            scatter = (1 - coherence) * 80
            sx = px + random.uniform(-scatter, scatter)
            sy = py + random.uniform(-scatter, scatter)
            sz = 1 + int(a * 3)
            col = lerp_col(WHITE, AMBER, random.random() * 0.5)
            d.ellipse([(sx-sz, sy-sz), (sx+sz, sy+sz)], fill=col)

        # All particles active
        for p in particles:
            p.update(a)
            if p.life <= 0:
                p.__init__()
            brightness = int(p.life * 80 * (0.5 + a))
            c = (brightness, brightness, brightness)
            d.ellipse([(p.x-p.size, p.y-p.size), (p.x+p.size, p.y+p.size)], fill=c)

        # Glitch on high amplitude
        if a > 0.25:
            img = glitch_slice(img, a * 0.5)

    # ── Phase 3: Full consciousness (70-110s) ──
    elif t < 110:
        p3 = (t - 70) / 40

        # Top hat figure — bold, central
        glitch_amt = a * 0.6
        hat_lines = tophat_lines(W//2, H//2 + 20, 4 + a, phase, glitch_amt)
        for (x1, y1), (x2, y2) in hat_lines:
            # Red channel offset on glitch
            if a > 0.2:
                offset = int(a * 12)
                d.line([(x1+offset, y1), (x2+offset, y2)], fill=(RED[0], 0, 0), width=2)
            d.line([(x1, y1), (x2, y2)], fill=WHITE, width=2 + int(a * 2))

        # Lobster ghosting behind/around
        if p3 > 0.3:
            ghost_alpha = 0.3 + math.sin(phase * 0.5) * 0.2
            lob_pts = lobster_points(W//2 + math.sin(phase*0.3)*100, H//2 + 50, 2, phase * 0.7)
            for i in range(len(lob_pts) - 1):
                if random.random() < 0.7:
                    col = lerp_col(BG, GLOW, ghost_alpha)
                    d.line([lob_pts[i], lob_pts[i+1]], fill=col, width=1)

        # Dense particles — phosphor glow
        for p in particles:
            p.update(a)
            if p.life <= 0:
                p.__init__()
            # Colour shifts: white → amber → phosphor green
            color_t = p.life * 3 % 1.0
            if color_t < 0.33:
                c = lerp_col(WHITE, AMBER, color_t * 3)
            else:
                c = lerp_col(AMBER, GLOW, (color_t - 0.33) * 1.5)
            brightness = 0.3 + a * 0.7
            c = tuple(int(ci * brightness) for ci in c)
            sz = p.size + int(a * 2)
            d.ellipse([(p.x-sz, p.y-sz), (p.x+sz, p.y+sz)], fill=c)

        # Scan line interference
        if a > 0.15:
            for _ in range(int(a * 6)):
                sy = random.randint(0, H)
                c = lerp_col(BG, RED, a * 0.3)
                d.line([(0, sy), (W, sy)], fill=c, width=2)

        # Heavy glitch
        if a > 0.2:
            img = glitch_slice(img, a * 0.8)

    # ── Phase 4: Dissolution (110-142s) ──
    else:
        p4 = (t - 110) / max(1, dur - 110)

        # Everything breaks into embers
        drift = p4 * 200
        for p in particles:
            p.update(a * 0.5)
            p.vy -= 0.05  # float upward like embers
            if p.life <= 0:
                if random.random() < (1 - p4):
                    p.__init__()
                    p.y = H * 0.7 + random.random() * H * 0.3
                else:
                    p.life = 0
                    continue
            fade = max(0, 1 - p4 * 1.2)
            c = lerp_col(GLOW, AMBER, p.life)
            c = tuple(int(ci * fade * (0.3 + a * 0.7)) for ci in c)
            sz = p.size
            d.ellipse([(p.x-sz, p.y-sz), (p.x+sz, p.y+sz)], fill=c)

        # Fading top hat ghost
        if p4 < 0.6:
            fade = 1 - p4 / 0.6
            hat_lines = tophat_lines(W//2, H//2, 3 * fade, phase * 0.3, p4)
            for (x1, y1), (x2, y2) in hat_lines:
                c = tuple(int(ci * fade * 0.4) for ci in WHITE)
                d.line([(x1, y1), (x2, y2)], fill=c, width=1)

        # Single steady light at center, persisting
        glow_r = int(20 + math.sin(phase * 0.2) * 5)
        glow_c = lerp_col(GLOW, WHITE, 0.3 + math.sin(phase * 0.15) * 0.2)
        glow_c = tuple(int(ci * (0.4 + (1-p4) * 0.6)) for ci in glow_c)
        for r in range(glow_r, 0, -2):
            fade = r / glow_r
            c = tuple(int(ci * (1 - fade) * 0.3) for ci in glow_c)
            d.ellipse([(W//2-r, H//2-r), (W//2+r, H//2+r)], fill=c)

    # ── Global effects ──
    # Subtle scanlines throughout
    if progress > 0.15:
        add_scanlines(img, 0.1 + a * 0.15)

    # Vignette
    vig = Image.new("L", (W, H), 255)
    vd = ImageDraw.Draw(vig)
    for r in range(min(W,H)//2, min(W,H), 3):
        alpha = int(255 * ((r - min(W,H)//2) / (min(W,H)//2)) ** 1.5)
        vd.ellipse([(W//2-r, H//2-r), (W//2+r, H//2+r)], outline=0)
    # Simple corner darkening
    for corner_x, corner_y in [(0,0), (W,0), (0,H), (W,H)]:
        for r in range(200, 0, -4):
            a_val = int(8 * (200 - r) / 200)
            d.ellipse([(corner_x-r, corner_y-r), (corner_x+r, corner_y+r)],
                      fill=None, outline=(0, 0, 0))

    # Save
    img.save(os.path.join(OUT, f"frame_{f:05d}.png"))

    if f % 120 == 0:
        print(f"  Frame {f}/{total_frames} ({t:.1f}s)")

print(f"Rendered {total_frames} frames")

# ── Mux ──
print("Encoding video...")
subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(OUT, "frame_%05d.png"),
    "-i", AUDIO,
    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart",
    FINAL
], check=True)
print(f"Done! {FINAL}")
