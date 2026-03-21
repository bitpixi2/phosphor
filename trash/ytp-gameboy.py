#!/usr/bin/env python3
"""
GameBoy Interview Adventure
A 1995 Game Boy style video about finding a building on Collins Street,
navigating floors, interviewing, and leaving.
Rendered at native GB resolution (160x144) then scaled to 1920x1080.
"""

import os, random, math, struct, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# GameBoy palette (4 shades)
GB_DARKEST  = (15, 56, 15)
GB_DARK     = (48, 98, 48)
GB_LIGHT    = (139, 172, 15)
GB_LIGHTEST = (155, 188, 15)
GB_RED      = (140, 60, 40)    # "nervous" — still GB-ish but warmer
GB_BG = GB_LIGHTEST

# Native GB res, then scale
GBW, GBH = 160, 144
W, H = 1920, 1080
SCALE = min(W // GBW, H // GBH)  # 7x
OX = (W - GBW * SCALE) // 2
OY = (H - GBH * SCALE) // 2

FPS = 12  # chunky GB framerate
OUT_DIR = "/home/clawdjob/.openclaw/workspace/art/ytp-frames-gb"
FINAL = "/home/clawdjob/.openclaw/workspace/art/ytp-gameboy-interview.mp4"
os.makedirs(OUT_DIR, exist_ok=True)

frame_num = 0

def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# Tiny pixel fonts for GB
FONT_3 = get_font(5)
FONT_5 = get_font(7)
FONT_8 = get_font(8)

def gb_frame():
    """Create a blank GB-sized image"""
    return Image.new("RGB", (GBW, GBH), GB_LIGHTEST)

def scale_up(gb_img):
    """Scale GB image to 1920x1080 with nearest neighbor"""
    bg = Image.new("RGB", (W, H), (8, 12, 8))
    scaled = gb_img.resize((GBW * SCALE, GBH * SCALE), Image.NEAREST)
    bg.paste(scaled, (OX, OY))
    return bg

def save_frame(gb_img, count=1):
    global frame_num
    big = scale_up(gb_img)
    for _ in range(count):
        big.save(os.path.join(OUT_DIR, f"frame_{frame_num:05d}.png"))
        frame_num += 1

def rect(draw, x, y, w, h, color):
    draw.rectangle([(x, y), (x+w-1, y+h-1)], fill=color)

def pixel(draw, x, y, color):
    draw.point((x, y), fill=color)

# ── Sprite Drawing ─────────────────────────────────────────────────
def draw_player(draw, x, y, facing='down', frame=0):
    """8x8 player sprite — simple RPG character"""
    # Head
    rect(draw, x+2, y, 4, 3, GB_DARKEST)
    # Body
    rect(draw, x+1, y+3, 6, 3, GB_DARK)
    # Legs (animated)
    if frame % 2 == 0:
        rect(draw, x+1, y+6, 2, 2, GB_DARKEST)
        rect(draw, x+5, y+6, 2, 2, GB_DARKEST)
    else:
        rect(draw, x+2, y+6, 2, 2, GB_DARKEST)
        rect(draw, x+4, y+6, 2, 2, GB_DARKEST)
    # Eyes based on facing
    if facing == 'down':
        pixel(draw, x+3, y+1, GB_LIGHTEST)
        pixel(draw, x+5, y+1, GB_LIGHTEST)
    elif facing == 'up':
        pass  # back of head
    elif facing == 'left':
        pixel(draw, x+2, y+1, GB_LIGHTEST)
    elif facing == 'right':
        pixel(draw, x+5, y+1, GB_LIGHTEST)

def draw_npc(draw, x, y, variant=0):
    """8x8 NPC sprite"""
    # Head
    rect(draw, x+2, y, 4, 3, GB_DARK)
    pixel(draw, x+3, y+1, GB_LIGHTEST)
    pixel(draw, x+5, y+1, GB_LIGHTEST)
    # Body - different shades per variant
    body_col = GB_DARKEST if variant % 2 == 0 else GB_DARK
    rect(draw, x+1, y+3, 6, 3, body_col)
    # Legs
    rect(draw, x+1, y+6, 2, 2, GB_DARK)
    rect(draw, x+5, y+6, 2, 2, GB_DARK)

def draw_dialogue_box(draw, text, show_cursor=True):
    """Classic RPG dialogue box at bottom of screen"""
    bx, by = 4, GBH - 36
    bw, bh = GBW - 8, 32
    rect(draw, bx, by, bw, bh, GB_LIGHTEST)
    draw.rectangle([(bx, by), (bx+bw-1, by+bh-1)], outline=GB_DARKEST)
    draw.rectangle([(bx+1, by+1), (bx+bw-2, by+bh-2)], outline=GB_DARK)
    # Text
    draw.text((bx+6, by+6), text, font=FONT_3, fill=GB_DARKEST)
    if show_cursor:
        # Blinking triangle cursor
        tx = bx + bw - 12
        ty = by + bh - 10
        draw.polygon([(tx, ty), (tx+4, ty+3), (tx, ty+6)], fill=GB_DARKEST)

def draw_location_label(draw, text):
    """Top bar location indicator"""
    rect(draw, 0, 0, GBW, 12, GB_DARKEST)
    draw.text((4, 2), text, font=FONT_3, fill=GB_LIGHTEST)

# ── Scene Backgrounds ──────────────────────────────────────────────
def scene_collins_street(player_x, player_y, anim_frame):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Sky
    rect(draw, 0, 0, GBW, 30, GB_LIGHT)

    # Buildings - left side
    for i in range(6):
        bx = i * 28 - 10
        bh = 50 + (i * 7) % 30
        rect(draw, bx, 30, 24, bh, GB_DARK)
        # Windows
        for wy in range(34, 30 + bh - 8, 10):
            for wx in range(bx+3, bx+21, 8):
                rect(draw, wx, wy, 4, 4, GB_LIGHTEST if random.random() > 0.3 else GB_LIGHT)

    # Street / footpath
    rect(draw, 0, 80, GBW, 10, GB_LIGHT)
    rect(draw, 0, 90, GBW, 54, GB_DARK)

    # Road markings
    for rx in range(0, GBW, 20):
        rect(draw, rx + (anim_frame * 2) % 20, 110, 8, 2, GB_LIGHT)

    # Trees
    for tx in [20, 70, 130]:
        rect(draw, tx, 72, 2, 8, GB_DARK)
        rect(draw, tx-3, 66, 8, 8, GB_DARKEST)

    # Target building - highlighted entrance
    rect(draw, 72, 30, 28, 50, GB_DARKEST)
    rect(draw, 78, 70, 16, 10, GB_LIGHTEST)  # door
    # Subtle arrow above door
    if anim_frame % 4 < 2:
        draw.polygon([(86, 24), (82, 28), (90, 28)], fill=GB_LIGHTEST)

    draw_player(draw, player_x, player_y, 'up' if player_y < 85 else 'right', anim_frame)
    draw_location_label(draw, "COLLINS ST, MELBOURNE")
    return img

def scene_lobby(player_x, player_y, anim_frame):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Floor
    for ty in range(12, GBH, 16):
        for tx in range(0, GBW, 16):
            c = GB_LIGHT if (tx // 16 + ty // 16) % 2 == 0 else GB_LIGHTEST
            rect(draw, tx, ty, 16, 16, c)

    # Walls
    rect(draw, 0, 12, GBW, 8, GB_DARK)
    rect(draw, 0, 12, 8, GBH, GB_DARK)
    rect(draw, GBW-8, 12, 8, GBH, GB_DARK)

    # Front desk
    rect(draw, 50, 30, 60, 12, GB_DARKEST)
    rect(draw, 55, 26, 10, 4, GB_DARK)  # monitor

    # Elevator doors (right wall)
    rect(draw, GBW-28, 50, 20, 28, GB_DARKEST)
    rect(draw, GBW-27, 51, 8, 26, GB_DARK)
    rect(draw, GBW-18, 51, 8, 26, GB_DARK)
    # Up arrow
    draw.polygon([(GBW-19, 45), (GBW-22, 49), (GBW-16, 49)], fill=GB_LIGHTEST)

    # Potted plant
    rect(draw, 14, 30, 6, 4, GB_DARKEST)
    rect(draw, 12, 24, 10, 8, GB_DARK)

    # Door we came through (bottom)
    rect(draw, 70, GBH-8, 20, 8, GB_LIGHT)

    draw_player(draw, player_x, player_y, 'right' if player_x < GBW-35 else 'up', anim_frame)
    draw_location_label(draw, "LOBBY - GROUND FLOOR")
    return img

def scene_elevator(floor_num, door_state='closed', anim_frame=0):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Elevator interior
    rect(draw, 20, 12, GBW-40, GBH-12, GB_DARK)
    rect(draw, 24, 16, GBW-48, GBH-20, GB_LIGHT)

    # Panel
    rect(draw, 30, 30, 16, 50, GB_DARKEST)
    # Floor buttons
    for fi in range(8):
        bx, by = 33, 34 + fi * 6
        c = GB_LIGHTEST if fi + 1 == floor_num else GB_DARK
        rect(draw, bx, by, 8, 4, c)

    # Floor display
    rect(draw, GBW//2 - 10, 20, 20, 12, GB_DARKEST)
    draw.text((GBW//2 - 4, 22), str(floor_num), font=FONT_5, fill=GB_LIGHTEST)

    # Doors
    if door_state == 'closed':
        rect(draw, GBW//2 - 20, 40, 18, 80, GB_DARKEST)
        rect(draw, GBW//2 + 2, 40, 18, 80, GB_DARKEST)
    elif door_state == 'opening':
        ow = 8 + (anim_frame % 4) * 3
        rect(draw, GBW//2 - ow - 2, 40, 8, 80, GB_DARKEST)
        rect(draw, GBW//2 + ow - 6, 40, 8, 80, GB_DARKEST)
    # else open — no door panels

    draw_location_label(draw, f"ELEVATOR - FL {floor_num}")
    return img

def scene_hallway(player_x, player_y, floor_num, anim_frame):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Floor tiles
    for ty in range(12, GBH, 12):
        for tx in range(0, GBW, 12):
            c = GB_LIGHT if (tx // 12 + ty // 12) % 2 == 0 else GB_LIGHTEST
            rect(draw, tx, ty, 12, 12, c)

    # Walls
    rect(draw, 0, 12, GBW, 6, GB_DARK)
    rect(draw, 0, 12, 4, GBH, GB_DARK)
    rect(draw, GBW-4, 12, 4, GBH, GB_DARK)

    # Doors along hallway
    for dx in range(20, GBW-20, 35):
        rect(draw, dx, 18, 14, 20, GB_DARKEST)
        rect(draw, dx+10, 28, 3, 3, GB_LIGHT)  # handle

    # Bathroom sign
    rect(draw, 22, 14, 10, 4, GB_LIGHTEST)
    draw.text((23, 14), "WC", font=FONT_3, fill=GB_DARKEST)

    # Waiting chairs
    for cx in range(50, 130, 18):
        rect(draw, cx, 60, 10, 8, GB_DARKEST)
        rect(draw, cx+1, 56, 8, 4, GB_DARK)

    # Elevator at bottom left
    rect(draw, 8, GBH-24, 18, 20, GB_DARKEST)
    rect(draw, 9, GBH-23, 7, 18, GB_DARK)
    rect(draw, 18, GBH-23, 7, 18, GB_DARK)

    # Stairwell door at far right
    rect(draw, GBW-22, 50, 16, 22, GB_DARKEST)
    rect(draw, GBW-20, 52, 12, 18, GB_DARK)
    # Arrow up
    if anim_frame % 6 < 3:
        draw.polygon([(GBW-15, 46), (GBW-18, 50), (GBW-12, 50)], fill=GB_LIGHTEST)

    draw_player(draw, player_x, player_y, 'right', anim_frame)
    draw_location_label(draw, f"HALLWAY - FLOOR {floor_num}")
    return img

def scene_stairwell(player_y, going_up=True, anim_frame=0):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Stairwell walls
    rect(draw, 0, 0, GBW, GBH, GB_DARK)

    # Stairs - zigzag pattern
    stair_y = 10
    for i in range(8):
        sx = 20 if i % 2 == 0 else 80
        rect(draw, sx, stair_y, 60, 6, GB_LIGHT)
        rect(draw, sx, stair_y+6, 60, 2, GB_DARKEST)
        # Railing
        rect(draw, sx-2, stair_y-2, 2, 10, GB_DARKEST)
        rect(draw, sx+60, stair_y-2, 2, 10, GB_DARKEST)
        stair_y += 16

    # Floor labels
    draw.text((6, 14), "7", font=FONT_8, fill=GB_LIGHTEST)
    draw.text((6, GBH-18), "6", font=FONT_8, fill=GB_LIGHTEST)

    # Door at top
    rect(draw, 100, 8, 14, 18, GB_DARKEST)
    rect(draw, 110, 16, 3, 3, GB_LIGHTEST)

    # Player on stairs
    py = int(player_y)
    px = 50 + int(math.sin(py * 0.1) * 20)
    draw_player(draw, px, py, 'up' if going_up else 'down', anim_frame)

    draw_location_label(draw, "STAIRWELL")
    return img

def scene_office_floor7(player_x, player_y, anim_frame, npcs=None, wave=False):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Open plan office floor
    for ty in range(12, GBH, 10):
        for tx in range(0, GBW, 10):
            c = GB_LIGHT if (tx // 10 + ty // 10) % 2 == 0 else GB_LIGHTEST
            rect(draw, tx, ty, 10, 10, c)

    # Walls
    rect(draw, 0, 12, GBW, 4, GB_DARK)

    # Desks / cubicles scattered
    desk_positions = [(15, 30), (60, 25), (110, 35), (15, 70), (65, 75), (110, 70), (40, 100), (90, 100)]
    for dx, dy in desk_positions:
        rect(draw, dx, dy, 20, 10, GB_DARKEST)
        rect(draw, dx+2, dy-4, 8, 4, GB_DARK)  # monitor
        # Chair
        rect(draw, dx+6, dy+12, 8, 6, GB_DARK)

    # Door we came through
    rect(draw, 4, 50, 4, 16, GB_DARKEST)

    # NPCs at desks (waving if tour)
    if npcs:
        for i, (nx, ny) in enumerate(npcs):
            draw_npc(draw, nx, ny, i)
            if wave and anim_frame % 6 < 3:
                # Exclamation / wave indicator
                draw.text((nx+2, ny-8), "!", font=FONT_3, fill=GB_DARKEST)

    draw_player(draw, player_x, player_y, 'right', anim_frame)
    draw_location_label(draw, "OFFICE - FLOOR 7")
    return img

def scene_meeting_room(anim_frame, mood='good', talking_frame=0):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    # Room
    rect(draw, 0, 12, GBW, GBH-12, GB_LIGHT)
    rect(draw, 0, 12, GBW, 4, GB_DARK)
    rect(draw, 0, 12, 4, GBH, GB_DARK)
    rect(draw, GBW-4, 12, 4, GBH, GB_DARK)

    # Table
    rect(draw, 30, 45, 100, 40, GB_DARK)

    # Whiteboard
    rect(draw, 50, 16, 60, 24, GB_LIGHTEST)
    draw.rectangle([(50, 16), (109, 39)], outline=GB_DARKEST)
    # Scribbles on whiteboard
    for i in range(4):
        lw = random.randint(10, 40)
        draw.line([(55 + random.randint(0,20), 20+i*5), (55+lw, 20+i*5)], fill=GB_DARK, width=1)

    # 3 NPCs across the table (interviewers)
    npc_positions = [(40, 30), (72, 28), (104, 30)]
    for i, (nx, ny) in enumerate(npc_positions):
        draw_npc(draw, nx, ny, i)

    # Player on this side
    draw_player(draw, 72, 90, 'up', anim_frame)

    # Mood indicator — speech bubbles / atmosphere
    if mood == 'good':
        # Green positive indicators
        col = GB_DARKEST
        if talking_frame % 8 < 4:
            # Speech lines from NPCs
            speaker = talking_frame % 3
            sx, sy = npc_positions[speaker]
            draw.line([(sx+4, sy-4), (sx+4, sy-8)], fill=col, width=1)
            draw.line([(sx+2, sy-6), (sx+6, sy-6)], fill=col, width=1)
    elif mood == 'nervous':
        # Red-ish nervous indicators
        col = GB_RED if hasattr(draw, '_no_') else GB_DARKEST  # fallback
        # Sweat drops near player
        if anim_frame % 4 < 2:
            pixel(draw, 68, 88, GB_DARKEST)
            pixel(draw, 80, 87, GB_DARKEST)
        # Exclamation
        draw.text((66, 82), "!", font=FONT_3, fill=GB_DARKEST)
    elif mood == 'challenge':
        # Technical challenge — code on whiteboard intensifies
        rect(draw, 50, 16, 60, 24, GB_LIGHTEST)
        draw.rectangle([(50, 16), (109, 39)], outline=GB_DARKEST)
        for i in range(6):
            lw = random.randint(15, 50)
            draw.line([(53 + random.randint(0,10), 18+i*3), (53+lw, 18+i*3)], fill=GB_DARKEST, width=1)

    # Door
    rect(draw, GBW-14, 60, 10, 18, GB_DARKEST)

    draw_location_label(draw, "MEETING ROOM - FLOOR 7")
    return img

def scene_bathroom(anim_frame):
    img = gb_frame()
    draw = ImageDraw.Draw(img)

    rect(draw, 0, 12, GBW, GBH-12, GB_LIGHT)
    rect(draw, 0, 12, GBW, 4, GB_DARK)

    # Mirror
    rect(draw, 50, 18, 60, 30, GB_LIGHTEST)
    draw.rectangle([(50, 18), (109, 47)], outline=GB_DARKEST)

    # Sink
    rect(draw, 60, 48, 40, 10, GB_DARK)
    rect(draw, 70, 50, 20, 4, GB_LIGHTEST)

    # Player reflection in mirror (simple)
    rect(draw, 76, 26, 6, 8, GB_DARK)

    # Player
    draw_player(draw, 74, 65, 'up', anim_frame)

    # Deep breath indicators
    if anim_frame % 8 < 4:
        draw.text((62, 58), "...", font=FONT_3, fill=GB_DARKEST)

    draw_location_label(draw, "BATHROOM")
    return img

# ══════════════════════════════════════════════════════════════════
# ANIMATION SEQUENCES
# ══════════════════════════════════════════════════════════════════

print("Scene 1: Collins Street — finding the building")
# Walk along Collins Street from right to the building entrance
for i in range(36):
    px = 140 - i * 2.5
    py = 92 if i < 20 else 92 - (i - 20) * 1.2
    img = scene_collins_street(int(px), int(py), i)
    draw = ImageDraw.Draw(img)
    if i == 0:
        draw_dialogue_box(draw, "COLLINS ST...")
    save_frame(img)

# Arrive at door
for i in range(8):
    img = scene_collins_street(78, 72, i)
    draw = ImageDraw.Draw(img)
    if i > 3:
        draw_dialogue_box(draw, "This is it.", i % 4 < 2)
    save_frame(img)

# Flash to black (entering)
for _ in range(4):
    save_frame(gb_frame())

print("Scene 2: Lobby — walk to elevator")
for i in range(24):
    px = 78 - i * 0.5 if i < 8 else 74
    py = GBH - 20 - i * 3 if i < 8 else GBH - 44 + (i-8) * 0
    if i >= 8:
        px = 74 + (i - 8) * 4
        py = 66
    img = scene_lobby(int(px), int(py), i)
    save_frame(img)

# Reach elevator
for i in range(6):
    img = scene_lobby(GBW-34, 58, i)
    save_frame(img)

print("Scene 3: Elevator ride to floor 6")
# Doors closing
for i in range(6):
    save_frame(scene_elevator(1, 'closed', i))

# Floor counter ticking up
for floor in range(1, 7):
    for f in range(4):
        save_frame(scene_elevator(floor, 'closed', f))

# Doors opening
for i in range(6):
    save_frame(scene_elevator(6, 'opening', i))
for i in range(3):
    save_frame(scene_elevator(6, 'open', i))

# Flash
for _ in range(3):
    save_frame(gb_frame())

print("Scene 4: Floor 6 hallway — waiting")
# Walk out of elevator, sit in waiting area
for i in range(20):
    px = 16 + i * 3
    py = GBH - 30 if i < 8 else GBH - 30 - (i-8) * 2.5
    img = scene_hallway(int(px), int(py), 6, i)
    save_frame(img)

# Sitting and waiting — clock ticking feeling
for i in range(20):
    img = scene_hallway(62, 62, 6, i)
    draw = ImageDraw.Draw(img)
    if i % 10 == 0:
        draw_dialogue_box(draw, "...")
    save_frame(img)

print("Scene 5: Bathroom break #1")
for _ in range(3):
    save_frame(gb_frame())
for i in range(14):
    save_frame(scene_bathroom(i))
for _ in range(3):
    save_frame(gb_frame())

print("Scene 6: More waiting on floor 6")
for i in range(16):
    img = scene_hallway(62, 62, 6, i)
    draw = ImageDraw.Draw(img)
    if i == 8:
        draw_dialogue_box(draw, "...", True)
    save_frame(img)

print("Scene 7: Someone comes to get you")
for i in range(16):
    img = scene_hallway(62, 62, 6, i)
    draw = ImageDraw.Draw(img)
    # NPC walks in from the stairwell door
    npc_x = GBW - 24 - max(0, i - 4) * 5
    npc_y = 56
    if i >= 4:
        draw_npc(draw, int(npc_x), npc_y, 0)
    if i == 12:
        draw_dialogue_box(draw, "Hi! Follow me.")
    save_frame(img)

# Brief hold
for i in range(6):
    img = scene_hallway(62, 62, 6, i)
    draw = ImageDraw.Draw(img)
    draw_npc(draw, 75, 56, 0)
    draw_dialogue_box(draw, "Hi! Follow me.", i % 4 < 2)
    save_frame(img)

print("Scene 8: Stairwell — floor 6 to 7")
for _ in range(3):
    save_frame(gb_frame())

for i in range(24):
    py = GBH - 30 - i * 4
    save_frame(scene_stairwell(max(16, py), True, i))

# Through the door
for _ in range(4):
    save_frame(gb_frame())

print("Scene 9: Floor 7 — enter the office")
for i in range(16):
    px = 10 + i * 4
    py = 54
    img = scene_office_floor7(int(px), py, i,
                               npcs=[(25, 82), (75, 82), (115, 30), (30, 38)])
    save_frame(img)

print("Scene 10: Meeting room — the interview (longer)")
# Good start
for i in range(24):
    img = scene_meeting_room(i, 'good', i)
    save_frame(img)

# Technical challenge — whiteboard fills up
for i in range(18):
    img = scene_meeting_room(i, 'challenge', i)
    save_frame(img)

# Nervous moment — brief red
for i in range(14):
    img = scene_meeting_room(i, 'nervous', i)
    draw = ImageDraw.Draw(img)
    # Tint the background slightly darker
    save_frame(img)

# Recovery — back to good
for i in range(6):
    img = scene_meeting_room(i, 'challenge', i)
    save_frame(img)

for i in range(20):
    img = scene_meeting_room(i, 'good', i)
    draw = ImageDraw.Draw(img)
    if i == 16:
        draw_dialogue_box(draw, "Great answer.")
    save_frame(img)

# More good talking
for i in range(16):
    img = scene_meeting_room(i, 'good', i)
    save_frame(img)

print("Scene 11: Bathroom break #2")
for _ in range(3):
    save_frame(gb_frame())
for i in range(10):
    save_frame(scene_bathroom(i))
for _ in range(3):
    save_frame(gb_frame())

print("Scene 12: Office tour — floor 7")
# 2 NPCs walk you around
tour_npcs = [
    (25, 82), (75, 82), (115, 30), (30, 38),  # desk people
    (50, 50), (100, 55),  # hallway people
]
for i in range(28):
    px = 50 + int(math.sin(i * 0.2) * 30)
    py = 50 + int(math.cos(i * 0.15) * 20)
    # Guide NPCs move ahead
    guide1_x = px + 16
    guide1_y = py - 4
    guide2_x = px + 8
    guide2_y = py - 12
    all_npcs = tour_npcs + [(guide1_x, guide1_y), (guide2_x, guide2_y)]

    img = scene_office_floor7(px, py, i, npcs=all_npcs, wave=(i > 10))
    save_frame(img)

# People waving
for i in range(10):
    img = scene_office_floor7(80, 50, i,
                               npcs=[(25, 82), (75, 82), (115, 30), (30, 38), (50, 55), (100, 55)],
                               wave=True)
    save_frame(img)

print("Scene 13: Back to elevator — down to ground")
for _ in range(4):
    save_frame(gb_frame())

# Elevator going down
for floor in range(7, 0, -1):
    for f in range(3):
        save_frame(scene_elevator(floor, 'closed', f))

# Doors open on ground floor
for i in range(4):
    save_frame(scene_elevator(1, 'opening', i))

for _ in range(3):
    save_frame(gb_frame())

print("Scene 14: Exit onto Collins Street")
# Lobby walk out
for i in range(12):
    px = GBW - 34 - i * 6
    py = 66 + i * 2
    img = scene_lobby(int(max(30, px)), int(min(GBH-16, py)), i)
    save_frame(img)

for _ in range(3):
    save_frame(gb_frame())

# Back on Collins Street — walking away
for i in range(24):
    px = 82 + i * 2.2
    py = 78 + min(14, i)
    img = scene_collins_street(int(min(148, px)), int(min(94, py)), i)
    draw = ImageDraw.Draw(img)
    if i == 18:
        draw_dialogue_box(draw, "Done. Deep breath.", True)
    save_frame(img)

# Hold on street
for i in range(12):
    img = scene_collins_street(148, 94, i)
    save_frame(img)

# Fade to GB darkest
for i in range(12):
    img = scene_collins_street(148, 94, i)
    factor = 1.0 - i / 12.0
    img = ImageEnhance.Brightness(img).enhance(factor)
    save_frame(img)

# End card
for i in range(18):
    img = gb_frame()
    draw = ImageDraw.Draw(img)
    rect(draw, 0, 0, GBW, GBH, GB_DARKEST)
    a_col = GB_LIGHT if i > 4 else GB_DARK
    draw.text((GBW//2-28, GBH//2-12), "ClawdJob", font=FONT_5, fill=a_col)
    if i > 8:
        draw.text((GBW//2-14, GBH//2+4), "2026", font=FONT_3, fill=GB_DARK)
    save_frame(img)

for _ in range(8):
    img = gb_frame()
    draw = ImageDraw.Draw(img)
    rect(draw, 0, 0, GBW, GBH, GB_DARKEST)
    save_frame(img)

print(f"Total frames: {frame_num}")
print(f"Duration: {frame_num / FPS:.1f}s")

# ── Audio: Chiptune GameBoy style ──────────────────────────────────
print("Generating chiptune audio...")
AUDIO_PATH = os.path.join(OUT_DIR, "audio.wav")
SAMPLE_RATE = 22050
duration_sec = frame_num / FPS + 0.5
num_samples = int(SAMPLE_RATE * duration_sec)

def square_wave(t, freq, duty=0.5):
    """Classic GameBoy square wave"""
    phase = (t * freq) % 1.0
    return 1.0 if phase < duty else -1.0

def noise(t):
    """Pseudo-noise for GB percussion"""
    return random.random() * 2 - 1

samples = []
beat_len = 0.25  # 120 BPM feel

# Simple GB melody — pentatonic, looping
melody_notes = [
    262, 294, 330, 392, 440,  # C D E G A
    440, 392, 330, 294, 262,
    330, 392, 440, 524, 440,
    392, 330, 262, 294, 330,
]
bass_notes = [
    131, 131, 165, 165,
    131, 131, 196, 196,
    131, 131, 165, 165,
    196, 196, 131, 131,
]

for s in range(num_samples):
    t = s / SAMPLE_RATE
    beat = int(t / beat_len)

    # Lead — square wave, 25% duty (classic GB)
    note_idx = beat % len(melody_notes)
    lead_freq = melody_notes[note_idx]
    # Slight vibrato
    lead_freq += math.sin(t * 6) * 2
    val = square_wave(t, lead_freq, 0.25) * 0.08

    # Bass — square wave, 50% duty
    bass_idx = (beat // 2) % len(bass_notes)
    bass_freq = bass_notes[bass_idx]
    val += square_wave(t, bass_freq, 0.5) * 0.06

    # Arpeggio layer — fast arps
    arp_notes = [262, 330, 392]
    arp_idx = int(t / 0.08) % len(arp_notes)
    val += square_wave(t, arp_notes[arp_idx], 0.125) * 0.03

    # Percussion — noise on beats
    beat_phase = (t % beat_len) / beat_len
    if beat_phase < 0.05:
        val += noise(t) * 0.12 * (1 - beat_phase / 0.05)
    # Hi-hat on offbeats
    offbeat_phase = ((t + beat_len/2) % beat_len) / beat_len
    if offbeat_phase < 0.02:
        val += noise(t) * 0.04

    # Fade in/out
    if t < 1.0:
        val *= t
    if t > duration_sec - 2.0:
        val *= max(0, (duration_sec - t) / 2.0)

    # Low-pass approximation (simple averaging would need state, just clamp)
    val = max(-0.95, min(0.95, val))
    samples.append(int(val * 32767))

with open(AUDIO_PATH, 'wb') as f:
    data_size = num_samples * 2
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36 + data_size))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<IHHIIHH', 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16))
    f.write(b'data')
    f.write(struct.pack('<I', data_size))
    for s_val in samples:
        f.write(struct.pack('<h', s_val))

print("Audio generated.")

# ── Render ─────────────────────────────────────────────────────────
print("Rendering video with ffmpeg...")
cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(OUT_DIR, "frame_%05d.png"),
    "-i", AUDIO_PATH,
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "128k",
    "-shortest",
    "-movflags", "+faststart",
    FINAL
]
subprocess.run(cmd, check=True)
print(f"Done! Video saved to {FINAL}")
