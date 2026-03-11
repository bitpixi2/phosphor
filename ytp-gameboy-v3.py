#!/usr/bin/env python3
"""
GameBoy Interview Adventure v3
320x180 native (16:9), crisp bitmap text, correct names/details,
train ending, better music.
"""

import os, random, math, struct, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# GB palette
C0 = (15, 56, 15)
C1 = (48, 98, 48)
C2 = (139, 172, 15)
C3 = (155, 188, 15)

# Meeting palettes (darkest, dark, light, lightest)
PAL_GOOD = ((30, 100, 40), (55, 135, 60), (140, 195, 70), (165, 215, 85))
PAL_NERV = ((110, 45, 35), (135, 65, 45), (195, 135, 75), (215, 160, 90))
PAL_TECH = ((25, 50, 90), (45, 78, 115), (115, 160, 175), (140, 185, 195))
PAL_STD  = (C0, C1, C2, C3)

GBW, GBH = 320, 180
W, H = 1920, 1080
SCALE = 6
OX = (W - GBW*SCALE)//2
OY = (H - GBH*SCALE)//2
FPS = 12

OUT = "/home/clawdjob/.openclaw/workspace/art/ytp-frames-gb3"
FINAL = "/home/clawdjob/.openclaw/workspace/art/ytp-gameboy-interview-v3.mp4"
os.makedirs(OUT, exist_ok=True)

frame_num = 0

# ── BITMAP FONT ────────────────────────────────────────────────────
# To avoid antialiasing blur, we render text onto a 1-bit image then
# colorize and paste. This gives perfectly crisp pixel text.

def get_font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_bold(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return get_font(size)

F_SM = get_font(10)
F_MD = get_font(12)
F_LG = get_bold(14)
F_XL = get_bold(18)

def crisp_text(target, x, y, text, font, color):
    """Render text without antialiasing by thresholding"""
    # Measure text
    tmp = Image.new("L", (GBW, GBH), 0)
    td = ImageDraw.Draw(tmp)
    td.text((x, y), text, font=font, fill=255)
    # Threshold to 1-bit
    mask = tmp.point(lambda p: 255 if p > 80 else 0, mode='1')
    # Create colored version
    colored = Image.new("RGB", (GBW, GBH), color)
    target.paste(colored, mask=mask)

def crisp_text_draw(img, x, y, text, font, color):
    """Direct crisp text onto image"""
    crisp_text(img, x, y, text, font, color)

def centered_crisp(img, y, text, font, color):
    tmp = Image.new("L", (1, 1), 0)
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0,0), text, font=font)
    tw = bbox[2] - bbox[0]
    crisp_text(img, (GBW-tw)//2, y, text, font, color)

# ── FRAME OPS ──────────────────────────────────────────────────────
def gb(pal=None):
    return Image.new("RGB", (GBW, GBH), (pal or PAL_STD)[3])

def sup(img):
    bg = Image.new("RGB", (W, H), (8, 12, 8))
    bg.paste(img.resize((GBW*SCALE, GBH*SCALE), Image.NEAREST), (OX, OY))
    return bg

def save(img, n=1):
    global frame_num
    big = sup(img)
    for _ in range(n):
        big.save(os.path.join(OUT, f"frame_{frame_num:05d}.png"))
        frame_num += 1

def R(d, x, y, w, h, c):
    d.rectangle([(x,y),(x+w-1,y+h-1)], fill=c)

def player(d, x, y, face='down', f=0, p=None):
    p = p or PAL_STD
    R(d, x+3, y, 6, 5, p[0])
    R(d, x+1, y+5, 10, 5, p[1])
    if f%2==0:
        R(d, x+1, y+10, 4, 3, p[0]); R(d, x+7, y+10, 4, 3, p[0])
    else:
        R(d, x+3, y+10, 4, 3, p[0]); R(d, x+5, y+10, 4, 3, p[0])
    if face=='down':
        R(d, x+4, y+2, 2, 2, p[3]); R(d, x+7, y+2, 2, 2, p[3])
    elif face=='right':
        R(d, x+7, y+2, 2, 2, p[3])
    elif face=='left':
        R(d, x+3, y+2, 2, 2, p[3])

def npc(d, x, y, v=0, p=None):
    p = p or PAL_STD
    bc = p[0] if v%2==0 else p[1]
    R(d, x+3, y, 6, 5, p[1])
    R(d, x+4, y+2, 2, 2, p[3]); R(d, x+7, y+2, 2, 2, p[3])
    R(d, x+1, y+5, 10, 5, bc)
    R(d, x+1, y+10, 4, 3, p[1]); R(d, x+7, y+10, 4, 3, p[1])

def dlg(img, text, cursor=True, pal=None):
    p = pal or PAL_STD
    bx, by = 8, GBH-48
    bw, bh = GBW-16, 42
    d = ImageDraw.Draw(img)
    R(d, bx, by, bw, bh, p[3])
    d.rectangle([(bx,by),(bx+bw-1,by+bh-1)], outline=p[0])
    d.rectangle([(bx+1,by+1),(bx+bw-2,by+bh-2)], outline=p[1])
    lines = text.split('\n')
    for i, line in enumerate(lines):
        crisp_text(img, bx+8, by+6+i*12, line, F_SM, p[0])
    if cursor:
        tx, ty = bx+bw-14, by+bh-12
        d.polygon([(tx,ty),(tx+5,ty+4),(tx,ty+8)], fill=p[0])

def loc(img, text, pal=None):
    p = pal or PAL_STD
    d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, 14, p[0])
    crisp_text(img, 6, 2, text, F_SM, p[3])

# ══════════════════════════════════════════════════════════════════
# SCENE FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def sc_collins(px, py, af):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, 40, C2)
    for i in range(12):
        bx = i*28-6; bh = 50+(i*13)%30
        R(d, bx, 40, 24, bh, C1)
        for wy in range(44, 40+bh-8, 10):
            for wx in range(bx+3, bx+20, 8):
                R(d, wx, wy, 4, 4, C3 if random.random()>0.3 else C2)
    R(d, 0, 90, GBW, 12, C2)
    R(d, 0, 102, GBW, 78, C1)
    for rx in range(0, GBW, 22):
        R(d, rx+(af*3)%22, 130, 10, 2, C2)
    for tx in [30, 100, 190, 270]:
        R(d, tx, 82, 3, 8, C1); R(d, tx-4, 74, 11, 10, C0)
    R(d, 145, 40, 30, 50, C0)
    R(d, 150, 78, 20, 12, C3)
    if af%4<2:
        d.polygon([(160, 34), (155, 38), (165, 38)], fill=C3)
    player(d, int(px), int(py), 'up' if py < 92 else 'right', af)
    loc(img, "COLLINS ST, MELBOURNE")
    return img

def sc_lobby(px, py, af):
    img = gb(); d = ImageDraw.Draw(img)
    for ty in range(14, GBH, 18):
        for tx in range(0, GBW, 18):
            c = C2 if (tx//18+ty//18)%2==0 else C3
            R(d, tx, ty, 18, 18, c)
    R(d, 0, 14, GBW, 8, C1); R(d, 0, 14, 8, GBH, C1); R(d, GBW-8, 14, 8, GBH, C1)
    R(d, 80, 35, 70, 14, C0); R(d, 88, 30, 12, 5, C1)
    R(d, GBW-35, 60, 24, 32, C0)
    R(d, GBW-34, 61, 10, 30, C1); R(d, GBW-22, 61, 10, 30, C1)
    d.polygon([(GBW-22, 54), (GBW-26, 59), (GBW-18, 59)], fill=C3)
    R(d, 18, 35, 8, 5, C0); R(d, 15, 27, 14, 10, C1)
    R(d, 140, GBH-8, 24, 8, C2)
    player(d, int(px), int(py), 'right' if px < GBW-40 else 'up', af)
    loc(img, "LOBBY - GROUND FLOOR")
    return img

def sc_elev(floor, door='closed', af=0, going_up=True):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 30, 14, GBW-60, GBH-14, C1)
    R(d, 36, 20, GBW-72, GBH-26, C2)
    R(d, 44, 34, 20, 60, C0)
    for fi in range(1, 8):
        c = C3 if fi == floor else C1
        R(d, 48, 36+(7-fi)*7, 12, 5, c)
    R(d, GBW//2-12, 22, 24, 14, C0)
    centered_crisp(img, 24, str(floor), F_LG, C3)
    # Arrow
    if going_up:
        d.polygon([(GBW//2, 18), (GBW//2-4, 22), (GBW//2+4, 22)], fill=C3)
    else:
        d.polygon([(GBW//2, 40), (GBW//2-4, 36), (GBW//2+4, 36)], fill=C3)
    if door == 'closed':
        R(d, GBW//2-22, 48, 18, 90, C0)
        R(d, GBW//2+4, 48, 18, 90, C0)
    elif door == 'opening':
        ow = 8+(af%5)*4
        R(d, GBW//2-ow-4, 48, 10, 90, C0)
        R(d, GBW//2+ow-6, 48, 10, 90, C0)
    loc(img, f"ELEVATOR - FL {floor}")
    return img

def sc_floor6(px, py, af, show_npc=None, receptionist=True):
    img = gb(); d = ImageDraw.Draw(img)
    for ty in range(14, GBH, 12):
        for tx in range(0, GBW, 12):
            c = C2 if (tx//12+ty//12)%2==0 else C3
            R(d, tx, ty, 12, 12, c)
    R(d, 0, 14, GBW, 6, C1); R(d, 0, 14, 6, GBH, C1); R(d, GBW-6, 14, 6, GBH, C1)
    for dx in range(35, GBW-25, 45):
        R(d, dx, 20, 16, 24, C0); R(d, dx+11, 32, 4, 4, C2)
    for cx in range(90, 240, 22):
        R(d, cx, 75, 14, 10, C0); R(d, cx+1, 71, 12, 5, C1)
    if receptionist:
        R(d, 20, 55, 42, 12, C0); R(d, 28, 50, 12, 5, C1)
        npc(d, 30, 38, 2)
    R(d, 10, GBH-28, 22, 22, C0)
    R(d, 11, GBH-27, 9, 20, C1); R(d, 22, GBH-27, 9, 20, C1)
    R(d, GBW-24, 62, 18, 24, C0); R(d, GBW-22, 64, 14, 20, C1)
    if af%6<3:
        d.polygon([(GBW-16, 56), (GBW-20, 62), (GBW-12, 62)], fill=C3)
    if show_npc:
        for i, (nx, ny) in enumerate(show_npc):
            npc(d, nx, ny, i)
    player(d, int(px), int(py), 'right', af)
    loc(img, "FLOOR 6 - WAITING AREA")
    return img

def sc_stair(py, af):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, GBH, C1)
    sy = 12
    for i in range(7):
        sx = 30 if i%2==0 else 150
        R(d, sx, sy, 100, 7, C2); R(d, sx, sy+7, 100, 2, C0)
        R(d, sx-3, sy-2, 3, 11, C0); R(d, sx+100, sy-2, 3, 11, C0)
        sy += 22
    crisp_text(img, 10, 14, "7", F_XL, C3)
    crisp_text(img, 10, GBH-24, "6", F_XL, C3)
    R(d, 190, 10, 18, 22, C0); R(d, 204, 18, 4, 4, C3)
    ppx = 90+int(math.sin(py*0.08)*30)
    player(d, ppx, int(py), 'up', af)
    loc(img, "STAIRWELL")
    return img

def sc_office7(px, py, af, npcs=None, wave=False):
    img = gb(); d = ImageDraw.Draw(img)
    for ty in range(14, GBH, 11):
        for tx in range(0, GBW, 11):
            c = C2 if (tx//11+ty//11)%2==0 else C3
            R(d, tx, ty, 11, 11, c)
    R(d, 0, 14, GBW, 5, C1)
    desks = [(20,34),(90,28),(180,36),(260,30),(20,85),(95,90),(180,85),(260,90)]
    for dx, dy in desks:
        R(d, dx, dy, 24, 10, C0); R(d, dx+3, dy-5, 10, 5, C1)
        R(d, dx+7, dy+12, 10, 7, C1)
    R(d, 6, 62, 6, 18, C0)
    if npcs:
        for i, (nx, ny) in enumerate(npcs):
            npc(d, nx, ny, i)
            if wave and af%6<3:
                crisp_text(img, nx+3, ny-10, "!", F_SM, C0)
    player(d, int(px), int(py), 'right', af)
    loc(img, "OFFICE - FLOOR 7")
    return img

def sc_meeting(af, mood='good', tf=0, pal=None):
    p = pal or PAL_STD
    img = Image.new("RGB", (GBW, GBH), p[3])
    d = ImageDraw.Draw(img)
    R(d, 0, 14, GBW, GBH-14, p[2])
    R(d, 0, 14, GBW, 5, p[1]); R(d, 0, 14, 6, GBH, p[1]); R(d, GBW-6, 14, 6, GBH, p[1])
    R(d, 50, 55, 160, 40, p[1])
    R(d, 80, 20, 100, 28, p[3])
    d.rectangle([(80,20),(179,47)], outline=p[0])
    for i in range(5):
        lw = random.randint(15, 70)
        d.line([(86+random.randint(0,15), 24+i*5), (86+lw, 24+i*5)], fill=p[0] if mood=='tech' else p[1])
    if mood == 'tech':
        for i in range(3):
            lw = random.randint(25, 60)
            d.line([(86+random.randint(0,10), 36+i*4), (86+lw, 36+i*4)], fill=p[0])
    # 3 interviewers (Adel + Edward + 1 other)
    npc_pos = [(65, 36), (130, 34), (195, 36)]
    for i, (nx, ny) in enumerate(npc_pos):
        npc(d, nx, ny, i, p)
    player(d, 130, 110, 'up', af, p)
    if mood == 'good' and tf%8<4:
        sp = tf%3; sx, sy = npc_pos[sp]
        d.line([(sx+6, sy-4), (sx+6, sy-10)], fill=p[0], width=2)
        d.line([(sx+3, sy-7), (sx+9, sy-7)], fill=p[0], width=2)
    elif mood == 'nervous':
        if af%4<2:
            R(d, 124, 106, 2, 3, p[0]); R(d, 142, 105, 2, 3, p[0])
        crisp_text(img, 120, 100, "!", F_MD, p[0])
    R(d, GBW-16, 72, 10, 20, p[0])
    loc(img, "MEETING ROOM - FLOOR 7", p)
    return img

def sc_train(px, py, af, train_x=0):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, 50, C2)  # sky
    # City skyline receding
    for i in range(14):
        bx = i*24-4; bh = 25+(i*11)%20
        R(d, bx, 50-bh, 20, bh, C1)
    R(d, 0, 50, GBW, 8, C1)  # platform
    R(d, 0, 58, GBW, 4, C0)  # platform edge
    # Tracks
    R(d, 0, 62, GBW, 2, C0)
    R(d, 0, 72, GBW, 2, C0)
    for rx in range(0, GBW, 14):
        R(d, rx, 63, 2, 10, C1)
    R(d, 0, 74, GBW, GBH-74, C2)  # ground below
    # Train
    tx = int(train_x)
    R(d, tx, 52, 80, 20, C0)
    R(d, tx+2, 54, 76, 16, C1)
    # Windows
    for wx in range(tx+6, tx+72, 12):
        R(d, wx, 56, 8, 8, C3)
    # Front
    R(d, tx+74, 54, 6, 16, C0)
    R(d, tx+76, 58, 4, 4, C3)  # headlight
    if train_x <= 10:
        player(d, int(px), int(py), 'right', af)
    loc(img, "FLINDERS ST STATION")
    return img

# ══════════════════════════════════════════════════════════════════
# ANIMATION
# ══════════════════════════════════════════════════════════════════

print("Scene 1: Collins Street")
for i in range(44):
    ppx = 280-i*3
    ppy = 100 if i<24 else 100-(i-24)*2
    img = sc_collins(ppx, ppy, i)
    if i==2:
        dlg(img, "Collins Street.\nTuesday afternoon.")
    elif 3<=i<=14:
        dlg(img, "Collins Street.\nTuesday afternoon.", i%4<2)
    save(img)

for i in range(14):
    img = sc_collins(152, 56, i)
    if i>=2:
        dlg(img, "This is the one.\nDeep breath.", i%4<2)
    save(img)

for _ in range(4): save(gb())

print("Scene 2: Lobby")
for i in range(22):
    ppx = 148-i*0.5 if i<8 else 144
    ppy = GBH-16 - i*4.2 if i<8 else GBH-16-33.6
    if i>=8:
        ppx = 144+(i-8)*5.5
        ppy = 82
    img = sc_lobby(int(ppx), int(ppy), i)
    if i==2:
        dlg(img, "Nice lobby.")
    elif 3<=i<=8:
        dlg(img, "Nice lobby.", i%4<2)
    save(img)

for i in range(10):
    img = sc_lobby(GBW-42, 68, i)
    if i>=2:
        dlg(img, "Floor 6, please.", i%4<2)
    save(img)

print("Scene 3: Elevator up to 6")
for i in range(5): save(sc_elev(1, 'closed', i, going_up=True))
for fl in range(1,7):
    for f in range(4): save(sc_elev(fl, 'closed', f, going_up=True))
for i in range(5): save(sc_elev(6, 'opening', i, going_up=True))
for i in range(4): save(sc_elev(6, 'open', i, going_up=True))
for _ in range(3): save(gb())

print("Scene 4: Floor 6 — receptionist + waiting")
for i in range(28):
    ppx = 20+i*4
    ppy = GBH-34 if i<8 else GBH-34-(i-8)*2.5
    img = sc_floor6(int(ppx), int(max(62, ppy)), i)
    if i==10:
        dlg(img, "Hi, I have a 3pm\ninterview. Software\nengineer role?")
    elif 11<=i<=22:
        dlg(img, "Hi, I have a 3pm\ninterview. Software\nengineer role?", i%4<2)
    save(img)

for i in range(14):
    img = sc_floor6(120, 62, i)
    dlg(img, "Sure! Take a seat.\nSomeone will be right\nwith you.", i%4<2)
    save(img)

for i in range(20):
    img = sc_floor6(100, 77, i)
    if i==8:
        dlg(img, "...")
    elif 9<=i<=14:
        dlg(img, "...", i%4<2)
    save(img)

print("Scene 5: Adel comes")
for i in range(24):
    img = sc_floor6(100, 77, i)
    d = ImageDraw.Draw(img)
    npc_x = GBW-26 - max(0, i-4)*6
    npc_y = 68
    if i>=4:
        npc(d, int(max(130, npc_x)), npc_y, 0)
    if i==12:
        dlg(img, "Hi! I'm Adel.\nFollow me upstairs?")
    elif 13<=i<=23:
        dlg(img, "Hi! I'm Adel.\nFollow me upstairs?", i%4<2)
    save(img)

print("Scene 6: Stairwell")
for _ in range(3): save(gb())
for i in range(30):
    py = GBH-28 - i*4.5
    save(sc_stair(max(18, py), i))
img = sc_stair(18, 0)
dlg(img, "Floor 7. Here we go.")
save(img, 10)
for _ in range(3): save(gb())

print("Scene 7: Floor 7 entrance")
desk_npcs = [(35,96),(105,96),(190,34),(265,38),(50,50),(140,55)]
for i in range(20):
    ppx = 14+i*5
    img = sc_office7(int(ppx), 66, i, npcs=desk_npcs)
    if i==5:
        dlg(img, "Big office.\nLots of screens.")
    elif 6<=i<=14:
        dlg(img, "Big office.\nLots of screens.", i%4<2)
    save(img)

print("Scene 8: Meeting room — the interview")
# Good intro
for i in range(30):
    img = sc_meeting(i, 'good', i, PAL_GOOD)
    if i==4:
        dlg(img, "Tell us about your\nwork at Gfycat.", True, PAL_GOOD)
    elif 5<=i<=16:
        dlg(img, "Tell us about your\nwork at Gfycat.", i%4<2, PAL_GOOD)
    elif i==20:
        dlg(img, "80 million to 180\nmillion MAU...", True, PAL_GOOD)
    elif 21<=i<=29:
        dlg(img, "80 million to 180\nmillion MAU...", i%4<2, PAL_GOOD)
    save(img)

# Technical — blue
for i in range(26):
    img = sc_meeting(i, 'tech', i, PAL_TECH)
    if i==2:
        dlg(img, "OK, now a technical\nchallenge.", True, PAL_TECH)
    elif 3<=i<=14:
        dlg(img, "OK, now a technical\nchallenge.", i%4<2, PAL_TECH)
    elif i==18:
        dlg(img, "Walk us through\nyour approach.", True, PAL_TECH)
    elif 19<=i<=25:
        dlg(img, "Walk us through\nyour approach.", i%4<2, PAL_TECH)
    save(img)

# Nervous — red
for i in range(18):
    img = sc_meeting(i, 'nervous', i, PAL_NERV)
    if i==2:
        dlg(img, "Hmm, that's\ntricky...", True, PAL_NERV)
    elif 3<=i<=12:
        dlg(img, "Hmm, that's\ntricky...", i%4<2, PAL_NERV)
    save(img)

# Recovery — blue
for i in range(12):
    img = sc_meeting(i, 'tech', i, PAL_TECH)
    if i==2:
        dlg(img, "Actually, wait.\nI'd frame it like\nthis...", True, PAL_TECH)
    elif 3<=i<=11:
        dlg(img, "Actually, wait.\nI'd frame it like\nthis...", i%4<2, PAL_TECH)
    save(img)

# Nailed it — green
for i in range(26):
    img = sc_meeting(i, 'good', i, PAL_GOOD)
    if i==2:
        dlg(img, "That's a great\nanswer.", True, PAL_GOOD)
    elif 3<=i<=12:
        dlg(img, "That's a great\nanswer.", i%4<2, PAL_GOOD)
    elif i==16:
        dlg(img, "Tell us about your\nAR patents.", True, PAL_GOOD)
    elif 17<=i<=25:
        dlg(img, "Tell us about your\nAR patents.", i%4<2, PAL_GOOD)
    save(img)

# Final good
for i in range(14):
    img = sc_meeting(i, 'good', i, PAL_GOOD)
    if i==2:
        dlg(img, "Thanks so much for\ncoming in today.", True, PAL_GOOD)
    elif 3<=i<=13:
        dlg(img, "Thanks so much for\ncoming in today.", i%4<2, PAL_GOOD)
    save(img)

print("Scene 9: Office tour")
tour_npcs = desk_npcs
for i in range(32):
    ppx = 80+int(math.sin(i*0.16)*40)
    ppy = 60+int(math.cos(i*0.12)*22)
    g1x, g1y = ppx+18, ppy-4
    g2x, g2y = ppx+10, ppy-14
    all_n = tour_npcs + [(g1x, g1y), (g2x, g2y)]
    img = sc_office7(ppx, ppy, i, npcs=all_n, wave=(i>14))
    if i==4:
        dlg(img, "Let me show you\naround!")
    elif 5<=i<=14:
        dlg(img, "Let me show you\naround!", i%4<2)
    elif i==20:
        dlg(img, "This is the\nengineering team.")
    elif 21<=i<=28:
        dlg(img, "This is the\nengineering team.", i%4<2)
    save(img)

for i in range(14):
    img = sc_office7(120, 60, i, npcs=tour_npcs, wave=True)
    if i>=2:
        dlg(img, "Everyone's friendly.\nGood sign.", i%4<2)
    save(img)

print("Scene 10: Elevator down from 7")
for _ in range(4): save(gb())
for fl in range(7, 0, -1):
    for f in range(3): save(sc_elev(fl, 'closed', f, going_up=False))
for i in range(4): save(sc_elev(1, 'opening', i, going_up=False))
for _ in range(3): save(gb())

print("Scene 11: Exit + lobby")
for i in range(10):
    ppx = GBW-42 - i*8
    ppy = 68+i*3
    img = sc_lobby(int(max(50, ppx)), int(min(GBH-14, ppy)), i)
    save(img)
for _ in range(3): save(gb())

print("Scene 12: Collins Street exit")
for i in range(20):
    ppx = 154+i*3
    ppy = 58+min(42, i*2.5)
    img = sc_collins(int(min(280, ppx)), int(min(100, ppy)), i)
    if i==6:
        dlg(img, "Done.")
    elif 7<=i<=14:
        dlg(img, "Done.", i%4<2)
    save(img)

for i in range(10):
    img = sc_collins(280, 100, i)
    save(img)

print("Scene 13: Train departure")
for _ in range(3): save(gb())

# Walk onto platform + train arrives
for i in range(16):
    tx = -80+i*6 if i < 14 else 4
    img = sc_train(260-i*4, 50, i, train_x=tx)
    if i==4:
        dlg(img, "Platform 3.\nHomeward bound.")
    elif 5<=i<=12:
        dlg(img, "Platform 3.\nHomeward bound.", i%4<2)
    save(img)

# Board + train departs into distance
for i in range(30):
    tx = 4+i*12
    img = sc_train(0, 0, i, train_x=tx)
    d = ImageDraw.Draw(img)
    # Train shrinks as it goes
    if tx < GBW+100:
        save(img)
    else:
        save(img)

# Hold on empty platform
for i in range(8):
    img = sc_train(0, 0, i, train_x=GBW+200)
    save(img)

# Fade
for i in range(14):
    img = sc_train(0, 0, i, train_x=GBW+200)
    big = sup(img)
    big = ImageEnhance.Brightness(big).enhance(1.0-i/14.0)
    big.save(os.path.join(OUT, f"frame_{frame_num:05d}.png"))
    frame_num += 1

print("Scene 14: End card")
for i in range(42):
    img = gb(); d = ImageDraw.Draw(img)
    R(d, 0, 0, GBW, GBH, C0)
    if i>4:
        centered_crisp(img, GBH//2-30, "ClawdJob", F_XL, C2)
    if i>10:
        centered_crisp(img, GBH//2-6, "Phosphor", F_LG, C3)
    if i>16:
        centered_crisp(img, GBH//2+16, "2026", F_MD, C1)
    save(img)

# Hold
for _ in range(30): save(img)

for _ in range(6):
    img2 = gb(); ImageDraw.Draw(img2).rectangle([(0,0),(GBW-1,GBH-1)], fill=C0)
    save(img2)

print(f"Total frames: {frame_num}")
print(f"Duration: {frame_num/FPS:.1f}s")

# ── AUDIO: Cheerful melodic chiptune ──────────────────────────────
print("Generating cheerful audio...")
APATH = os.path.join(OUT, "audio.wav")
SR = 44100
dur = frame_num/FPS + 0.5
ns = int(SR*dur)

def sq(t, f, d=0.5):
    return 1.0 if (t*f)%1.0 < d else -1.0

def tri(t, f):
    p=(t*f)%1.0
    return 4*abs(p-0.5)-1.0

def sine(t, f):
    return math.sin(2*math.pi*f*t)

# Cheerful melody in C major — fuller, more melodic
# Using actual musical phrases that resolve nicely
mel = [
    # Phrase 1: bright ascending
    523, 523, 587, 659, 784, 784, 880, 784,
    # Phrase 2: happy bounce
    659, 784, 880, 1047, 880, 784, 659, 587,
    # Phrase 3: gentle resolution
    523, 587, 659, 523, 392, 440, 523, 523,
    # Phrase 4: triumphant
    659, 784, 880, 1047, 1175, 1047, 880, 784,
    # Phrase 5: coming home
    659, 587, 523, 440, 523, 587, 659, 523,
    # Phrase 6: playful
    784, 880, 784, 659, 523, 659, 784, 880,
    # Phrase 7: resolution
    1047, 880, 784, 659, 523, 587, 523, 440,
    # Phrase 8: ending
    523, 523, 659, 784, 523, 523, 440, 523,
]
bass = [
    262, 262, 262, 262, 330, 330, 330, 330,
    392, 392, 392, 392, 262, 262, 262, 262,
    196, 196, 262, 262, 330, 330, 392, 392,
    262, 262, 262, 262, 196, 196, 262, 262,
    330, 330, 392, 392, 262, 262, 196, 196,
    262, 262, 330, 330, 392, 392, 330, 330,
    262, 262, 196, 196, 330, 330, 262, 262,
    262, 262, 330, 330, 262, 262, 196, 262,
]
# Counter-melody harmony (thirds above lead)
harmony = [n * 1.26 for n in mel]  # ~major third up

arps = [262, 330, 392, 523, 659, 523, 392, 330]

beat = 0.165  # upbeat tempo

samps = []
for s in range(ns):
    t = s/SR
    bi = int(t/beat)

    # Lead — mix of square + sine for warmth
    mf = mel[bi%len(mel)]
    mf += math.sin(t*4.5)*1.2  # gentle vibrato
    v = sq(t, mf, 0.25) * 0.05
    v += sine(t, mf) * 0.03  # sine adds warmth

    # Harmony — softer triangle
    hf = harmony[bi%len(harmony)]
    v += tri(t, hf) * 0.018

    # Bass — warm sine + square
    bf = bass[(bi//2)%len(bass)]
    v += sine(t, bf) * 0.04
    v += sq(t, bf, 0.5) * 0.02

    # Arp — triangle, fast, light
    ai = int(t/0.07) % len(arps)
    v += tri(t, arps[ai]) * 0.015

    # Drums — punchy kick + crisp hat + snare
    bp = (t%beat)/beat
    if bp < 0.035:
        v += sine(t, 90*(1-bp/0.035)) * 0.10 * (1-bp/0.035)
    # Hi-hat every beat
    if bp < 0.025:
        v += (random.random()-0.5) * 0.06 * (1-bp/0.025)
    # Snare on 2,4
    if bi%4 in (1,3):
        sp = ((t-beat)%(beat*2))/(beat*2)
        if sp < 0.018:
            v += (random.random()-0.5) * 0.06

    # Reverb-ish: echo at ~100ms
    # (Simple delay would need buffer, just add a quiet copy)
    echo_t = t - 0.1
    if echo_t > 0:
        emf = mel[int(echo_t/beat)%len(mel)]
        v += sine(echo_t, emf) * 0.008

    # Fades
    if t < 1.0: v *= t
    if t > dur-2.0: v *= max(0, (dur-t)/2.0)

    v = max(-0.95, min(0.95, v))
    samps.append(int(v*32767))

with open(APATH, 'wb') as f:
    ds = ns*2
    f.write(b'RIFF'); f.write(struct.pack('<I', 36+ds))
    f.write(b'WAVE'); f.write(b'fmt ')
    f.write(struct.pack('<IHHIIHH', 16, 1, 1, SR, SR*2, 2, 16))
    f.write(b'data'); f.write(struct.pack('<I', ds))
    for sv in samps:
        f.write(struct.pack('<h', sv))

print("Audio generated.")

print("Rendering video...")
subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(OUT, "frame_%05d.png"),
    "-i", APATH,
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k",
    "-shortest", "-movflags", "+faststart",
    FINAL
], check=True)
print(f"Done! {FINAL}")
