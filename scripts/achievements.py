#!/usr/bin/env python3
"""
achievements.py - render a self-hosted "achievements" badge strip as SVG.

Replaces lowlighter/metrics' Achievements plugin, which scrapes GitHub's own
achievements page with a headless browser and has broken repeatedly since
2023 with no fix from the (now largely unmaintained) upstream project.

This computes a small set of real, verifiable badges straight from the
GitHub REST/GraphQL APIs -- stdlib only, no scraping, nothing to break.

    python scripts/achievements.py --user Janiyash -o assets/achievements

Writes <out>-{dark,light}.svg.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

UA = {"User-Agent": "achievements.py"}

THEMES = {
    "dark":  {"bg": "#0d1117", "border": "#30363d", "title": "#39d353",
              "text": "#c9d1d9", "muted": "#8b949e", "locked": "#30363d"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#1a7f37",
              "text": "#1f2328", "muted": "#57606a", "locked": "#d0d7de"},
}
FONT = "ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"


def rest(path: str, token: str | None):
    req = urllib.request.Request("https://api.github.com" + path, headers=dict(UA))
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def graphql(query: str, variables: dict, token: str):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body,
                                 headers={**UA, "Content-Type": "application/json",
                                          "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


CONTRIB_QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
  }
}
"""


def fetch_streaks(user: str, token: str | None):
    if not token:
        return None
    try:
        data = graphql(CONTRIB_QUERY, {"login": user}, token)
    except urllib.error.HTTPError:
        return None
    if data.get("errors"):
        return None
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort()
    longest = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    return cal["totalContributions"], longest


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render(user, badges, theme):
    """badges: list of (emoji, title, subtitle, unlocked: bool)"""
    c = THEMES[theme]
    pad = 22
    cell_w, cell_h = 128, 96
    cols = min(len(badges), 6)
    rows = (len(badges) + cols - 1) // cols
    W = pad * 2 + cols * cell_w
    H = pad + 30 + rows * cell_h + pad

    out = [
        f'<text x="{pad}" y="{pad + 12}" font-size="15" font-weight="700" '
        f'fill="{c["title"]}">{esc(user)} \u00b7 achievements</text>',
        f'<line x1="{pad}" y1="{pad + 22}" x2="{W - pad}" y2="{pad + 22}" stroke="{c["border"]}"/>',
    ]
    top = pad + 30
    for i, (emoji, title, subtitle, unlocked) in enumerate(badges):
        cx = pad + (i % cols) * cell_w
        cy = top + (i // cols) * cell_h
        fg = c["text"] if unlocked else c["muted"]
        ring = c["title"] if unlocked else c["locked"]
        opacity = "1" if unlocked else "0.45"
        out.append(f'<g opacity="{opacity}">')
        out.append(f'<circle cx="{cx + cell_w/2:.0f}" cy="{cy + 28}" r="22" '
                   f'fill="none" stroke="{ring}" stroke-width="2"/>')
        out.append(f'<text x="{cx + cell_w/2:.0f}" y="{cy + 36}" font-size="22" '
                   f'text-anchor="middle">{emoji}</text>')
        out.append(f'<text x="{cx + cell_w/2:.0f}" y="{cy + 66}" font-size="11" '
                   f'font-weight="600" text-anchor="middle" fill="{fg}">{esc(title)}</text>')
        out.append(f'<text x="{cx + cell_w/2:.0f}" y="{cy + 80}" font-size="9.5" '
                   f'text-anchor="middle" fill="{c["muted"]}">{esc(subtitle)}</text>')
        out.append("</g>")

    body = "".join(out)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="{esc(user)} achievements" '
        f'font-family="{FONT}">'
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>'
        f"{body}</svg>"
    )


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--user", required=True)
    p.add_argument("-o", "--out", type=Path, required=True,
                   help="output path prefix, e.g. assets/achievements")
    args = p.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    user = rest(f"/users/{args.user}", token)
    repos, page = [], 1
    while True:
        batch = rest(f"/users/{args.user}/repos?per_page=100&page={page}&type=owner", token)
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    owned = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in owned)
    languages = {r["language"] for r in owned if r.get("language")}

    streaks = fetch_streaks(args.user, token)
    total_contrib, longest_streak = streaks if streaks else (0, 0)

    badges = [
        ("\U0001F31F", "Star Collector", f"{stars} star{'s' if stars != 1 else ''}", stars >= 1),
        ("\U0001F4E6", "Builder", f"{len(owned)} repos", len(owned) >= 5),
        ("\U0001F30D", "Polyglot", f"{len(languages)} languages", len(languages) >= 4),
        ("\U0001F525", "Streak Keeper", f"best: {longest_streak}d", longest_streak >= 7),
        ("\U0001F4AA", "Consistent", f"best: {longest_streak}d", longest_streak >= 14),
        ("\U0001F680", "Prolific", f"{total_contrib} this year", total_contrib >= 500),
        ("\U0001F465", "Popular", f"{user['followers']} followers", user["followers"] >= 5),
        ("\U0001F9E9", "Diverse", f"{len(owned)} public repos", len(owned) >= 10),
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        dest = args.out.parent / f"{args.out.name}-{theme}.svg"
        dest.write_text(render(args.user, badges, theme), encoding="utf-8")
    unlocked = sum(1 for b in badges if b[3])
    print(f"wrote {args.out.name}-*.svg  ({unlocked}/{len(badges)} unlocked)")


if __name__ == "__main__":
    main()