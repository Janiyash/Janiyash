# Setup — Yash Jani's GitHub profile

This whole folder goes into a repo named **exactly** `Janiyash` (your username),
i.e. `github.com/Janiyash/Janiyash`. That special repo's README is what shows
on your GitHub profile page.

Already done for you in this package:
- `assets/portrait.svg` — dot-matrix portrait generated from your photo
- `assets/skills.json` — your self-rated skill radar data (edit the numbers any time)
- `assets/projects.json` — your 3 featured repos with descriptions
- `README.md` — fully personalized, all placeholders filled in
- `.github/workflows/*.yml` — the automation, untouched (they read the repo
  owner automatically, so no extra editing needed)

## 1. Push it

```bash
cd yash-profile
git init && git branch -M main
git add -A && git commit -m "profile readme"
git remote add origin https://github.com/Janiyash/Janiyash.git
git push -u origin main
```

If the repo doesn't exist yet, create it first at github.com/new, named
exactly `Janiyash`, and make sure it's **public** — the SVG assets are loaded
by URL, so a private repo shows broken images on your profile.

## 2. Let Actions write to the repo

Repo → **Settings** → **Actions** → **General** → **Workflow permissions** →
select **Read and write permissions** → Save.

Without this the Radar/Cards and Snake workflows fail on push.

## 3. (Optional but recommended) Add a metrics token

The built-in token can't read the full contribution graph. For the isometric
calendar and streak numbers to show up:

1. https://github.com/settings/tokens → **Generate new token (classic)**
2. Scope: **`read:user`** (add `repo` too if you want private repos counted)
3. Copy it, then repo → **Settings** → **Secrets and variables** → **Actions**
   → **New repository secret** → name it **`METRICS_TOKEN`**, paste the value

Without this step everything still works, just with a couple of tiles missing
from the stat card.

## 4. Kick off the workflows

Repo → **Actions** tab → enable workflows if prompted → run each one via
**Run workflow**:

| workflow | produces | lands in |
|---|---|---|
| **Metrics** | 3D isometric calendar, language mix, achievements | `assets/metrics.*.svg` on `main` |
| **Snake** | snake eating your contribution graph | the `output` branch |
| **Charts and cards** | both radar charts, stat card, project cards | `assets/radar*.svg`, `assets/card-*.svg` on `main` |

First run takes a couple of minutes. After that: metrics every 6h, snake every
12h, charts/cards daily.

> The snake image is referenced from the `output` branch, so it 404s until
> the Snake workflow has run once. Expected — it'll appear after that.

## Notes on why some assets were generated locally and some aren't included yet

The portrait, skill radar (from `skills.json`), and README were generated
right here and are ready to go. The **live** pieces — language radar, stat
card, project cards, isometric calendar — need to hit the real GitHub API
with proper auth/rate limits, which only works cleanly from GitHub Actions
itself (that's literally what the workflows above are for). They'll appear
automatically the first time you run them, no extra steps beyond what's above.

## Tuning the portrait later

Regenerate any time with a new photo or a different look:

```bash
python scripts/dotify.py your_photo.png -o assets/portrait \
  --cols 100 --equalize --detail 0.5 --color --reveal
```

Other looks worth trying:

```bash
# green monochrome, matches the contribution-graph palette
python scripts/dotify.py your_photo.png -o assets/portrait --cols 88 --equalize --detail 0.5 --animate

# literal 0s and 1s
python scripts/dotify.py your_photo.png -o assets/portrait --mode binary --cols 62 --equalize --detail 0.5
```

## Updating your project cards or skill radar

Edit `assets/projects.json` or `assets/skills.json` directly on GitHub (or
locally + push) — the **Charts and cards** workflow watches those files and
redraws everything automatically on push.
