#!/usr/bin/env python3
"""
Generates the three profile graphics:

    assets/hero.svg          "Hi there, I'm ..."  hero card
    assets/stack.svg         "Tools change. Curiosity doesn't."  orbit + stack
    assets/id-dashboard.svg  swinging ID badge + "Real work. Real impact."

Usage (from the repo root):
    pip install pillow numpy
    python scripts/build_profile.py

Everything you would want to change lives in the CONFIG block. The photo is
assets/photo.png (swap the file to change it). Fonts and icons are embedded
in the SVGs, so nothing is loaded from the internet when GitHub renders them.
"""
import base64, io, json, random
from collections import deque
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
FIRST, LAST = "YASH", "JANI"
HANDLE = "@Janiyash"
BADGE_ID = "0911"
LOCATION = "India"
TOP_LEFT = "YJ / SOFTWARE DEVELOPER"
TOP_MID = "INDIA"
PILL = "OPEN TO INTERNSHIPS"
TAGLINE = ("CODE.", "SHIP.")
ROLES = ["Full-Stack Developer", "MERN Stack Developer"]
SUBLINE = ("Building scalable web apps with clean code", "and real-world impact.")
NAME_TAG = "FULL-STACK DEV"

# public numbers (update whenever you like - see README "Updating")
SNAPSHOT = "07 OCT 2026"
REPOS, STARS, FOLLOWERS = 26, 6, 9

PROJECTS = [  # (repo name, one-liner, tag)
    ("meterly-saas", "Subscriptions, API keys & usage analytics", "SAAS"),
    ("safelease", "Lease & rental management platform", "LEASE"),
    ("karma-services", "Service booking with email notifications", "BOOKING"),
]
NOW_TITLE = "Building full-stack products"
NOW_SUB = "MERN · PHP · REST APIs — open to internships & backend roles."

# --------------------------------------------------------------------------- #
# Palette / fonts
# --------------------------------------------------------------------------- #
BG = "#070b16"
BLUE, BLUE_L, BLUE_D = "#2f7bff", "#6aa5ff", "#1650d8"
RED = "#ff3b55"
INK = "#eef2ff"
MUTE = "#7c8bb0"
LINE = "#1b2748"
ICON = "#8db8ff"

ICONS = json.loads((HERE / "icons.json").read_text())


def b64(path):
    return base64.b64encode((HERE / path).read_bytes()).decode()


def font_css():
    return (
        "@font-face{font-family:YJD;font-weight:700;font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2')}"
        "@font-face{font-family:YJD;font-weight:800;font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2')}"
        "@font-face{font-family:YJM;font-weight:400;font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2')}"
        % (b64("display-700.woff2"), b64("display-800.woff2"), b64("mono-400.woff2"))
    )


BASE_CSS = """
.d{font-family:YJD,'Barlow Condensed','Arial Narrow',Impact,sans-serif}
.m{font-family:YJM,'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace}
.w7{font-weight:700}.w8{font-weight:800}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes spinr{to{transform:rotate(-360deg)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes ping{0%{r:62;opacity:.55}100%{r:96;opacity:0}}
@keyframes arrow{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}
"""

# --------------------------------------------------------------------------- #
# Photo cut-out (removes the black studio backdrop, keeps hair / hoodie)
# --------------------------------------------------------------------------- #
def cutout(width, feather_left=0.0, feather_right=0.0, fade_bottom=0.0):
    im = Image.open(ASSETS / "photo.png").convert("RGB")
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    mx = np.array(im).astype(int).max(axis=2)
    dark = mx < 12
    bg = np.zeros((h, width), bool)
    q = deque()
    for x in range(width):
        for y in (0, h - 1):
            if dark[y, x] and not bg[y, x]:
                bg[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, width - 1):
            if dark[y, x] and not bg[y, x]:
                bg[y, x] = True; q.append((y, x))
    while q:  # flood fill from the edges only -> dark hair/hoodie stay opaque
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < width and dark[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; q.append((ny, nx))
    a = Image.fromarray(np.where(bg, 0, 255).astype("uint8"))
    a = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.1))
    a = np.array(a).astype(float) / 255
    xs = np.arange(width)[None, :]
    ys = np.arange(h)[:, None]
    if feather_left:
        a *= np.clip(xs / (width * feather_left), 0, 1)
    if feather_right:
        a *= np.clip((width - 1 - xs) / (width * feather_right), 0, 1)
    if fade_bottom:
        a *= np.clip((h - 1 - ys) / (h * fade_bottom), 0, 1)
    im.putalpha(Image.fromarray((a * 255).astype("uint8")))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=90, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(), width, h


# --------------------------------------------------------------------------- #
# Shared building blocks
# --------------------------------------------------------------------------- #
def wrap(w, h, title, desc, defs, css, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<style>{font_css()}{BASE_CSS}{css}</style><defs>{defs}</defs>{body}</svg>"
    )


def slashes(x, y, h=18, color=RED, gap=14, w=9, skew=6):
    out = ""
    for i in range(3):
        sx = x + i * gap
        out += f'<polygon points="{sx+skew},{y} {sx+skew+w},{y} {sx+w},{y+h} {sx},{y+h}" fill="{color}"/>'
    return out


def dots_and_glows(w, h, glows):
    """background: base colour, dot grid, soft colour glows"""
    g = "".join(
        f'<radialGradient id="g{i}" cx="{cx}" cy="{cy}" r="{r}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{c}" stop-opacity="{o}"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
        for i, (cx, cy, r, c, o) in enumerate(glows)
    )
    defs = (
        g + '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1" fill="#2a3a6a" fill-opacity=".45"/></pattern>'
        f'<clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath>'
    )
    layers = f'<rect width="{w}" height="{h}" fill="{BG}"/><rect width="{w}" height="{h}" fill="url(#dots)"/>'
    layers += "".join(f'<rect width="{w}" height="{h}" fill="url(#g{i})"/>' for i in range(len(glows)))
    return defs, layers


def frame(w, h):
    return (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="28" fill="none" stroke="#1d2c5a"/>'
            f'<rect x="28" y="{h-1.5}" width="{w-56}" height="1.5" fill="url(#edge)"/>')


EDGE = (f'<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{BLUE}"/>'
        f'<stop offset="1" stop-color="{RED}"/></linearGradient>')


def icon(key, x, y, size=26, color=ICON):
    """brand glyph (Simple Icons, 24x24 grid) centred at x,y"""
    s = size / 24
    return (f'<g transform="translate({x - size/2:.1f} {y - size/2:.1f}) scale({s:.3f})">'
            f'<path d="{ICONS[key]["path"]}" fill="{color}"/></g>')


# --------------------------------------------------------------------------- #
# 1. HERO
# --------------------------------------------------------------------------- #
def hero():
    W, H = 1200, 640
    uri, pw, ph = cutout(560, feather_left=0.20, feather_right=0.12, fade_bottom=0.38)
    px, py = 640, 96
    defs, layers = dots_and_glows(W, H, [(930, 330, 460, BLUE, 0.42), (1190, 0, 360, RED, 0.30), (120, 640, 300, BLUE, 0.10)])
    defs += EDGE + f'<linearGradient id="jani" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4f97ff"/><stop offset="1" stop-color="{BLUE_D}"/></linearGradient>'
    _n = len(ROLES); _a = 100 / _n; _f = 0.5 / (3 * _n) * 100
    css = """
.r{opacity:0}.r0{opacity:1}
.ring{transform-origin:940px 360px;animation:spin 60s linear infinite}
.ring2{transform-origin:940px 360px;animation:spinr 90s linear infinite}
.dot{animation:pulse 1.8s ease-in-out infinite}
.float{animation:float 7s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
"""
    css += (f".role{{animation:role {3*_n}s infinite}}"
            f"@keyframes role{{0%{{opacity:0;transform:translateY(10px)}}{_f:.2f}%{{opacity:1;transform:translateY(0)}}"
            f"{_a-_f:.2f}%{{opacity:1;transform:translateY(0)}}{_a:.2f}%{{opacity:0;transform:translateY(-10px)}}100%{{opacity:0}}}}")
    roles = ""
    for i, r in enumerate(ROLES):
        cls = "role r0" if i == 0 else "role r"
        roles += (f'<text class="d w7 {cls}" x="44" y="492" font-size="46" fill="#fff" '
                  f'style="animation-delay:{i*3}s">{escape(r)}</text>')
    stats = [("pin", LOCATION), ("repo", f"{REPOS} repos"), ("star", f"{STARS} stars"), ("code", "MERN · PHP")]
    sx, srow = 44, ""
    for kind, label in stats:
        g = {
            "pin": f'<path d="M10 2a6 6 0 0 0-6 6c0 4.5 6 10 6 10s6-5.5 6-10a6 6 0 0 0-6-6z" transform="translate({sx} 600) scale(.9)" fill="none" stroke="{BLUE}" stroke-width="1.6"/><circle cx="{sx+9}" cy="607" r="2.2" fill="{BLUE}"/>',
            "repo": f'<rect x="{sx+2}" y="601" width="13" height="16" rx="2" fill="none" stroke="{BLUE}" stroke-width="1.6"/><path d="M{sx+2} 612h13" stroke="{BLUE}" stroke-width="1.6"/>',
            "star": f'<path d="M{sx+9} 600l2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z" fill="none" stroke="{BLUE}" stroke-width="1.5" stroke-linejoin="round"/>',
            "code": f'<path d="M{sx+6} 603l-5 6 5 6M{sx+12} 603l5 6-5 6" fill="none" stroke="{BLUE}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
        }[kind]
        srow += g + f'<text class="m" x="{sx+28}" y="614" font-size="14" fill="#9fb0d6">{escape(label)}</text>'
        sx += 28 + len(label) * 8.6 + 40
    body = f"""
<g clip-path="url(#card)">
{layers}
<g stroke="#1f3170" stroke-opacity=".5" stroke-width="1.2">
  <line x1="760" y1="640" x2="1010" y2="0"/><line x1="560" y1="640" x2="810" y2="0"/><line x1="360" y1="640" x2="610" y2="0"/>
</g>
<g fill="none" stroke="{BLUE}">
  <circle class="ring" cx="940" cy="360" r="270" stroke-opacity=".22" stroke-dasharray="2 10"/>
  <circle class="ring2" cx="940" cy="360" r="340" stroke-opacity=".14"/>
</g>
<image class="float" x="{px}" y="{py}" width="{pw}" height="{ph}" href="{uri}" xlink:href="{uri}"/>

<text class="m" x="44" y="46" font-size="13" letter-spacing="2.5" fill="{MUTE}">{escape(TOP_LEFT)}</text>
<text class="m" x="446" y="46" font-size="13" letter-spacing="2.5" fill="{MUTE}">{escape(TOP_MID)}</text>
{slashes(1086, 32, 20, RED, 15, 10, 7)}
<line x1="44" y1="76" x2="1156" y2="76" stroke="{LINE}"/>

<rect x="44" y="104" width="214" height="30" rx="7" fill="#0f2147" stroke="#1d3c80"/>
<text class="m" x="60" y="124" font-size="12" letter-spacing="1.8" fill="#bcd0ff">{escape(PILL)}</text>
<circle class="dot" cx="282" cy="119" r="4.5" fill="{BLUE}"/>

<text class="m" x="44" y="182" font-size="26" fill="#a9b6d6">Hi there, I'm</text>
<text class="d w8" x="42" y="304" font-size="160" fill="{INK}">{FIRST}</text>
<text class="d w8" x="42" y="426" font-size="160" fill="url(#jani)">{LAST}</text>

{slashes(338, 334, 17, RED, 13, 9, 6)}
<text class="d w7" x="336" y="392" font-size="40" fill="#fff">{TAGLINE[0]}</text>
<text class="d w7" x="336" y="428" font-size="40" fill="#fff">{TAGLINE[1]}</text>

{roles}
<text class="m" x="44" y="534" font-size="17" fill="#a9b6d6">{escape(SUBLINE[0])}</text>
<text class="m" x="44" y="560" font-size="17" fill="#a9b6d6">{escape(SUBLINE[1])}</text>
<line x1="44" y1="582" x2="640" y2="582" stroke="{LINE}" stroke-width="1.5"/>
{srow}

<g transform="translate(768 524)">
  <rect width="304" height="70" rx="14" fill="#09122b" fill-opacity=".94" stroke="#25489a"/>
  {slashes(20, 22, 22, BLUE, 12, 8, 6)}
  <text class="d w7" x="76" y="38" font-size="28" fill="#fff">{escape(NAME_TAG)}</text>
  <text class="m" x="76" y="58" font-size="12" fill="{MUTE}">{escape(HANDLE)}</text>
</g>
<text class="m" x="768" y="624" font-size="11" letter-spacing="2.5" fill="#35508f">01 / BUILT TO SHIP</text>
</g>
{frame(W, H)}"""
    (ASSETS / "hero.svg").write_text(
        wrap(W, H, f"{FIRST.title()} {LAST.title()} - {ROLES[0]}",
             f"Hi there, I'm {FIRST.title()} {LAST.title()}. {SUBLINE[0]} {SUBLINE[1]}", defs, css, body), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 2. STACK (orbit + tiles)
# --------------------------------------------------------------------------- #
def stack():
    import math
    W, H = 1200, 680
    cx, cy = 300, 396
    defs, layers = dots_and_glows(W, H, [(300, 396, 330, BLUE, 0.30), (1190, 20, 300, RED, 0.12)])
    defs += EDGE
    # (radius, seconds, clockwise?, icons)
    # tilted elliptical orbits, like the reference:
    # (rx, ry, tilt deg, seconds per lap, clockwise, colour, icons)
    orbits = [
        (112, 112, 0, 22, True, BLUE, ["js", "php", "mysql"]),
        (218, 104, -25, 34, False, RED, ["node", "react", "postman"]),
        (212, 122, 38, 44, True, BLUE, ["python", "java", "tailwind", "github"]),
        (230, 88, 8, 52, False, RED, ["git", "html"]),
    ]
    css = ""
    orb = ""
    for oi, (rx, ry, tilt, dur, cw, col, keys) in enumerate(orbits):
        bright = "#ff5d70" if col == RED else "#8db8ff"
        path = f"M{cx-rx},{cy} a{rx},{ry} 0 1,0 {2*rx},0 a{rx},{ry} 0 1,0 {-2*rx},0"
        css += (f".a{oi}{{animation:dash{oi} {dur*0.6:.1f}s linear infinite}}"
                f"@keyframes dash{oi}{{from{{stroke-dashoffset:0}}to{{stroke-dashoffset:{-100 if cw else 100}}}}}")
        ell = f'cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none"'
        g = (f'<ellipse {ell} stroke="{col}" stroke-opacity=".5" stroke-width="1.2"/>'
             f'<ellipse {ell} class="a{oi}" pathLength="100" stroke="{bright}" stroke-width="2.6" '
             f'stroke-linecap="round" stroke-dasharray="11 89"/>')
        for i, k in enumerate(keys):
            kp = "0;1" if cw else "1;0"
            if k == "postman":      # filled red disc, white glyph (like the filled "N" in the reference)
                disc = f'<circle r="27" fill="{RED}"/>' + icon(k, 0, 0, 26, "#fff")
            elif k == "js":         # filled blue square glyph (like the "TS" in the reference)
                disc = (f'<circle r="27" fill="#0a1226" stroke="{col}" stroke-opacity=".9" stroke-width="1.4"/>'
                        + icon(k, 0, 0, 34, BLUE))
            else:
                disc = (f'<circle r="27" fill="#0a1226" stroke="{col}" stroke-opacity=".9" stroke-width="1.4"/>'
                        + icon(k, 0, 0, 28, bright))
            g += (f'<g><animateMotion dur="{dur}s" begin="-{dur*i/len(keys):.2f}s" repeatCount="indefinite" '
                  f'calcMode="linear" keyPoints="{kp}" keyTimes="0;1" path="{path}"/>'
                  f'<g transform="rotate({-tilt})">{disc}</g></g>')
        orb += f'<g transform="rotate({tilt} {cx} {cy})">{g}</g>'
    css += ".pulse{animation:ping 3.6s ease-out infinite}.tile{}"
    # tiles
    rows = [
        ("01 / LANGUAGES", BLUE, [("JavaScript", "js"), ("Python", "python"), ("Java", "java")]),
        ("02 / FRONTEND", BLUE, [("React", "react"), ("Tailwind", "tailwind"), ("HTML & CSS", "html")]),
        ("03 / BACKEND & DATA", RED, [("Node.js", "node"), ("PHP", "php"), ("MySQL", "mysql")]),
    ]
    tiles = ""
    for ri, (label, accent, items) in enumerate(rows):
        y0 = 204 + ri * 132
        tiles += f'<text class="m" x="625" y="{y0}" font-size="12" letter-spacing="3" fill="{MUTE}">{escape(label)}</text>'
        for ci, (name, key) in enumerate(items):
            x, y = 625 + ci * 177, y0 + 20
            tiles += (f'<g><rect x="{x}" y="{y}" width="163" height="84" rx="13" fill="#0c1428" stroke="#1d2f5c"/>'
                      f'{icon(key, x + 28, y + 26, 22, "#ffb3bd" if accent == RED else ICON)}'
                      f'<text class="d w7" x="{x+16}" y="{y+66}" font-size="28" fill="#fff">{escape(name)}</text>'
                      f'<rect x="{x+16}" y="{y+74}" width="58" height="3" rx="1.5" fill="{accent}"/></g>')
    body = f"""
<g clip-path="url(#card)">
{layers}
<text class="m" x="42" y="42" font-size="13" letter-spacing="3" fill="{MUTE}">02 / MY ENGINE ROOM</text>
<text class="d w8" x="40" y="112" font-size="62" fill="{INK}">TOOLS CHANGE. CURIOSITY DOESN’T.</text>
<text class="m" x="42" y="146" font-size="12" letter-spacing="3" fill="{MUTE}">LANGUAGES / SYSTEMS / PRODUCTS</text>
{slashes(1086, 76, 20, RED, 15, 10, 7)}
<line x1="580" y1="184" x2="580" y2="632" stroke="{LINE}" stroke-width="1.5"/>

{orb}
<circle class="pulse" cx="{cx}" cy="{cy}" r="62" fill="none" stroke="{BLUE_L}" stroke-width="1.5"/>
<circle cx="{cx}" cy="{cy}" r="98" fill="none" stroke="#2f6bff" stroke-opacity=".35"/>
<circle cx="{cx}" cy="{cy}" r="78" fill="#0a1531" stroke="#1f56d6" stroke-width="2"/>
<circle cx="{cx}" cy="{cy}" r="62" fill="#0b1a3d" stroke="#2f6bff" stroke-opacity=".5"/>
<g transform="translate({cx} {cy + 6})">
  <polygon points="0,-52 46,-26 0,0 -46,-26" fill="#5b9bff"/>
  <polygon points="-46,-26 0,0 0,54 -46,28" fill="#2262e8"/>
  <polygon points="46,-26 0,0 0,54 46,28" fill="#1546b8"/>
  <text class="d w8" x="0" y="14" text-anchor="middle" font-size="40" fill="#fff">YJ</text>
</g>
<text class="m" x="70" y="636" font-size="12" letter-spacing="3" fill="{MUTE}">CODE IS THE TOOL. IMPACT IS THE POINT.</text>

{tiles}
<text class="m" x="625" y="636" font-size="12" letter-spacing="3" fill="{MUTE}">BUILD / SHIP / LEARN / REPEAT</text>
</g>
{frame(W, H)}"""
    (ASSETS / "stack.svg").write_text(
        wrap(W, H, "Tools change. Curiosity doesn't.",
             "Stack: JavaScript, Python, Java, React, Tailwind CSS, HTML and CSS, Node.js, PHP, MySQL, Git, GitHub and Postman.",
             defs, css, body), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 3. ID BADGE + CREDENTIALS
# --------------------------------------------------------------------------- #
def barcode(x, y, w, h, seed):
    rnd, cur, out = random.Random(seed), 0.0, ""
    while cur < w - 2:
        bw = rnd.choice([1.4, 1.4, 2.2, 3.2])
        if rnd.random() > 0.28:
            out += f'<rect x="{x+cur:.1f}" y="{y}" width="{bw}" height="{h}"/>'
        cur += bw + rnd.choice([1.4, 2.2])
    return out


def id_dashboard():
    W, H = 1200, 800
    uri, pw, ph = cutout(300, feather_left=0.0)
    defs, layers = dots_and_glows(W, H, [(230, 360, 380, BLUE, 0.30), (160, 800, 340, RED, 0.28), (1100, 0, 300, BLUE, 0.10)])
    defs += EDGE + f"""
<linearGradient id="strap" x1="0" x2="1"><stop offset="0" stop-color="#1a45bd"/><stop offset=".5" stop-color="#2f6bff"/><stop offset="1" stop-color="#1a45bd"/></linearGradient>
<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6ecf8"/><stop offset=".5" stop-color="#8e9bb6"/><stop offset="1" stop-color="#d4dbea"/></linearGradient>
<linearGradient id="cardbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0e1b3d"/><stop offset="1" stop-color="#070e22"/></linearGradient>
<linearGradient id="phbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#143272"/><stop offset="1" stop-color="#091533"/></linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e9c872"/><stop offset="1" stop-color="#b98d34"/></linearGradient>
<linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<pattern id="stripes" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1.4" height="9" fill="#2a4d9a" fill-opacity=".18"/></pattern>
<clipPath id="badge"><rect x="105" y="215" width="330" height="470" rx="26"/></clipPath>
<clipPath id="photo"><rect x="128" y="282" width="284" height="240" rx="20"/></clipPath>"""
    css = """
.drop{animation:drop 1.5s cubic-bezier(.2,.7,.25,1) 1 both}
@keyframes drop{0%{transform:translateY(-640px)}55%{transform:translateY(0)}70%{transform:translateY(-34px)}85%{transform:translateY(0)}93%{transform:translateY(-9px)}100%{transform:translateY(0)}}
.swing{transform-origin:270px 0px;animation:swing 6.5s ease-in-out 1.4s infinite}
@keyframes swing{0%,100%{transform:rotate(-2.6deg)}50%{transform:rotate(2.6deg)}}
.sweep{animation:sweep 5.5s ease-in-out 2s infinite}
@keyframes sweep{0%{transform:translateX(-380px)}55%,100%{transform:translateX(420px)}}
.arrow{animation:arrow 1.8s ease-in-out infinite}
"""
    strap_txt = f"{FIRST} {LAST} // {BADGE_ID}"
    strap = "".join(
        f'<text class="m" transform="translate({270+4} {8+i*190}) rotate(90)" font-size="11" letter-spacing="1.8" fill="#cfe0ff" fill-opacity=".85">{escape(strap_txt)}</text>'
        for i in range(1))
    # project rows
    prow = ""
    for i, (name, desc, tag) in enumerate(PROJECTS):
        y = 420 + i * 70
        tw = len(tag) * 8.3 + 26
        prow += (f'<text class="d w7" x="520" y="{y}" font-size="28" fill="#fff">{escape(name)}</text>'
                 f'<text class="m" x="520" y="{y+22}" font-size="12.5" fill="{MUTE}">{escape(desc)}</text>'
                 f'<rect x="{1152-tw:.0f}" y="{y-22}" width="{tw:.0f}" height="26" rx="13" fill="#0f2147" stroke="#1d3c80"/>'
                 f'<text class="m" x="{1152-tw/2:.0f}" y="{y-5}" text-anchor="middle" font-size="11" letter-spacing="1.5" fill="#bcd0ff">{tag}</text>'
                 f'<line x1="520" y1="{y+38}" x2="1152" y2="{y+38}" stroke="{LINE}"/>')
    tiles = ""
    for i, (lab, num, sub, col) in enumerate([("PUBLIC REPOS", REPOS, "ON GITHUB", RED), ("REPO STARS", STARS, "RECEIVED", BLUE), ("FOLLOWERS", FOLLOWERS, "GITHUB", BLUE_L)]):
        x = 520 + i * 217
        tiles += (f'<rect x="{x}" y="164" width="198" height="156" rx="14" fill="#0c1428" stroke="#1d2f5c"/>'
                  f'<text class="m" x="{x+20}" y="194" font-size="11" letter-spacing="2" fill="{MUTE}">{lab}</text>'
                  f'<text class="d w8" x="{x+20}" y="272" font-size="84" fill="{col}">{num}</text>'
                  f'<text class="m" x="{x+20}" y="302" font-size="10" letter-spacing="2" fill="#4d5d86">{sub}</text>')
    body = f"""
<g clip-path="url(#card)">
{layers}
<text class="d w8" x="36" y="196" font-size="150" fill="#102250">THE</text>
<text class="d w8" x="36" y="326" font-size="150" fill="#102250">HUMAN.</text>
<text class="d w8" x="36" y="756" font-size="74" fill="#2a1423">BEHIND THE CODE.</text>

<g class="drop"><g transform="rotate(3.5 270 0)"><g class="swing">
  <rect x="244" y="-30" width="52" height="204" fill="url(#strap)"/>
  <rect x="244" y="-30" width="3" height="204" fill="#fff" fill-opacity=".18"/>
  {strap}
  <rect x="249" y="160" width="42" height="56" rx="8" fill="url(#metal)"/>
  <rect x="260" y="176" width="20" height="22" rx="5" fill="#0a1226"/>
  <g clip-path="url(#badge)">
    <rect x="105" y="215" width="330" height="470" fill="url(#cardbg)"/>
    <rect x="105" y="215" width="330" height="470" fill="url(#stripes)"/>
    <rect x="105" y="215" width="330" height="9" fill="{RED}"/>
    <rect x="250" y="226" width="40" height="8" rx="4" fill="#04070f"/>
    <text class="d w7" x="128" y="266" font-size="26" fill="#fff">YJ / BUILDER PASS</text>
    <text class="m" x="412" y="264" text-anchor="end" font-size="16" fill="{BLUE}">{BADGE_ID}</text>
    <rect x="128" y="282" width="284" height="240" rx="20" fill="url(#phbg)"/>
    <g clip-path="url(#photo)"><image x="122" y="{522 - ph - 4}" width="{pw}" height="{ph}" href="{uri}" xlink:href="{uri}"/></g>
    <rect x="128" y="282" width="284" height="240" rx="20" fill="none" stroke="#bfe0ff" stroke-width="2.4" pathLength="100" stroke-dasharray="7 93" stroke-linecap="round"><animate attributeName="stroke-dashoffset" values="0;-100" dur="5.5s" repeatCount="indefinite"/></rect>
    <rect x="142" y="486" width="132" height="26" rx="6" fill="#2a6cff"/>
    <text class="m" x="208" y="503" text-anchor="middle" font-size="12" letter-spacing="1.5" fill="#fff">{escape(NAME_TAG)}</text>
    <text class="d w8" x="128" y="576" font-size="54" fill="#fff">{FIRST} {LAST}</text>
    <text class="m" x="128" y="598" font-size="12" letter-spacing="1.5" fill="{MUTE}">{escape(LOCATION.upper())} / OPEN TO WORK</text>
    <rect x="352" y="548" width="58" height="46" rx="9" fill="url(#gold)"/>
    <path d="M352 571h58M381 548v46M363 559h36v24h-36z" stroke="#8d6a1f" stroke-width="1.2" fill="none"/>
    <g fill="#cfe0ff" fill-opacity=".9">{barcode(128, 612, 284, 32, FIRST + LAST)}</g>
    <text class="m" x="128" y="668" font-size="10" letter-spacing="2" fill="#4d5d86">INDEPENDENT BUILDER ID · {HANDLE.lstrip('@').upper()}</text>
    <rect class="sweep" x="105" y="215" width="150" height="470" fill="url(#sweep)" transform="skewX(-14)"/>
  </g>
  <rect x="105" y="215" width="330" height="470" rx="26" fill="none" stroke="#2a4fa8" stroke-width="2"/>
</g></g></g>

<text class="m" x="520" y="42" font-size="13" letter-spacing="3" fill="{MUTE}">03 / BUILDER CREDENTIALS</text>
<text class="d w8" x="518" y="112" font-size="62" fill="{INK}">REAL WORK. REAL IMPACT.</text>
<text class="m" x="520" y="142" font-size="12" letter-spacing="3" fill="{MUTE}">PUBLIC SNAPSHOT / {SNAPSHOT}</text>
{tiles}
<text class="m" x="520" y="364" font-size="12" letter-spacing="3" fill="{MUTE}">FEATURED / PUBLIC REPOSITORIES</text>
<path d="M1138 352l3.2 6.6 7.2 1-5.2 5 1.2 7.2-6.4-3.4-6.4 3.4 1.2-7.2-5.2-5 7.2-1z" fill="none" stroke="{RED}" stroke-width="1.5" stroke-linejoin="round"/>
{prow}

<rect x="520" y="634" width="632" height="120" rx="14" fill="#0b1329" stroke="#1d2f5c"/>
<rect x="540" y="652" width="54" height="26" rx="6" fill="{RED}"/>
<text class="m" x="567" y="670" text-anchor="middle" font-size="12" letter-spacing="1.5" fill="#fff">NOW</text>
<text class="d w7" x="540" y="716" font-size="38" fill="#fff">{escape(NOW_TITLE)}</text>
<text class="m" x="540" y="740" font-size="13" fill="{MUTE}">{escape(NOW_SUB)}</text>
<g class="arrow"><path d="M1108 700h28m-9-9l9 9-9 9" fill="none" stroke="{BLUE}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></g>
</g>
{frame(W, H)}"""
    (ASSETS / "id-dashboard.svg").write_text(
        wrap(W, H, f"{FIRST.title()} {LAST.title()} builder ID",
             f"Builder ID card and public snapshot: {REPOS} public repositories, {STARS} stars, {FOLLOWERS} followers.",
             defs, css, body), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 4. ABOUT  ("Ideas. Built different.")
# --------------------------------------------------------------------------- #
ABOUT_SLIDES = [  # (step, title, two description lines, icons)
    ("IDEATE", "Real-World Problems", ("Start from a real need,", "then plan the simplest way to solve it."), ["git", "github", "postman"]),
    ("ENGINEER", "Full-Stack Web Apps", ("MERN & PHP, REST APIs,", "authentication and MySQL."), ["react", "node", "php", "mysql"]),
    ("SHIP", "Clean, Scalable Code", ("Built to be used, maintained", "and grown over time."), ["tailwind", "html", "js"]),
]


def about():
    W, H = 1200, 600
    defs, layers = dots_and_glows(W, H, [(900, 330, 420, BLUE, 0.30), (0, 600, 300, RED, 0.14)])
    defs += EDGE
    n = len(ABOUT_SLIDES)
    dur = 4 * n
    a, f = 100 / n, 0.6 / dur * 100
    css = (f".sl{{opacity:0;animation:slide {dur}s infinite}}.sl0{{opacity:1}}"
           f"@keyframes slide{{0%{{opacity:0;transform:translateX(26px)}}{f:.2f}%{{opacity:1;transform:translateX(0)}}"
           f"{a-f:.2f}%{{opacity:1;transform:translateX(0)}}{a:.2f}%{{opacity:0;transform:translateX(-26px)}}100%{{opacity:0}}}}"
           f".hl{{opacity:0;animation:hl {dur}s infinite}}.hl0{{opacity:1}}"
           f"@keyframes hl{{0%{{opacity:0}}{f:.2f}%{{opacity:1}}{a-f:.2f}%{{opacity:1}}{a:.2f}%{{opacity:0}}100%{{opacity:0}}}}"
           ".cur{animation:blink 1s steps(2,end) infinite}@keyframes blink{50%{opacity:0}}")
    steps = ""
    for i, (st, *_r) in enumerate(ABOUT_SLIDES):
        x = 40 + i * 188
        d = f'style="animation-delay:{i*4}s"'
        steps += (f'<g><rect x="{x}" y="452" width="164" height="58" rx="12" fill="#0c1428" stroke="#1d2f5c"/>'
                  f'<rect class="hl {"hl0" if i == 0 else ""}" {d} x="{x}" y="452" width="164" height="58" rx="12" fill="{BLUE}" fill-opacity=".22" stroke="{BLUE_L}"/>'
                  f'<text class="m" x="{x+16}" y="476" font-size="11" letter-spacing="2" fill="{RED}">0{i+1}</text>'
                  f'<text class="d w7" x="{x+16}" y="500" font-size="26" fill="#fff">{st}</text></g>')
        if i < n - 1:
            steps += f'<path d="M{x+170} 481h12m-5-5l5 5-5 5" fill="none" stroke="{MUTE}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    slides = ""
    for i, (st, title, desc, keys) in enumerate(ABOUT_SLIDES):
        ic = "".join(
            f'<g transform="translate({690 + j*76} 232)"><circle r="30" fill="#0a1226" stroke="{BLUE if j % 2 == 0 else RED}" stroke-opacity=".9" stroke-width="1.5"/>'
            f'{icon(k, 0, 0, 30, ICON if j % 2 == 0 else "#ff5d70")}</g>' for j, k in enumerate(keys))
        slides += (f'<g class="sl {"sl0" if i == 0 else ""}" style="animation-delay:{i*4}s">'
                   f'<text class="d w8" x="1124" y="262" text-anchor="end" font-size="112" fill="#12214a">0{i+1}</text>'
                   f'{ic}'
                   f'<text class="d w8" x="668" y="364" font-size="46" fill="#fff">{escape(title)}</text>'
                   f'<text class="m" x="670" y="404" font-size="16" fill="#a9b6d6">{escape(desc[0])}</text>'
                   f'<text class="m" x="670" y="430" font-size="16" fill="#a9b6d6">{escape(desc[1])}</text>'
                   f'<text class="m" x="670" y="478" font-size="12" letter-spacing="3" fill="{BLUE_L}">{st} / 0{i+1} OF 0{n}</text></g>')
    body = f"""
<g clip-path="url(#card)">
{layers}
<text class="m" x="42" y="42" font-size="13" letter-spacing="3" fill="{MUTE}">01 / FROM THOUGHT TO THING</text>
{slashes(1086, 28, 20, RED, 15, 10, 7)}
<text class="d w8" x="40" y="168" font-size="104" fill="{INK}">IDEAS.</text>
<text class="d w8" x="40" y="262" font-size="104" fill="{INK}">BUILT</text>
<text class="d w8" x="40" y="356" font-size="104" fill="url(#jani)">DIFFERENT.</text>
<text class="m" x="42" y="414" font-size="18" fill="{BLUE_L}">&gt; turn_curiosity_into_impact()</text>
<rect class="cur" x="418" y="399" width="10" height="19" fill="{BLUE_L}"/>
{steps}
<rect x="640" y="130" width="512" height="400" rx="22" fill="#0b1329" stroke="#1d2f5c"/>
<rect x="640" y="130" width="512" height="4" rx="2" fill="{RED}"/>
<text class="m" x="668" y="168" font-size="12" letter-spacing="3" fill="{MUTE}">WHAT I DO</text>
{slides}
<text class="m" x="42" y="566" font-size="12" letter-spacing="3" fill="{MUTE}">LEARNING • BUILDING • IMPROVING</text>
</g>
{frame(W, H)}"""
    defs += f'<linearGradient id="jani" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4f97ff"/><stop offset="1" stop-color="{BLUE_D}"/></linearGradient>'
    (ASSETS / "about.svg").write_text(
        wrap(W, H, "Ideas. Built different.",
             "Ideate, engineer, ship: real-world problems, full-stack web apps with MERN and PHP, clean scalable code.",
             defs, css, body), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 5. CONNECT
# --------------------------------------------------------------------------- #
CONNECT = [  # (label, sub, colour, glyph)
    ("LinkedIn", "linkedin.com/in/jani-yash001", BLUE, "linkedin"),
    ("Portfolio", "portfolio.yashjani.in", BLUE_L, "portfolio"),
    ("GitHub", "github.com/Janiyash", "#cdd9f5", "github"),
    ("Email", "janiyash0911@gmail.com", RED, "gmail"),
]


def connect():
    W, H = 1200, 640
    uri, pw, ph = cutout(430, feather_left=0.16, feather_right=0.16, fade_bottom=0.42)
    defs, layers = dots_and_glows(W, H, [(240, 470, 330, BLUE, 0.34), (1190, 600, 320, RED, 0.16)])
    defs += EDGE + f'<linearGradient id="jani" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4f97ff"/><stop offset="1" stop-color="{BLUE_D}"/></linearGradient>'
    css = ".arr{animation:arrow 1.8s ease-in-out infinite}.flt{animation:float 7s ease-in-out infinite}@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}"
    cards = ""
    for i, (label, sub, col, g) in enumerate(CONNECT):
        y = 168 + i * 100
        if g == "linkedin":
            glyph = f'<text class="d w8" x="30" y="40" text-anchor="middle" font-size="34" fill="{col}">in</text>'
        elif g == "portfolio":
            glyph = f'<text class="d w8" x="30" y="39" text-anchor="middle" font-size="30" fill="{col}">YJ</text>'
        else:
            glyph = icon(g, 30, 30, 30, col)
        cards += (f'<g transform="translate(520 {y})">'
                  f'<rect width="640" height="84" rx="16" fill="#0c1428" stroke="{col}" stroke-opacity=".55"/>'
                  f'<rect width="5" height="84" rx="2.5" fill="{col}"/>'
                  f'<g transform="translate(26 12)"><rect width="60" height="60" rx="14" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".6"/>{glyph}</g>'
                  f'<text class="d w7" x="108" y="42" font-size="32" fill="#fff">{escape(label)}</text>'
                  f'<text class="m" x="109" y="64" font-size="14" fill="{MUTE}">{escape(sub)}</text>'
                  f'<g class="arr"><path d="M580 42h30m-10-10l10 10-10 10" fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></g></g>')
    body = f"""
<g clip-path="url(#card)">
{layers}
<text class="m" x="42" y="42" font-size="13" letter-spacing="3" fill="{MUTE}">04 / START A CONVERSATION</text>
{slashes(1086, 28, 20, RED, 15, 10, 7)}
<image class="flt" x="52" y="56" width="{pw}" height="{ph}" href="{uri}" xlink:href="{uri}"/>
<text class="d w8" x="40" y="516" font-size="104" fill="{INK}">LET’S</text>
<text class="d w8" x="40" y="612" font-size="104" fill="url(#jani)">CONNECT.</text>
<text class="d w8" x="520" y="104" font-size="54" fill="{BLUE}">BUILD SOMETHING GREAT.</text>
<text class="m" x="522" y="134" font-size="14" letter-spacing="1" fill="{MUTE}">Ideas. Opportunities. Your next move.</text>
{cards}
<text class="m" x="522" y="610" font-size="12" letter-spacing="3" fill="{MUTE}">GOOD PEOPLE. GOOD IDEAS. LET’S TALK.</text>
</g>
{frame(W, H)}"""
    (ASSETS / "connect.svg").write_text(
        wrap(W, H, "Let's connect",
             "Connect with Yash Jani on LinkedIn, his portfolio, GitHub or email.", defs, css, body), encoding="utf-8")


if __name__ == "__main__":
    hero(); about(); stack(); id_dashboard(); connect()
    for n in ("hero", "about", "stack", "id-dashboard", "connect"):
        print(f"assets/{n}.svg  {(ASSETS / (n + '.svg')).stat().st_size/1024:.0f} KB")
