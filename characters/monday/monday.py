"""MONDAY (マンデー) — idle pose, AI Virtual Office.

Pure-vector drawing (pycairo) so the same code exports:
  monday_idle.png   1024x1024 RGBA, transparent, ~15% margin
  monday_idle.svg   resolution-independent vector version
  parts/*.png       separated rig layers (same 1024 canvas) for web animation
Run:  python3.13 characters/monday/monday.py
"""
import math
import pathlib
import sys

import cairo

OUT = pathlib.Path(__file__).resolve().parent
S = 1024

# ---- palette (sampled / matched to the confirmed character sheet) ----
INK = (0.33, 0.21, 0.13)          # warm dark-brown outline
INK_SOFT = (0.50, 0.34, 0.22)
BODY = (0.93, 0.84, 0.69)         # cream
BODY_LIGHT = (0.97, 0.92, 0.80)
BODY_SHADE = (0.82, 0.68, 0.50)
BODY_DEEP = (0.70, 0.55, 0.38)
EYE_Y = (0.98, 0.80, 0.18)
EYE_Y_DARK = (0.88, 0.62, 0.10)
EYE_RIM = (0.62, 0.38, 0.10)
PUPIL = (0.10, 0.07, 0.06)
MOUTH = (0.55, 0.16, 0.14)
TONGUE = (0.90, 0.42, 0.38)
TIE = (0.17, 0.33, 0.68)
TIE_DARK = (0.10, 0.20, 0.47)
TIE_LIGHT = (0.33, 0.52, 0.86)
TIE_INK = (0.07, 0.12, 0.30)


def rgba(c, a=1.0):
    return (*c, a)


# ---------------------------------------------------------------- path helpers
def smooth(ctx, pts, closed=True, tension=1.0):
    """Catmull-Rom spline through pts -> cubic beziers."""
    n = len(pts)
    P = pts
    rng = range(n) if closed else range(n - 1)
    ctx.move_to(*P[0])
    for i in rng:
        p0 = P[(i - 1) % n] if closed or i > 0 else P[i]
        p1 = P[i]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed or i + 2 < n else P[(i + 1) % n]
        k = tension / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        ctx.curve_to(*c1, *c2, *p2)
    if closed:
        ctx.close_path()


def fill_stroke(ctx, fill, lw=6.0, ink=INK):
    ctx.set_source(fill) if isinstance(fill, cairo.Pattern) else ctx.set_source_rgba(*rgba(fill))
    ctx.fill_preserve()
    ctx.set_source_rgba(*rgba(ink))
    ctx.set_line_width(lw)
    ctx.stroke()


def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c, a in stops:
        g.add_color_stop_rgba(o, *c, a)
    return g


def rad(cx, cy, r0, r1, stops, fx=None, fy=None):
    g = cairo.RadialGradient(cx if fx is None else fx, cy if fy is None else fy, r0, cx, cy, r1)
    for o, c, a in stops:
        g.add_color_stop_rgba(o, *c, a)
    return g


# ---------------------------------------------------------------- geometry
# Puddle (melted base) — lobed outline
PUDDLE = [(168, 838), (190, 806), (238, 790), (262, 770), (300, 776), (330, 790), (372, 786),
          (420, 796), (470, 792), (520, 800), (575, 794), (630, 800), (690, 792), (734, 778),
          (770, 772), (800, 788), (842, 798), (864, 826), (846, 852), (790, 860), (735, 852),
          (690, 862), (628, 856), (566, 864), (500, 858), (430, 866), (360, 858), (296, 864),
          (236, 856), (190, 858)]

# Body: half-melted rounded block. Front contour (clockwise from top-left)
BODY_PTS = [(288, 268), (400, 252), (512, 248), (624, 252), (736, 268), (780, 306),
            (794, 400), (800, 500), (806, 590), (818, 660), (846, 712), (862, 752),
            (826, 776), (782, 766), (752, 792), (708, 780), (668, 800), (620, 790),
            (562, 804), (500, 796), (440, 806), (386, 790), (342, 804), (298, 780),
            (254, 770), (190, 754), (202, 712), (220, 660), (230, 590), (232, 500),
            (236, 400), (248, 306)]

# crease between top face and front face
TOP_CREASE = [(240, 344), (340, 326), (512, 320), (684, 326), (790, 344)]

EYE_L = (410, 504)
EYE_R = (614, 504)
EYE_RX, EYE_RY = 96, 90


def body_path(ctx):
    smooth(ctx, BODY_PTS)


def puddle_path(ctx):
    smooth(ctx, PUDDLE)


# ---------------------------------------------------------------- layers
def draw_puddle(ctx):
    puddle_path(ctx)
    g = lin(0, 770, 0, 866, [(0, BODY, 1), (0.6, BODY_SHADE, 1), (1, BODY_DEEP, 1)])
    fill_stroke(ctx, g, 6)
    # gloss on puddle lobes
    ctx.save()
    puddle_path(ctx)
    ctx.clip()
    ctx.set_source_rgba(1, 1, 1, 0.55)
    for (x, y, w) in [(214, 818, 38), (300, 806, 30), (760, 806, 34), (826, 820, 22)]:
        ctx.save(); ctx.translate(x, y); ctx.scale(w, 6); ctx.arc(0, 0, 1, math.pi, 2 * math.pi)
        ctx.restore(); ctx.set_line_width(4); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.restore()


def draw_body(ctx):
    # base fill with vertical gradient (top lighter, bottom warmer)
    body_path(ctx)
    g = lin(0, 200, 0, 800, [(0, BODY_LIGHT, 1), (0.35, BODY, 1), (0.8, BODY, 1), (1, BODY_SHADE, 1)])
    ctx.set_source(g)
    ctx.fill()
    ctx.save()
    body_path(ctx)
    ctx.clip()
    # side shading (right side in shadow, left catches light)
    ctx.set_source(lin(220, 0, 820, 0, [(0, BODY_SHADE, 0.35), (0.18, BODY_SHADE, 0.0), (0.78, BODY_SHADE, 0.0), (1, BODY_DEEP, 0.55)]))
    ctx.paint()
    # top face: lighter slab above crease
    smooth(ctx, [(236, 344)] + BODY_PTS[0:6] + [(794, 344)] + TOP_CREASE[::-1][1:-1], closed=True)
    ctx.set_source_rgba(*BODY_LIGHT, 0.75)
    ctx.fill()
    # crease line (soft)
    smooth(ctx, TOP_CREASE, closed=False)
    ctx.set_source_rgba(*BODY_SHADE, 0.9)
    ctx.set_line_width(5)
    ctx.stroke()
    # melting drips running down the front, darker undersides
    for (x, y0, y1, w) in [(270, 640, 758, 20), (330, 700, 790, 14), (700, 690, 786, 16), (768, 630, 762, 18), (600, 730, 798, 12)]:
        ctx.save()
        smooth(ctx, [(x - w, y0), (x - w * 0.8, (y0 + y1) / 2), (x - w * 0.9, y1 - w), (x, y1), (x + w * 0.9, y1 - w), (x + w * 0.8, (y0 + y1) / 2), (x + w, y0)], closed=True)
        ctx.set_source(lin(0, y0, 0, y1, [(0, BODY, 0), (0.5, BODY, 0.6), (1, BODY_LIGHT, 0.9)]))
        ctx.fill_preserve()
        ctx.set_source(lin(0, y0, 0, y1, [(0, BODY_DEEP, 0), (1, BODY_DEEP, 0.55)]))
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.restore()
    # glossy highlights (top-left)
    ctx.set_source_rgba(1, 1, 1, 0.65)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    smooth(ctx, [(300, 284), (380, 268), (460, 262)], closed=False)
    ctx.set_line_width(10); ctx.stroke()
    smooth(ctx, [(256, 370), (250, 420), (250, 470)], closed=False)
    ctx.set_source_rgba(1, 1, 1, 0.45); ctx.set_line_width(9); ctx.stroke()
    ctx.arc(490, 262, 6, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.7); ctx.fill()
    # bottom occlusion toward puddle
    ctx.set_source(lin(0, 700, 0, 810, [(0, BODY_DEEP, 0), (1, BODY_DEEP, 0.45)]))
    ctx.paint()
    ctx.restore()
    # outline
    body_path(ctx)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(6.5)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def eye_socket(ctx, cx, cy, side):
    """Bulging eye dome + heavy sleepy bags (skin)."""
    rx, ry = EYE_RX + 22, EYE_RY + 24
    ctx.save(); ctx.translate(cx, cy - 6); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    g = rad(cx - 20 * side, cy - 60, 10, rx * 1.25, [(0, BODY_LIGHT, 1), (0.65, BODY, 1), (1, BODY_SHADE, 0.0)])
    ctx.set_source(g); ctx.fill()
    # brow ridge: upper arc of the bulging dome
    ctx.save(); ctx.translate(cx, cy - 6); ctx.scale(rx, ry)
    a0, a1 = (math.radians(198), math.radians(318)) if side < 0 else (math.radians(222), math.radians(342))
    ctx.arc(0, 0, 1, a0, a1); ctx.restore()
    ctx.set_source_rgba(*INK, 0.9); ctx.set_line_width(5); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    # under-eye bags (two tired creases)
    smooth(ctx, [(cx - 78, cy + 84), (cx, cy + 106), (cx + 78, cy + 84)], closed=False)
    ctx.set_source_rgba(*INK_SOFT, 0.75); ctx.set_line_width(3.5); ctx.stroke()
    smooth(ctx, [(cx - 50, cy + 112), (cx + 6 * side, cy + 124), (cx + 54, cy + 110)], closed=False)
    ctx.set_source_rgba(*INK_SOFT, 0.4); ctx.set_line_width(3); ctx.stroke()


def eye_ball(ctx, cx, cy, side, look=(0, 0)):
    ctx.save(); ctx.translate(cx, cy); ctx.scale(EYE_RX, EYE_RY); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    g = rad(cx - 18 * side, cy - 20, 6, EYE_RX * 1.05, [(0, (1.0, 0.90, 0.40), 1), (0.6, EYE_Y, 1), (1, EYE_Y_DARK, 1)])
    fill_stroke(ctx, g, 5, EYE_RIM)


def pupil(ctx, cx, cy, side, look=(0, 0)):
    px, py = cx + 4 * side + look[0] * 14, cy - 16 + look[1] * 10
    ctx.save(); ctx.translate(px, py); ctx.scale(40, 38); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgba(*PUPIL); ctx.fill()
    ctx.arc(px - 14, py + 14, 8, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.95); ctx.fill()
    ctx.arc(px + 16, py + 24, 4, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.7); ctx.fill()


def _lid_edge(cx, cy, side, close, closed_y):
    """Lid edge y-values (inner, middle, outer) — open: droopy sleepy line; closed: given level."""
    lerp = lambda a, b: a + (b - a) * close
    return (lerp(cy - 40, cy + closed_y), lerp(cy - 24, cy + closed_y + 14), lerp(cy - 8, cy + closed_y + 6))


def lid_path(ctx, cx, cy, side, close=0.0, closed_y=EYE_RY + 12):
    """Heavy upper eyelid covering the top of the eyeball; droops toward the outer corner."""
    inner, outer = cx - 100 * side, cx + 100 * side
    base_in, mid, base_out = _lid_edge(cx, cy, side, close, closed_y)
    ctx.move_to(inner, cy - 120); ctx.line_to(outer, cy - 120); ctx.line_to(outer + 4 * side, base_out)
    ctx.curve_to(cx + 70 * side, base_out + 6, cx + 50 * side, mid + 8, cx + 10 * side, mid + 4)
    ctx.curve_to(cx - 40 * side, mid, cx - 80 * side, base_in + 2, inner, base_in)
    ctx.close_path()


def eyelid(ctx, cx, cy, side, close=0.0):
    ctx.save()
    ctx.save(); ctx.translate(cx, cy); ctx.scale(EYE_RX + 5, EYE_RY + 5); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.clip()
    if close > 0.5:   # lower lid rises to meet the upper one: hide the eyeball below the lash line
        ctx.rectangle(cx - 120, cy - 120, 240, 240)
        ctx.set_source(lin(0, cy, 0, cy + EYE_RY, [(0, BODY, min(1, (close - 0.5) * 4)), (1, BODY_LIGHT, min(1, (close - 0.5) * 4))]))
        ctx.fill()
    lash = _lid_edge(cx, cy, side, close, 30)
    lid_path(ctx, cx, cy, side, close, closed_y=30)
    edge = max(lash)
    ctx.set_source(lin(0, cy - 90, 0, edge + 4, [(0, BODY_LIGHT, 1), (0.8, BODY, 1), (1, BODY_SHADE, 1)]))
    ctx.fill()
    ctx.restore()
    # lash line: follows the lid edge while open, settles into a soft "sleeping" arc when closed
    inner, outer = cx - 100 * side, cx + 100 * side
    base_in, mid, base_out = lash
    ctx.save()
    ctx.save(); ctx.translate(cx, cy); ctx.scale(EYE_RX + 6, EYE_RY + 6); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.clip()
    ctx.move_to(inner, base_in)
    ctx.curve_to(cx - 80 * side, base_in + 2, cx - 40 * side, mid, cx + 10 * side, mid + 4)
    ctx.curve_to(cx + 50 * side, mid + 8, cx + 70 * side, base_out + 6, outer + 4 * side, base_out)
    ctx.set_source_rgba(*INK); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.restore()
    # crease above lid (tired fold)
    smooth(ctx, [(cx - 66 * side, cy - 66), (cx + 10 * side, cy - 72), (cx + 74 * side, cy - 52)], closed=False)
    ctx.set_source_rgba(*INK_SOFT, 0.75); ctx.set_line_width(3.5); ctx.stroke()


def draw_eyes(ctx, close=0.0, look=(0, 0)):
    for (cx, cy), side in ((EYE_L, -1), (EYE_R, 1)):
        eye_socket(ctx, cx, cy, side)
    for (cx, cy), side in ((EYE_L, -1), (EYE_R, 1)):
        eye_ball(ctx, cx, cy, side)
        ctx.save()
        ctx.save(); ctx.translate(cx, cy); ctx.scale(EYE_RX - 2, EYE_RY - 2); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.clip()
        pupil(ctx, cx, cy, side, look)
        ctx.restore()
        eyelid(ctx, cx, cy, side, close)


def draw_mouth(ctx):
    cx, cy = 512, 600
    smooth(ctx, [(cx - 18, cy - 4), (cx, cy - 12), (cx + 18, cy - 4), (cx + 12, cy + 16), (cx, cy + 22), (cx - 12, cy + 16)])
    fill_stroke(ctx, MOUTH, 4, INK)
    ctx.save(); smooth(ctx, [(cx - 18, cy - 4), (cx, cy - 12), (cx + 18, cy - 4), (cx + 12, cy + 16), (cx, cy + 22), (cx - 12, cy + 16)]); ctx.clip()
    ctx.arc(cx + 2, cy + 22, 13, 0, 2 * math.pi); ctx.set_source_rgba(*TONGUE); ctx.fill()
    ctx.restore()
    # tiny nose/philtrum bump between eyes
    smooth(ctx, [(cx - 14, cy - 34), (cx, cy - 40), (cx + 14, cy - 34)], closed=False)
    ctx.set_source_rgba(*INK_SOFT, 0.7); ctx.set_line_width(3); ctx.stroke()


def tie_blade_path(ctx):
    """Long tie: hangs from the knot, slumps onto the floor and lies there, pointed tip forward."""
    ctx.move_to(492, 650)
    ctx.curve_to(510, 646, 526, 646, 536, 650)            # under the knot
    ctx.curve_to(548, 700, 556, 750, 574, 786)            # right edge down
    ctx.curve_to(596, 806, 650, 810, 708, 816)            # bend onto the floor
    ctx.line_to(772, 838)                                 # upper edge to the point
    ctx.line_to(716, 862)                                 # lower edge back from the point
    ctx.curve_to(640, 868, 560, 866, 506, 858)            # underside on the floor
    ctx.curve_to(466, 850, 448, 826, 452, 792)            # rounded fold at the bend
    ctx.curve_to(456, 750, 470, 700, 492, 650)            # left edge up
    ctx.close_path()


def draw_tie(ctx):
    # blade
    tie_blade_path(ctx)
    g = lin(460, 0, 720, 0, [(0, TIE_LIGHT, 1), (0.35, TIE, 1), (1, TIE_DARK, 1)])
    fill_stroke(ctx, g, 6, TIE_INK)
    ctx.save()
    tie_blade_path(ctx)
    ctx.clip()
    # fold where the tie meets the floor
    smooth(ctx, [(458, 808), (520, 812), (590, 806), (650, 814)], closed=False)
    ctx.set_source_rgba(*TIE_INK, 0.55); ctx.set_line_width(4); ctx.stroke()
    # centre crease of the floor part, leading to the point
    ctx.move_to(560, 838); ctx.curve_to(640, 840, 700, 840, 770, 838)
    ctx.set_source_rgba(*TIE_DARK, 0.5); ctx.set_line_width(3); ctx.stroke()
    ctx.set_source(lin(0, 800, 0, 866, [(0, TIE_DARK, 0.0), (1, TIE_DARK, 0.6)]))
    ctx.paint()
    # diagonal stripes (subtle) and highlight
    ctx.set_source_rgba(1, 1, 1, 0.16); ctx.set_line_width(10)
    for k in range(-6, 8):
        ctx.move_to(440 + k * 46, 600); ctx.line_to(440 + k * 46 + 160, 870); ctx.stroke()
    smooth(ctx, [(498, 680), (492, 730), (486, 780)], closed=False)
    ctx.set_source_rgba(1, 1, 1, 0.45); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.restore()
    # knot
    knot = [(482, 618), (512, 610), (544, 618), (540, 646), (528, 664), (498, 664), (486, 646)]
    smooth(ctx, knot)
    g = lin(482, 610, 540, 664, [(0, TIE_LIGHT, 1), (0.5, TIE, 1), (1, TIE_DARK, 1)])
    fill_stroke(ctx, g, 6, TIE_INK)
    smooth(ctx, [(494, 624), (512, 620), (528, 626)], closed=False)
    ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(4); ctx.stroke()


def draw_face_shading(ctx):
    """Soft cheek/socket ambient occlusion under the eyes (inside body)."""
    ctx.save(); body_path(ctx); ctx.clip()
    for (cx, cy) in (EYE_L, EYE_R):
        ctx.set_source(rad(cx, cy + 40, 30, 150, [(0, BODY_SHADE, 0.45), (1, BODY_SHADE, 0)]))
        ctx.paint()
    ctx.set_source(rad(512, 640, 10, 90, [(0, BODY_DEEP, 0.4), (1, BODY_DEEP, 0)]))
    ctx.paint()
    ctx.restore()


LAYERS = {
    "puddle": lambda c: draw_puddle(c),
    "body": lambda c: (draw_body(c), draw_face_shading(c)),
    "eyes": lambda c: draw_eyes(c),
    "mouth": lambda c: draw_mouth(c),
    "tie": lambda c: draw_tie(c),
}


CENTER_SHIFT = (0, -44)   # centres the figure: ~15% transparent margin on every side


def draw_all(ctx, close=0.0, look=(0, 0)):
    ctx.translate(*CENTER_SHIFT)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    draw_puddle(ctx)
    draw_body(ctx)
    draw_face_shading(ctx)
    draw_eyes(ctx, close, look)
    draw_mouth(ctx)
    draw_tie(ctx)


def render_png(path, fn=draw_all, **kw):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    fn(ctx, **kw)
    surf.write_to_png(str(path))


def render_svg(path):
    surf = cairo.SVGSurface(str(path), S, S)
    ctx = cairo.Context(surf)
    draw_all(ctx)
    surf.finish()


if __name__ == "__main__":
    render_png(OUT / "monday_idle.png")
    render_svg(OUT / "monday_idle.svg")
    print("ok")


# ---------------------------------------------------------------- rig parts & idle loop
BASE_Y = 800  # ground line (pre-shift) used as the squash/stretch anchor


def _part(fn):
    def run(ctx):
        ctx.translate(*CENTER_SHIFT)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        fn(ctx)
    return run


PARTS = {
    "01_puddle": _part(draw_puddle),
    "02_body": _part(lambda c: (draw_body(c), draw_face_shading(c))),
    "03_eyes_open": _part(lambda c: draw_eyes(c, 0.0)),
    "03_eyes_half": _part(lambda c: draw_eyes(c, 0.5)),
    "03_eyes_closed": _part(lambda c: draw_eyes(c, 1.0)),
    "04_mouth": _part(draw_mouth),
    "05_tie": _part(draw_tie),
}


def idle_frame(ctx, t, period=2.0):
    """Idle loop: slow breathing squash, a lazy blink, drifting pupils, tie sway."""
    ph = 2 * math.pi * t / period
    breath = math.sin(ph)
    sy, sx = 1 + 0.018 * breath, 1 - 0.012 * breath
    blink_t = (t % period) / period
    close = 0.0
    if 0.62 < blink_t < 0.78:                      # slow, heavy-lidded blink
        close = math.sin((blink_t - 0.62) / 0.16 * math.pi)
    look = (0.25 * math.sin(ph * 0.5), 0.1 * math.sin(ph))
    ctx.translate(*CENTER_SHIFT)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    draw_puddle(ctx)
    ctx.save()
    ctx.translate(512, BASE_Y); ctx.scale(sx, sy); ctx.translate(-512, -BASE_Y)
    draw_body(ctx); draw_face_shading(ctx)
    draw_eyes(ctx, max(close, 0.08 + 0.06 * (1 + breath) / 2), look)
    draw_mouth(ctx)
    ctx.save()                                     # tie hangs from the knot and sways a touch
    ctx.translate(512, 640); ctx.rotate(0.012 * math.sin(ph + 0.6)); ctx.translate(-512, -640)
    draw_tie(ctx)
    ctx.restore()
    ctx.restore()


def render_parts():
    d = OUT / "parts"
    d.mkdir(exist_ok=True)
    for name, fn in PARTS.items():
        render_png(d / f"{name}.png", fn)


def render_idle_loop(size=512, fps=24, period=2.0):
    from PIL import Image
    frames = []
    for i in range(int(fps * period)):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
        ctx = cairo.Context(surf)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        idle_frame(ctx, i / fps, period)
        buf = bytes(surf.get_data())
        im = Image.frombuffer("RGBA", (S, S), buf, "raw", "BGRA", 0, 1)
        # cairo stores premultiplied alpha -> un-premultiply for correct edges
        im = Image.frombuffer("RGBa", (S, S), im.tobytes(), "raw", "RGBa", 0, 1).convert("RGBA")
        frames.append(im.resize((size, size), Image.LANCZOS))
    frames[0].save(OUT / "monday_idle_loop.webp", save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0, quality=88, method=6)


if __name__ == "__main__" and "--all" in sys.argv:
    render_parts()
    render_idle_loop()
    print("parts + loop ok")
