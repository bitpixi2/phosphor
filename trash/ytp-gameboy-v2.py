#!/usr/bin/env python3
"""
GameBoy Interview Adventure v2
16:9 GB screen (180x120 native), more dialogue, happier chiptune,
receptionist on floor 6, no bathrooms, colour shifts in meeting room.
"""

import os, random, math, struct, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# GameBoy palette
GB0 = (15, 56, 15)     # darkest
GB1 = (48, 98, 48)     # dark
GB2 = (139, 172, 15)   # light
GB3 = (155, 188, 15)   # lightest

# Meeting room colour shifts
MEET_GOOD    = ((40, 120, 50),  (60, 150, 70),  (150, 200, 80),  (170, 215, 90))
MEET_NERVOUS = ((120, 55, 40),  (140, 72, 48),  (190, 140, 80),  (210, 165, 95))
MEET_TECH    = ((30, 60, 100),  (50, 85, 120),  (120, 165, 180), (145, 190, 200))

GBW, GBH = 180, 120  # 16:9 ish (3:2 close enough for GB feel at 180x120)
W, H = 1920, 1080
SCALE = min(W // GBW, H // GBH)  # 9x
OX = (W - GBW * SCALE) // 2
OY = (H - GBH * SCALE) // 2

FPS = 12
OUT_DIR = "/home/clawdjob/.openclaw/workspace/art/ytp-frames-gb2"
FINAL = "/home/clawdjob/.openclaw/workspace/art/ytp-gameboy-interview-v2.mp4"
os.makedirs(OUT_DIR, exist_ok=True)

frame_num = 0

def get_font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F3 = get_font(5)
F5 = get_font(7)
F8 = get_font(8)

def gb(pal=None):
    c = (pal or (GB0, GB1, GB2, GB3))[3]
    return Image.new("RGB", (GBW, GBH), c)

def scale_up(img):
    bg = Image.new("RGB", (W, H), (8, 12, 8))
    scaled = img.resize((GBW * SCALE, GBH * SCALE), Image.NEAREST)
    bg.paste(scaled, (OX, OY))
    return bg

def save(img, count=1):
    global frame_num
    big = scale_up(img)
    for _ in range(count):
        big.save(os.path.join(OUT_DIR, f"frame_{frame_num:05d}.png"))
        frame_num += 1

def R(d, x, y, w, h, c):
    d.rectangle([(x, y), (x+w-1, y+h-1)], fill=c)

def px(d, x, y, c):
    d.point((x, y), fill=c)

def draw_player(d, x, y, facing='down', f=0, pal=None):
    p = pal or (GB0, GB1, GB2, GB3)
    R(d, x+2, y, 4, 3, p[0])
    R(d, x+1, y+3, 6, 3, p[1])
    if f % 2 == 0:
        R(d, x+1, y+6, 2, 2, p[0])
        R(d, x+5, y+6, 2, 2, p[0])
    else:
        R(d, x+2, y+6, 2, 2, p[0])
        R(d, x+4, y+6, 2, 2, p[0])
    if facing == 'down':
        px(d, x+3, y+1, p[3]); px(d, x+5, y+1, p[3])
    elif facing == 'left':
        px(d, x+2, y+1, p[3])
    elif facing == 'right':
        px(d, x+5, y+1, p[3])

def draw_npc(d, x, y, v=0, pal=None):
    p = pal or (GB0, GB1, GB2, GB3)
    R(d, x+2, y, 4, 3, p[1])
    px(d, x+3, y+1, p[3]); px(d, x+5, y+1, p[3])
    bc = p[0] if v % 2 == 0 else p[1]
    R(d, x+1, y+3, 6, 3, bc)
    R(d, x+1, y+6, 2, 2, p[1])
    R(d, x+5, y+6, 2, 2, p[1])

def dlg(d, text, cursor=True, pal=None):
    p = pal or (GB0, GB1, GB2, GB3)
    bx, by = 4, GBH - 32
    bw, bh = GBW - 8, 28
    R(d, bx, by, bw, bh, p[3])
    d.rectangle([(bx, by), (bx+bw-1, by+bh-1)], outline=p[0])
    d.rectangle([(bx+1, by+1), (bx+bw-2, by+bh-2)], outline=p[1])
    # Multi-line support
    lines = text.split('\n')
    for i, line in enumerate(lines):
        d.text((bx+6, by+5 + i*9), line, font=F3, fill=p[0])
    if cursor:
        d.polygon([(bx+bw-10, by+bh-8), (bx+bw-6, by+bh-5), (bx+bw-10, by+bh-2)], fill=p[0])

def loc(d, text, pal=None):
    p = pal or (GB0, GB1, GB2, GB3)
    R(d, 0, 0, GBW, 10, p[0])
    d.text((4, 2), text, font=F3, fill=p[3])

# ── SCENES ─────────────────────────────────────────────────────────

def collins_street(px_pos, py_pos, af):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, 25, GB2)  # sky
    for i in range(7):
        bx = i * 28 - 8; bh = 35 + (i*11) % 25
        R(d, bx, 25, 24, bh, GB1)
        for wy in range(28, 25+bh-6, 8):
            for wx in range(bx+3, bx+20, 7):
                R(d, wx, wy, 3, 3, GB3 if random.random()>0.3 else GB2)
    R(d, 0, 60, GBW, 8, GB2)   # footpath
    R(d, 0, 68, GBW, 52, GB1)  # road
    for rx in range(0, GBW, 18):
        R(d, rx + (af*2) % 18, 88, 7, 2, GB2)
    for tx in [18, 65, 125]:
        R(d, tx, 54, 2, 6, GB1); R(d, tx-3, 49, 8, 7, GB0)
    # Target building
    R(d, 80, 25, 24, 35, GB0)
    R(d, 85, 52, 14, 8, GB3)  # door
    if af % 4 < 2:
        d.polygon([(92, 20), (88, 24), (96, 24)], fill=GB3)
    draw_player(d, int(px_pos), int(py_pos), 'up' if py_pos < 62 else 'right', af)
    loc(d, "COLLINS ST, MELBOURNE")
    return img

def lobby(px_pos, py_pos, af):
    img = gb(); d = ImageDraw.Draw(img)
    for ty in range(10, GBH, 14):
        for tx in range(0, GBW, 14):
            c = GB2 if (tx//14+ty//14)%2==0 else GB3
            R(d, tx, ty, 14, 14, c)
    R(d, 0, 10, GBW, 6, GB1); R(d, 0, 10, 6, GBH, GB1); R(d, GBW-6, 10, 6, GBH, GB1)
    # Front desk
    R(d, 55, 25, 50, 10, GB0)
    R(d, 60, 22, 8, 3, GB1)  # monitor
    # Elevator
    R(d, GBW-24, 40, 18, 24, GB0)
    R(d, GBW-23, 41, 7, 22, GB1)
    R(d, GBW-15, 41, 7, 22, GB1)
    d.polygon([(GBW-15, 36), (GBW-18, 40), (GBW-12, 40)], fill=GB3)
    # Plant
    R(d, 14, 25, 5, 3, GB0); R(d, 12, 20, 9, 7, GB1)
    # Door
    R(d, 78, GBH-6, 18, 6, GB2)
    draw_player(d, int(px_pos), int(py_pos), 'right' if px_pos < GBW-30 else 'up', af)
    loc(d, "LOBBY - GROUND FLOOR")
    return img

def elevator(floor, door='closed', af=0):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 20, 10, GBW-40, GBH-10, GB1)
    R(d, 24, 14, GBW-48, GBH-18, GB2)
    R(d, 30, 24, 14, 42, GB0)
    for fi in range(8):
        c = GB3 if fi+1 == floor else GB1
        R(d, 33, 27+fi*5, 7, 3, c)
    R(d, GBW//2-8, 16, 16, 10, GB0)
    d.text((GBW//2-3, 18), str(floor), font=F5, fill=GB3)
    if door == 'closed':
        R(d, GBW//2-16, 34, 14, 70, GB0)
        R(d, GBW//2+2, 34, 14, 70, GB0)
    elif door == 'opening':
        ow = 6 + (af%5)*3
        R(d, GBW//2-ow-2, 34, 6, 70, GB0)
        R(d, GBW//2+ow-4, 34, 6, 70, GB0)
    loc(d, f"ELEVATOR - FL {floor}")
    return img

def floor6(px_pos, py_pos, af, npcs=None, receptionist=True):
    img = gb(); d = ImageDraw.Draw(img)
    for ty in range(10, GBH, 10):
        for tx in range(0, GBW, 10):
            c = GB2 if (tx//10+ty//10)%2==0 else GB3
            R(d, tx, ty, 10, 10, c)
    R(d, 0, 10, GBW, 4, GB1)
    R(d, 0, 10, 4, GBH, GB1)
    R(d, GBW-4, 10, 4, GBH, GB1)
    # Doors
    for dx in range(22, GBW-18, 32):
        R(d, dx, 14, 12, 18, GB0); R(d, dx+8, 24, 3, 3, GB2)
    # Waiting chairs
    for cx in range(55, 140, 16):
        R(d, cx, 50, 9, 7, GB0); R(d, cx+1, 47, 7, 3, GB1)
    # Reception desk
    if receptionist:
        R(d, 15, 38, 30, 8, GB0)
        R(d, 20, 35, 8, 3, GB1)  # monitor
        draw_npc(d, 22, 26, 2)   # receptionist
    # Elevator
    R(d, 8, GBH-20, 16, 16, GB0)
    R(d, 9, GBH-19, 6, 14, GB1)
    R(d, 17, GBH-19, 6, 14, GB1)
    # Stairwell door
    R(d, GBW-18, 42, 14, 18, GB0)
    R(d, GBW-16, 44, 10, 14, GB1)
    if af % 6 < 3:
        d.polygon([(GBW-12, 38), (GBW-15, 42), (GBW-9, 42)], fill=GB3)
    if npcs:
        for i, (nx, ny) in enumerate(npcs):
            draw_npc(d, nx, ny, i)
    draw_player(d, int(px_pos), int(py_pos), 'right', af)
    loc(d, "FLOOR 6 - WAITING AREA")
    return img

def stairwell(py_pos, af):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, GBH, GB1)
    sy = 8
    for i in range(6):
        sx = 20 if i%2==0 else 90
        R(d, sx, sy, 70, 5, GB2)
        R(d, sx, sy+5, 70, 2, GB0)
        R(d, sx-2, sy-2, 2, 9, GB0)
        R(d, sx+70, sy-2, 2, 9, GB0)
        sy += 16
    d.text((6, 10), "7", font=F8, fill=GB3)
    d.text((6, GBH-16), "6", font=F8, fill=GB3)
    R(d, 110, 6, 12, 16, GB0); R(d, 118, 12, 3, 3, GB3)
    ppx = 55 + int(math.sin(py_pos*0.12)*20)
    draw_player(d, ppx, int(py_pos), 'up', af)
    loc(d, "STAIRWELL")
    return img

def office7(px_pos, py_pos, af, npcs=None, wave=False):
    img = gb(); d = ImageDraw.Draw(img)
    for ty in range(10, GBH, 9):
        for tx in range(0, GBW, 9):
            c = GB2 if (tx//9+ty//9)%2==0 else GB3
            R(d, tx, ty, 9, 9, c)
    R(d, 0, 10, GBW, 4, GB1)
    desks = [(15,24),(65,20),(120,28),(15,58),(70,62),(125,58),(45,85),(100,85)]
    for dx, dy in desks:
        R(d, dx, dy, 18, 8, GB0)
        R(d, dx+2, dy-3, 7, 3, GB1)
        R(d, dx+5, dy+10, 7, 5, GB1)
    R(d, 4, 42, 4, 14, GB0)  # door
    if npcs:
        for i, (nx, ny) in enumerate(npcs):
            draw_npc(d, nx, ny, i)
            if wave and af % 6 < 3:
                d.text((nx+2, ny-7), "!", font=F3, fill=GB0)
    draw_player(d, int(px_pos), int(py_pos), 'right', af)
    loc(d, "OFFICE - FLOOR 7")
    return img

def meeting(af, mood='good', tf=0, pal=None):
    p = pal or (GB0, GB1, GB2, GB3)
    img = Image.new("RGB", (GBW, GBH), p[3])
    d = ImageDraw.Draw(img)
    R(d, 0, 10, GBW, GBH-10, p[2])
    R(d, 0, 10, GBW, 4, p[1]); R(d, 0, 10, 4, GBH, p[1]); R(d, GBW-4, 10, 4, GBH, p[1])
    # Table
    R(d, 30, 38, 100, 30, p[1])
    # Whiteboard
    R(d, 50, 14, 60, 20, p[3])
    d.rectangle([(50, 14), (109, 33)], outline=p[0])
    for i in range(4):
        lw = random.randint(10, 45)
        d.line([(55+random.randint(0,15), 17+i*4), (55+lw, 17+i*4)], fill=p[1] if mood != 'tech' else p[0], width=1)
    if mood == 'tech':
        for i in range(2):
            lw = random.randint(20, 50)
            d.line([(55+random.randint(0,8), 28+i*3), (55+lw, 28+i*3)], fill=p[0], width=1)
    # 3 interviewers
    npc_pos = [(40, 24), (72, 22), (108, 24)]
    for i, (nx, ny) in enumerate(npc_pos):
        draw_npc(d, nx, ny, i, pal)
    # Player
    draw_player(d, 72, 78, 'up', af, pal)
    # Speech / mood indicators
    if mood == 'good':
        if tf % 8 < 4:
            sp = tf % 3
            sx, sy = npc_pos[sp]
            d.line([(sx+4, sy-3), (sx+4, sy-7)], fill=p[0])
            d.line([(sx+2, sy-5), (sx+6, sy-5)], fill=p[0])
    elif mood == 'nervous':
        if af % 4 < 2:
            px(d, 68, 76, p[0]); px(d, 80, 75, p[0])
        d.text((66, 70), "!", font=F3, fill=p[0])
    # Door
    R(d, GBW-12, 50, 8, 14, p[0])
    loc(d, "MEETING ROOM - FLOOR 7", pal)
    return img

# ══════════════════════════════════════════════════════════════════
# ANIMATION
# ══════════════════════════════════════════════════════════════════

print("Scene 1: Collins Street")
# Walk from right to building
for i in range(40):
    ppx = 155 - i * 2.2
    ppy = 70 if i < 22 else 70 - (i-22) * 1.5
    img = collins_street(ppx, ppy, i)
    d = ImageDraw.Draw(img)
    if i == 2:
        dlg(d, "Collins Street.\nTuesday afternoon.")
    elif 3 <= i <= 10:
        dlg(d, "Collins Street.\nTuesday afternoon.", i%4<2)
    save(img)

# Arrive at door
for i in range(12):
    img = collins_street(86, 48, i)
    d = ImageDraw.Draw(img)
    if i >= 2:
        dlg(d, "This is the one.\nDeep breath.", i%4<2)
    save(img)

for _ in range(4): save(gb())

print("Scene 2: Lobby")
for i in range(20):
    ppx = 86 - i*0.4 if i < 6 else 84
    ppy = GBH-14 - i*3.2 if i < 6 else GBH-14-19.2
    if i >= 6:
        ppx = 84 + (i-6)*4.5
        ppy = 54
    img = lobby(int(ppx), int(ppy), i)
    d = ImageDraw.Draw(img)
    if i == 1:
        dlg(d, "Nice lobby.")
    elif 2 <= i <= 6:
        dlg(d, "Nice lobby.", i%4<2)
    save(img)

# At elevator
for i in range(8):
    img = lobby(GBW-30, 48, i)
    d = ImageDraw.Draw(img)
    if i >= 2:
        dlg(d, "Floor 6, please.", i%4<2)
    save(img)

print("Scene 3: Elevator up")
for i in range(5): save(elevator(1, 'closed', i))
for fl in range(1, 7):
    for f in range(4): save(elevator(fl, 'closed', f))
# Ding!
for i in range(5): save(elevator(6, 'opening', i))
for i in range(4): save(elevator(6, 'open', i))
for _ in range(3): save(gb())

print("Scene 4: Floor 6 — receptionist + waiting")
# Walk out of elevator
for i in range(24):
    ppx = 16 + i*3.5
    ppy = GBH-26 if i < 6 else GBH-26 - (i-6)*2.2
    img = floor6(int(ppx), int(max(44, ppy)), i)
    d = ImageDraw.Draw(img)
    if i == 8:
        dlg(d, "Hi, I have a 3pm\ninterview?")
    elif 9 <= i <= 17:
        dlg(d, "Hi, I have a 3pm\ninterview?", i%4<2)
    save(img)

# Receptionist responds
for i in range(12):
    img = floor6(80, 44, i)
    d = ImageDraw.Draw(img)
    dlg(d, "Sure! Take a seat.\nSomeone will be\nwith you shortly.", i%4<2)
    save(img)

# Sit and wait
for i in range(18):
    img = floor6(62, 52, i)
    d = ImageDraw.Draw(img)
    if i == 6:
        dlg(d, "...")
    elif 7 <= i <= 11:
        dlg(d, "...", i%4<2)
    save(img)

print("Scene 5: Someone comes")
for i in range(20):
    img = floor6(62, 52, i)
    d = ImageDraw.Draw(img)
    npc_x = GBW - 20 - max(0, i-4)*5
    npc_y = 48
    if i >= 4:
        draw_npc(d, int(max(78, npc_x)), npc_y, 0)
    if i == 10:
        dlg(d, "Hi! I'm Sarah.\nFollow me upstairs?")
    elif 11 <= i <= 19:
        dlg(d, "Hi! I'm Sarah.\nFollow me upstairs?", i%4<2)
    save(img)

print("Scene 6: Stairwell")
for _ in range(3): save(gb())
for i in range(28):
    py = GBH - 24 - i*3.5
    save(stairwell(max(14, py), i))
# Through the door
img = stairwell(14, 0)
d = ImageDraw.Draw(img)
dlg(d, "Floor 7. Here we go.")
save(img, 8)
for _ in range(3): save(gb())

print("Scene 7: Floor 7 entrance")
desk_npcs = [(25, 70), (80, 70), (130, 24), (35, 30)]
for i in range(18):
    ppx = 10 + i*4
    img = office7(int(ppx), 46, i, npcs=desk_npcs)
    d = ImageDraw.Draw(img)
    if i == 4:
        dlg(d, "Big office.\nLots of screens.")
    elif 5 <= i <= 12:
        dlg(d, "Big office.\nLots of screens.", i%4<2)
    save(img)

print("Scene 8: Meeting room — the interview")
# Good start
for i in range(28):
    img = meeting(i, 'good', i, MEET_GOOD)
    d = ImageDraw.Draw(img)
    if i == 4:
        dlg(d, "Tell us about your\nwork at Gfycat.", MEET_GOOD)
    elif 5 <= i <= 15:
        dlg(d, "Tell us about your\nwork at Gfycat.", i%4<2, MEET_GOOD)
    elif i == 20:
        dlg(d, "80 million to 180\nmillion MAU...", True, MEET_GOOD)
    elif 21 <= i <= 27:
        dlg(d, "80 million to 180\nmillion MAU...", i%4<2, MEET_GOOD)
    save(img)

# Technical challenge — blue shift
for i in range(22):
    img = meeting(i, 'tech', i, MEET_TECH)
    d = ImageDraw.Draw(img)
    if i == 2:
        dlg(d, "OK, now a design\nchallenge.", True, MEET_TECH)
    elif 3 <= i <= 12:
        dlg(d, "OK, now a design\nchallenge.", i%4<2, MEET_TECH)
    elif i == 16:
        dlg(d, "Walk us through\nyour approach.", True, MEET_TECH)
    elif 17 <= i <= 21:
        dlg(d, "Walk us through\nyour approach.", i%4<2, MEET_TECH)
    save(img)

# Nervous — red shift
for i in range(16):
    img = meeting(i, 'nervous', i, MEET_NERVOUS)
    d = ImageDraw.Draw(img)
    if i == 2:
        dlg(d, "Hmm, that's\ntricky...", True, MEET_NERVOUS)
    elif 3 <= i <= 10:
        dlg(d, "Hmm, that's\ntricky...", i%4<2, MEET_NERVOUS)
    save(img)

# Recovery — back to tech then good
for i in range(10):
    # Transition from nervous to tech
    img = meeting(i, 'tech', i, MEET_TECH)
    d = ImageDraw.Draw(img)
    if i == 2:
        dlg(d, "Actually, wait.\nI'd frame it like\nthis...", True, MEET_TECH)
    elif 3 <= i <= 9:
        dlg(d, "Actually, wait.\nI'd frame it like\nthis...", i%4<2, MEET_TECH)
    save(img)

# Back to good — green
for i in range(22):
    img = meeting(i, 'good', i, MEET_GOOD)
    d = ImageDraw.Draw(img)
    if i == 2:
        dlg(d, "That's a great\nanswer.", True, MEET_GOOD)
    elif 3 <= i <= 10:
        dlg(d, "That's a great\nanswer.", i%4<2, MEET_GOOD)
    elif i == 14:
        dlg(d, "One more thing -\nyour AR patents?", True, MEET_GOOD)
    elif 15 <= i <= 21:
        dlg(d, "One more thing -\nyour AR patents?", i%4<2, MEET_GOOD)
    save(img)

# Final good stretch
for i in range(16):
    img = meeting(i, 'good', i, MEET_GOOD)
    d = ImageDraw.Draw(img)
    if i == 3:
        dlg(d, "Thanks so much for\ncoming in today.", True, MEET_GOOD)
    elif 4 <= i <= 12:
        dlg(d, "Thanks so much for\ncoming in today.", i%4<2, MEET_GOOD)
    save(img)

print("Scene 9: Office tour")
tour_npcs = desk_npcs + [(55, 45), (110, 48)]
for i in range(30):
    ppx = 55 + int(math.sin(i*0.18)*28)
    ppy = 44 + int(math.cos(i*0.13)*18)
    g1x, g1y = ppx+14, ppy-3
    g2x, g2y = ppx+7, ppy-10
    all_n = tour_npcs + [(g1x, g1y), (g2x, g2y)]
    img = office7(ppx, ppy, i, npcs=all_n, wave=(i > 12))
    d = ImageDraw.Draw(img)
    if i == 4:
        dlg(d, "Let me show you\naround!")
    elif 5 <= i <= 12:
        dlg(d, "Let me show you\naround!", i%4<2)
    elif i == 18:
        dlg(d, "This is the design\nteam area.")
    elif 19 <= i <= 25:
        dlg(d, "This is the design\nteam area.", i%4<2)
    save(img)

# People waving
for i in range(12):
    img = office7(85, 44, i, npcs=tour_npcs, wave=True)
    d = ImageDraw.Draw(img)
    if i >= 2:
        dlg(d, "Everyone's friendly.\nGood sign.", i%4<2)
    save(img)

print("Scene 10: Elevator down")
for _ in range(4): save(gb())
for fl in range(7, 0, -1):
    for f in range(3): save(elevator(fl, 'closed', f))
for i in range(4): save(elevator(1, 'opening', i))
for _ in range(3): save(gb())

print("Scene 11: Exit to Collins Street")
for i in range(12):
    ppx = GBW-30 - i*5
    ppy = 54 + i*2.5
    img = lobby(int(max(40, ppx)), int(min(GBH-12, ppy)), i)
    save(img)
for _ in range(3): save(gb())

for i in range(28):
    ppx = 88 + i*2
    ppy = 52 + min(18, i*1.2)
    img = collins_street(int(min(155, ppx)), int(min(70, ppy)), i)
    d = ImageDraw.Draw(img)
    if i == 8:
        dlg(d, "Done.")
    elif 9 <= i <= 14:
        dlg(d, "Done.", i%4<2)
    elif i == 20:
        dlg(d, "That felt good.")
    elif 21 <= i <= 27:
        dlg(d, "That felt good.", i%4<2)
    save(img)

# Hold on street
for i in range(14):
    img = collins_street(155, 70, i)
    save(img)

# Fade
for i in range(14):
    img = collins_street(155, 70, i)
    big = scale_up(img)
    big = ImageEnhance.Brightness(big).enhance(1.0 - i/14.0)
    for _ in range(1):
        big.save(os.path.join(OUT_DIR, f"frame_{frame_num:05d}.png"))
        frame_num += 1

print("Scene 12: End card")
for i in range(36):
    img = gb()
    d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, GBH, GB0)
    if i > 4:
        d.text((GBW//2-34, GBH//2-18), "ClawdJob", font=F5, fill=GB2)
    if i > 10:
        d.text((GBW//2-26, GBH//2-4), "Phosphor", font=F5, fill=GB3)
    if i > 16:
        d.text((GBW//2-14, GBH//2+12), "2026", font=F5, fill=GB1)
    save(img)

# Hold end card
for _ in range(24): save(img)

# Black
for _ in range(6): save(gb())

print(f"Total frames: {frame_num}")
print(f"Duration: {frame_num / FPS:.1f}s")

# ── Happy Chiptune Audio ──────────────────────────────────────────
print("Generating happy chiptune audio...")
AUDIO_PATH = os.path.join(OUT_DIR, "audio.wav")
SR = 22050
dur = frame_num / FPS + 0.5
ns = int(SR * dur)

def sq(t, freq, duty=0.5):
    return 1.0 if (t*freq) % 1.0 < duty else -1.0

def tri(t, freq):
    p = (t*freq) % 1.0
    return 4*abs(p - 0.5) - 1.0

# Happy major key melody — C major pentatonic, bouncy
# Pattern: ascending phrases with resolution
melody = [
    523, 587, 659, 784, 880, 784, 659, 587,  # C5 D5 E5 G5 A5 G5 E5 D5
    523, 659, 784, 880, 1047, 880, 784, 659,  # higher phrase
    523, 587, 659, 523, 440, 523, 587, 659,   # bouncy resolution
    784, 880, 784, 659, 523, 587, 523, 440,   # descending happy
]
bass = [
    262, 262, 330, 330, 392, 392, 330, 330,   # C E G E
    262, 262, 392, 392, 262, 262, 330, 330,
    196, 196, 262, 262, 330, 330, 392, 392,
    262, 262, 196, 196, 262, 262, 196, 196,
]
# Arp patterns — major triads
arps = [262, 330, 392, 523, 392, 330]

beat = 0.18  # faster, bouncier tempo

samples = []
for s in range(ns):
    t = s / SR
    bi = int(t / beat)

    # Lead — 25% duty square (classic GB lead)
    mf = melody[bi % len(melody)]
    mf += math.sin(t * 5) * 1.5  # tiny vibrato
    v = sq(t, mf, 0.25) * 0.07

    # Bass — 50% duty
    bf = bass[(bi//2) % len(bass)]
    v += sq(t, bf, 0.5) * 0.05

    # Arp — triangle wave, fast
    ai = int(t / 0.06) % len(arps)
    v += tri(t, arps[ai]) * 0.025

    # Hi-hat on every beat
    bp = (t % beat) / beat
    if bp < 0.04:
        v += (random.random()-0.5) * 0.10 * (1-bp/0.04)
    # Kick on 1 and 3
    if bi % 4 in (0, 2):
        kp = (t % (beat*2)) / (beat*2)
        if kp < 0.03:
            v += math.sin(2*math.pi*80*t*(1-kp/0.03)) * 0.12 * (1-kp/0.03)
    # Snare on 2 and 4
    if bi % 4 in (1, 3):
        sp = ((t - beat) % (beat*2)) / (beat*2)
        if sp < 0.02:
            v += (random.random()-0.5) * 0.08

    # Fade
    if t < 0.8: v *= t/0.8
    if t > dur-1.5: v *= max(0, (dur-t)/1.5)

    v = max(-0.95, min(0.95, v))
    samples.append(int(v * 32767))

with open(AUDIO_PATH, 'wb') as f:
    ds = ns * 2
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36+ds))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<IHHIIHH', 16, 1, 1, SR, SR*2, 2, 16))
    f.write(b'data')
    f.write(struct.pack('<I', ds))
    for sv in samples:
        f.write(struct.pack('<h', sv))

print("Audio generated.")

print("Rendering video...")
cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(OUT_DIR, "frame_%05d.png"),
    "-i", AUDIO_PATH,
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest", "-movflags", "+faststart",
    FINAL
]
subprocess.run(cmd, check=True)
print(f"Done! {FINAL}")
