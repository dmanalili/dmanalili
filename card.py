#!/usr/bin/env python3
"""Terminal-style profile card with a spinning ASCII donut, as an animated SVG.

    python3 card.py          # writes assets/card.svg

The donut is the classic donut.c torus, pre-rendered into 64 frames that CSS
flips through, so it plays inside a GitHub README (no JavaScript or web fonts).
"""
import html
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "assets")

# The lines on the right. Keep exactly 22 rows (the donut's height), and keep
# key + value of a "kv" row to 47 characters or fewer so the dot leaders fit.
CARD_INFO = [
    ("head", "dev@localhost"),
    ("kv", "OS", "macOS, Linux"),
    ("kv", "Uptime", "99.98%"),
    ("kv", "Host", "planet Earth"),
    ("kv", "Kernel", "caffeine 6.2 (stable)"),
    ("kv", "IDE", "VS Code, Claude Code"),
    ("blank",),
    ("kv", "Languages.Programming", "TypeScript, JavaScript, C#"),
    ("kv", "Languages.Real", "█" * 9),
    ("kv", "Stack.Frontend", "React"),
    ("kv", "Stack.Backend", "NestJS, .NET"),
    ("kv", "Stack.Data", "PostgreSQL, SQL Server"),
    ("blank",),
    ("sec", "Contact"),
    ("kv", "Email", "█" * 16),
    ("kv", "Location", "127.0.0.1"),
    ("kv", "Socials", "/dev/null"),
    ("blank",),
    ("sec", "Status"),
    ("kv", "Currently", "shipping quietly"),
    ("kv", "Visitors", "welcome"),
    ("prompt",),
]


def num(v, prec=4):
    """Compact number for SVG attributes: 0.4500 -> .45, 13.0 -> 13."""
    s = f"{v:.{prec}f}".rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    return s or "0"


def donut_points(A, B):
    """Projected (x, y, depth, luminance) samples of the torus rotated by A and B."""
    cA, sA, cB, sB = math.cos(A), math.sin(A), math.cos(B), math.sin(B)
    pts = []
    th = 0.0
    while th < 2 * math.pi:
        ct, st = math.cos(th), math.sin(th)
        ph = 0.0
        while ph < 2 * math.pi:
            cp, sp = math.cos(ph), math.sin(ph)
            h = ct + 2
            D = 1 / (sp * h * sA + st * cA + 5)
            t = sp * h * cA - st * sA
            pts.append((D * (cp * h * cB - t * sB), D * (cp * h * sB + t * cB), D,
                        (st * sA - sp * ct * cA) * cB - sp * ct * sA - st * cA - cp * ct * sB))
            ph += 0.02
        th += 0.07
    return pts


def donut_frames(F, cols, rows, aspect):
    """F frames of one full turn, each a list of text rows, scaled to fit cols x rows."""
    ramp = ".,-~:;=!*#$@"
    clouds = [donut_points(2 * math.pi * k / F + 0.6, 2 * math.pi * k / F) for k in range(F)]
    mx = max(abs(p[0]) for c in clouds for p in c)
    my = max(abs(p[1]) for c in clouds for p in c)
    sx = (cols / 2 - 0.6) / mx
    sy = sx / aspect
    if sy * my > rows / 2 - 0.6:
        sy = (rows / 2 - 0.6) / my
        sx = sy * aspect
    frames = []
    for cloud in clouds:
        zb = [0.0] * (cols * rows)
        buf = [" "] * (cols * rows)
        for x, y, D, L in cloud:
            cx, cy = int(cols / 2 + sx * x), int(rows / 2 + sy * y)
            if 0 <= cx < cols and 0 <= cy < rows and D > zb[cx + cols * cy]:
                zb[cx + cols * cy] = D
                n = int(8 * L)
                buf[cx + cols * cy] = ramp[n if n > 0 else 0]
        frames.append(["".join(buf[r * cols:(r + 1) * cols]).rstrip() for r in range(rows)])
    return frames


def card_svg():
    F, COLS, ROWS = 64, 44, 22
    FS, CW, LH = 14, 8.43, 20
    X0, Y0 = 26, 34
    LINE = 54
    RX = round(X0 + COLS * CW + 22)
    WIDTH = round(RX + LINE * CW + 26)
    HEIGHT = Y0 + (ROWS - 1) * LH + 26
    FD = 0.075
    T = F * FD
    assert len(CARD_INFO) == ROWS, f"CARD_INFO needs exactly {ROWS} rows"
    frames = donut_frames(F, COLS, ROWS, LH / CW)
    css = (
        "text{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',"
        f"'DejaVu Sans Mono',monospace;font-size:{FS}px;fill:#c9d1d9;white-space:pre}}"
        ".d{fill:url(#dg)}.k{fill:#ffa657}.v{fill:#a5d6ff}.m{fill:#6e7681}.r{fill:#8b949e}"
        ".w{fill:#f0f6fc;font-weight:600}"
        f".f{{opacity:0;animation:fr {num(T)}s steps(1,end) infinite}}"
        f"@keyframes fr{{0%{{opacity:1}}{num(100 / F)}%{{opacity:0}}}}"
        ".cur{animation:bl 1.1s steps(1,end) infinite}@keyframes bl{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.f{animation:none}.f0{opacity:1}.cur{animation:none}}"
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="t d">',
        '<title id="t">Terminal card</title><desc id="d">A terminal-style profile card with a spinning '
        "ASCII donut and a list of generic system details, with the contact lines redacted.</desc>",
        f"<style>{css}</style>",
        f'<defs><linearGradient id="dg" gradientUnits="userSpaceOnUse" x1="{X0}" y1="{Y0 - 14}" '
        f'x2="{num(X0 + COLS * CW)}" y2="{Y0 + ROWS * LH}"><stop offset="0" stop-color="#ffa657"/>'
        '<stop offset="1" stop-color="#d2a8ff"/></linearGradient></defs>',
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" fill="#161b22" stroke="#30363d"/>',
    ]
    # Donut: one <text> per frame, each visible for 1/F of the loop.
    for k, lines in enumerate(frames):
        spans = "".join(f'<tspan x="{X0}" y="{Y0 + r * LH}">{html.escape(l)}</tspan>'
                        for r, l in enumerate(lines) if l.strip())
        cls = "d f f0" if k == 0 else "d f"
        out.append(f'<text class="{cls}" style="animation-delay:{num(k * FD)}s">{spans}</text>')
    # Info lines: textLength pins each line's width so columns line up in any monospace font.
    for r, item in enumerate(CARD_INFO):
        y = Y0 + r * LH
        kind = item[0]
        if kind == "head":
            segs = [("w", item[1]), ("m", " " + "─" * (LINE - len(item[1]) - 1))]
        elif kind == "sec":
            segs = [("m", "─ "), ("w", item[1]), ("m", " " + "─" * (LINE - len(item[1]) - 3))]
        elif kind == "kv":
            key, val = item[1], item[2]
            dots = LINE - 5 - len(key) - len(val)
            assert dots >= 2, f"{key}: key + value too long"
            segs = [("m", ". "), ("k", key + ":"), ("m", " " + "." * dots + " "),
                    ("r" if set(val) == {"█"} else "v", val)]
        elif kind == "blank":
            segs = [("m", ".")]
        else:
            segs = [("k", "dev@localhost"), ("m", ":"), ("v", "~"), ("m", "$ ")]
        text = "".join(s for _, s in segs)
        spans = "".join(f'<tspan class="{c}">{html.escape(s)}</tspan>' for c, s in segs)
        out.append(f'<text x="{RX}" y="{y}" textLength="{num(len(text) * CW)}" '
                   f'lengthAdjust="spacing">{spans}</text>')
        if kind == "prompt":
            out.append(f'<rect class="cur" x="{num(RX + len(text) * CW)}" y="{y - 12}" '
                       f'width="{num(CW - 1)}" height="16" fill="#c9d1d9"/>')
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "card.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(card_svg())
    print(path)
