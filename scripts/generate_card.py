import json
import math
import os
import re
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

HANDLE = "nankishr"
HOST = "notasynthezoid"
NAME = "Nandhakishor VS"
EDUCATION = "Bachelor's in CSE (Ongoing)"
BIO = "Passionate about optimizing software, reading fiction and listening to electronic music."
DOB = date(2008, 10, 1)
QUOTE = "I consume too much water for a human I think…"
TZ = "Asia/Kolkata"
TOKEN = os.environ.get("GITHUB_TOKEN")

W, H, S = 780, 480, 2
PAD_TOP = 28
GAIN = 1.3

BG = (13, 16, 21)
FG = (225, 229, 235)
DIM = (119, 127, 139)
ACCENT = (174, 157, 204)
SUBTLE = (39, 44, 53)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MONO = ASSETS / "fonts" / "FragmentMono-Regular.ttf"
SERIF = ASSETS / "fonts" / "CormorantGaramond-Italic[wght].ttf"


def font(path, size):
    return ImageFont.truetype(str(path), round(size * S))


def age(born, today):
    y = today.year - born.year
    m = today.month - born.month
    d = today.day - born.day
    if d < 0:
        m -= 1
        py, pm = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
        d += monthrange(py, pm)[1]
    if m < 0:
        y -= 1
        m += 12
    plural = lambda n, word: f"{n} {word}" + ("" if n == 1 else "s")
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(d, 'day')}"


def wrap(draw, text, fnt, limit):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= limit * S:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def gh(url):
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "nankishr-profile-card",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode()), res.headers.get("Link", "")


def commit_count(repo_url):
    commits, link = gh(f"{repo_url}/commits?per_page=1")
    if not commits:
        return 0
    for part in link.split(","):
        m = re.search(r'<([^>]+)>;\s*rel="last"', part)
        if m:
            return int(parse_qs(urlparse(m.group(1)).query)["page"][0])
    return len(commits)


def github_stats():
    stars = commits = 0
    page = 1
    try:
        while True:
            repos, _ = gh(
                f"https://api.github.com/users/{HANDLE}/repos"
                f"?type=owner&per_page=100&page={page}"
            )
            for repo in repos:
                if repo.get("fork"):
                    continue
                stars += repo.get("stargazers_count", 0)
                commits += commit_count(repo["url"])
            if len(repos) < 100:
                return stars, commits
            page += 1
    except Exception as e:
        print(f"GitHub API error: {e}")
        return stars, None


def star_icon(d, cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.43
        pts.append((round((cx + math.cos(a) * rr) * S), round((cy + math.sin(a) * rr) * S)))
    d.polygon(pts, fill=ACCENT)


def commit_icon(d, cx, cy):
    for x2, y2, x1, y1 in ((cx, cy + 5, cx, cy - 5), (cx + 5, cy, cx, cy)):
        d.line((round(x1 * S), round(y1 * S), round(x2 * S), round(y2 * S)), fill=ACCENT, width=2 * S)
    for x, y in ((cx, cy - 5), (cx, cy + 5), (cx + 5, cy)):
        d.ellipse(
            (round((x - 2) * S), round((y - 2) * S), round((x + 2) * S), round((y + 2) * S)),
            fill=BG, outline=ACCENT, width=2 * S,
        )


def main():
    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    src = Image.open(ASSETS / "portrait-source.png").convert("RGBA")
    ph = (H - PAD_TOP) * S
    pw = round(src.width * ph / src.height)
    alpha = src.getchannel("A").resize((pw, ph), Image.Resampling.LANCZOS)
    mask = alpha.point([min(255, round(255 * (i / 255) ** 0.8 * GAIN)) for i in range(256)])
    img.paste(Image.new("RGB", (pw, ph), FG), (0, PAD_TOP * S), mask)

    def text(x, y, s, f, c):
        d.text((round(x * S), round(y * S)), s, font=f, fill=c, anchor="ls")

    def line(x1, y1, x2, y2, c):
        d.line((round(x1 * S), round(y1 * S), round(x2 * S), round(y2 * S)), fill=c, width=S)

    def width(s, f):
        return d.textlength(s, font=f) / S

    stars, commits = github_stats()

    x = max(pw / S + 35, 350)
    right = W - 35

    label = font(MONO, 9)
    text(x, 78, "PERSONAL PROFILE", label, DIM)
    line(x, 83, x + width("PERSONAL PROFILE", label), 83, DIM)

    big, small = font(MONO, 21), font(MONO, 12)
    hw = width(HANDLE, big)
    text(x, 117, HANDLE, big, FG)
    text(x + hw, 117, "@", big, DIM)
    text(x + hw + width("@", big), 117, HOST, small, ACCENT)
    line(x, 139, right, 139, SUBTLE)

    key, val = font(MONO, 10), font(MONO, 14)
    uptime = age(DOB, datetime.now(ZoneInfo(TZ)).date())
    for y, k, v in ((173, "name", NAME), (201, "uptime", uptime), (229, "education", EDUCATION)):
        text(x, y, k, key, DIM)
        text(x + 90, y, v, val, FG)

    bio_size, bio_gap = 14, 21
    quote_size, quote_gap = 26, 30
    while True:
        bio_f = font(MONO, bio_size)
        quote_f = font(SERIF, quote_size)
        bio = wrap(d, BIO, bio_f, right - x)
        quote = wrap(d, QUOTE, quote_f, right - x - 25)
        box = quote_f.getbbox("Ihgy", anchor="ls")
        rise, fall = -box[1] / S, box[3] / S
        qtop = 277 + len(bio) * bio_gap + 15
        first = qtop + 6 + rise
        qbottom = first + (len(quote) - 1) * quote_gap + fall + 6
        if qbottom <= 410:
            break
        if quote_size > 19:
            quote_size -= 1
        elif bio_gap > 17:
            bio_gap -= 1
        elif quote_gap > 25:
            quote_gap -= 1
        elif bio_size > 12:
            bio_size = 12
        else:
            raise ValueError("card content doesn't fit")

    for i, row in enumerate(bio):
        text(x, 277 + i * bio_gap, row, bio_f, FG)

    line(x, qtop, x, qbottom, ACCENT)
    for i, row in enumerate(quote):
        open_q = "“" if i == 0 else ""
        close_q = "”" if i == len(quote) - 1 else ""
        text(x + 17, first + i * quote_gap, open_q + row + close_q, quote_f, FG)

    line(x, 435, right, 435, SUBTLE)
    text(x, 458, "Stats:", label, DIM)

    num = font(MONO, 10)
    s_txt = f"{stars:,}"
    c_txt = f"{commits:,}" if commits is not None else "—"
    s_w = 15 + width(s_txt, num)
    c_w = 15 + width(c_txt, num)
    sx = right - (s_w + 16 + c_w)

    star_icon(d, sx + 5, 455, 5)
    text(sx + 15, 458, s_txt, num, FG)

    sep = sx + s_w + 6
    line(sep, 449, sep, 462, SUBTLE)

    cx = sep + 10
    commit_icon(d, cx + 4, 455)
    text(cx + 15, 458, c_txt, num, FG)

    out = ASSETS / "card.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    print(f"Generated {out.relative_to(ROOT)} ({W}x{H}) | stars {stars:,} | commits {c_txt}")


if __name__ == "__main__":
    main()