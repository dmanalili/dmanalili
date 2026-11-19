#!/usr/bin/env python3
"""Conway's Game of Life on a contribution-graph grid, as animated SVGs.

    python3 life.py          # writes assets/life-light.svg and assets/life-dark.svg

The output is plain SVG with SMIL animation, so it plays inside a GitHub README
(no JavaScript, web fonts or external images).
"""
import datetime
import html
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "assets")

# Contribution-graph layout: 53 weeks x 7 days of 10px squares.
W, H = 53, 7
N = W * H
CELL, GAP = 10, 3
P = CELL + GAP
PAD = 16
GRID_X = PAD + 32
GRID_Y = PAD + 50
GRID_W = W * P - GAP
GRID_H = H * P - GAP
SVG_W = GRID_X + GRID_W + PAD
SVG_H = GRID_Y + GRID_H + 40
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
ABBR = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
THIS_MONTH = datetime.date.today().month
MONTHS = [ABBR[(THIS_MONTH + k) % 12] for k in range(12)]  # last 12 months, oldest first

THEMES = {
    "light": dict(l0="#eff2f5", l1="#aceebb", l2="#4ac26b", l3="#2da44e", l4="#116329",
                  live="#2da44e", text="#1f2328", muted="#59636e", border="#d1d9e0"),
    "dark": dict(l0="#151b23", l1="#033a16", l2="#196c2e", l3="#2ea043", l4="#56d364",
                 live="#3fb950", text="#f0f6fc", muted="#9198a1", border="#3d444d"),
}

# The visible 53x7 strip is a window onto a taller wrapping world, so patterns
# drift in and out instead of wrapping into stripes on a 7-row board.
WORLD_H, WIN_Y = 21, 7
WN = W * WORLD_H
NB = []
for _i in range(WN):
    _x, _y = _i % W, _i // W
    NB.append([((_y + dy) % WORLD_H) * W + (_x + dx) % W
               for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy])

GENS = 150
SEED = 4  # the liveliest of seeds 0-59; any seed works


def num(v, prec=4):
    """Compact number for SVG attributes: 0.4500 -> .45, 13.0 -> 13."""
    s = f"{v:.{prec}f}".rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    return s or "0"


def timeline(events, prec=4):
    """events: (fraction 0..1, value) -> (keyTimes, values) for a discrete SMIL animate."""
    merged = []
    for t, v in sorted(events, key=lambda e: e[0]):
        if merged and abs(merged[-1][0] - t) < 1e-9:
            merged[-1] = (t, v)
        else:
            merged.append((t, v))
    out = []
    for t, v in merged:
        if out and out[-1][1] == v:
            continue
        out.append((t, v))
    return ";".join(num(t, prec) for t, _ in out), ";".join(num(v) for _, v in out), len(out)


def anim(attr, dur, events, prec=4):
    kt, vs, n = timeline(events, prec)
    return (f'<animate attributeName="{attr}" dur="{num(dur)}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{kt}" values="{vs}"/>'), n


def life_step(g):
    out = []
    for i, nb in enumerate(NB):
        s = g[nb[0]] + g[nb[1]] + g[nb[2]] + g[nb[3]] + g[nb[4]] + g[nb[5]] + g[nb[6]] + g[nb[7]]
        out.append(1 if s == 3 or (s == 2 and g[i]) else 0)
    return out


def life_run(seed):
    """Random soup; when the world settles, drop in a little noise so it keeps going."""
    rnd = random.Random(seed)
    g = [1 if rnd.random() < 0.33 else 0 for _ in range(WN)]
    world = [g]
    quiet = 0
    for _ in range(GENS - 1):
        nxt = life_step(g)
        changed = sum(a != b for a, b in zip(g, nxt))
        quiet = quiet + 1 if (changed < 12 or nxt in world[-4:]) else 0
        if quiet >= 5:
            cx, cy = rnd.randrange(W), rnd.randrange(WORLD_H)
            for dy in range(4):
                for dx in range(5):
                    if rnd.random() < 0.5:
                        nxt[((cy + dy) % WORLD_H) * W + (cx + dx) % W] = 1
            quiet = 0
        world.append(nxt)
        g = nxt
    return [w[WIN_Y * W:(WIN_Y + H) * W] for w in world]


def frame(theme, body):
    """The contribution-graph card: border, labels, empty squares, legend."""
    c = THEMES[theme]
    css = (
        f"text{{font-family:{FONT};font-size:12px;fill:{c['muted']}}}"
        f".h{{font-size:16px;fill:{c['text']}}}"
        f".e{{fill:{c['l0']}}}.g1{{fill:{c['l1']}}}.g2{{fill:{c['l2']}}}"
        f".g3{{fill:{c['l3']}}}.g4{{fill:{c['l4']}}}.lv{{fill:{c['live']}}}"
    )
    title = "Game of Life on a contribution graph"
    desc = ("Green squares on a contribution-graph grid, born and dying by the rules of "
            "Conway's Game of Life, on a loop.")
    caption = "Conway's Game of Life"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" role="img" aria-labelledby="t d">',
        f'<title id="t">{html.escape(title)}</title><desc id="d">{html.escape(desc)}</desc>',
        f"<style>{css}</style>",
        f'<defs><rect id="q" width="{CELL}" height="{CELL}" rx="2"/>'
        f'<clipPath id="clip"><rect width="{GRID_W}" height="{GRID_H}"/></clipPath></defs>',
        f'<rect x=".5" y=".5" width="{SVG_W - 1}" height="{SVG_H - 1}" rx="6" fill="none" stroke="{c["border"]}"/>',
        f'<text class="h" x="{PAD}" y="{PAD + 16}">∞ contributions in the last year</text>',
    ]
    for i, m in enumerate(MONTHS):
        x = GRID_X + round(i * W / 12 + 1.5) * P
        out.append(f'<text x="{x}" y="{GRID_Y - 8}">{m}</text>')
    for row, day in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{PAD}" y="{GRID_Y + row * P + 9}">{day}</text>')
    empty = "".join(f'<use href="#q" x="{x * P}" y="{y * P}"/>' for y in range(H) for x in range(W))
    out.append(f'<g class="e" transform="translate({GRID_X},{GRID_Y})">{empty}</g>')
    out.append(f'<g transform="translate({GRID_X},{GRID_Y})"><g clip-path="url(#clip)">{body}</g></g>')
    ly = GRID_Y + GRID_H + 14
    right = SVG_W - PAD
    out.append(f'<text x="{PAD}" y="{ly + 9}">{html.escape(caption)}</text>')
    out.append(f'<text x="{right}" y="{ly + 9}" text-anchor="end">More</text>')
    sx = right - 34 - (5 * P - GAP)
    for k, cls in enumerate(("e", "g1", "g2", "g3", "g4")):
        out.append(f'<use href="#q" class="{cls}" x="{sx + k * P}" y="{ly}"/>')
    out.append(f'<text x="{sx - 6}" y="{ly + 9}" text-anchor="end">Less</text>')
    out.append("</svg>")
    return "".join(out)


def life_svg(theme, gens):
    INTRO, GEN, OUTRO, PAUSE = 1.0, 0.2, 0.9, 0.5
    T = INTRO + GENS * GEN + OUTRO + PAUSE
    last = [-99] * N
    vals = []
    for g, state in enumerate(gens):
        row = []
        for i in range(N):
            if state[i]:
                last[i] = g
                row.append(1)
            else:
                row.append(0.4 if g - last[i] == 1 else 0)  # just died: leave a ghost
        vals.append(row)
    end = INTRO + GENS * GEN
    cells = []
    for i in range(N):
        x, y = i % W, i // W
        ev = [(0.0, 0)]
        if gens[0][i]:
            ev.append((INTRO * 0.85 * x / (W - 1), 1))  # wipe in from the left
        for g in range(1, GENS):
            ev.append((INTRO + g * GEN, vals[g][i]))
        ev.append((end, 0.4 if vals[-1][i] else 0))
        ev.append((end + OUTRO * 0.6, 0))
        a, n = anim("opacity", T, [(t / T, val) for t, val in ev], prec=3)
        if n <= 1:
            continue
        cells.append(f'<use href="#q" x="{x * P}" y="{y * P}" opacity="{gens[0][i]}">{a}</use>')
    return frame(theme, f'<g class="lv">{"".join(cells)}</g>')


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gens = life_run(SEED)
    for theme in THEMES:
        path = os.path.join(OUT, f"life-{theme}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(life_svg(theme, gens))
        print(path)
