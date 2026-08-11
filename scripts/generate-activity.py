"""Generate assets/activity-{dark,light}.svg — lifetime figures beside a trend line.

contributionCalendar counts private repository activity, so these figures include
private work. Only dates and counts are requested: repository names, owners and
organizations never cross the API boundary.

The token comes from the environment and needs only the read:user scope — it does
not need, and must not be given, access to any repository.

Usage: GITHUB_TOKEN=$(gh auth token) python3 scripts/generate-activity.py
"""

import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

API = "https://api.github.com/graphql"
DEFAULT_LOGIN = "ryzca"

RECENT_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      contributionCalendar {
        weeks { firstDay contributionDays { contributionCount } }
      }
    }
  }
}
"""

# sized to sit under hero (960x256) and the tier list (960x312)
WIDTH = 960
HEIGHT = 228
MARGIN_X = 40
HEADER_Y = 36

COL_X = MARGIN_X
COL_TOP = 48
COL_STEP = 42
DIVIDER_X = 196
TICK_W = 3
TICK_H = 24

PLOT_X = DIVIDER_X + 24
PLOT_RIGHT = WIDTH - MARGIN_X
GRAPH_TOP = 62
BASE = 186
GRAPH_H = BASE - GRAPH_TOP
MONTH_Y = 206

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

THEMES = {
    "dark": {
        "bg": ("#0d1117", "#131a2b"),
        "border": "#30363d",
        "text": "#c9d1d9",
        "subtext": "#8b949e",
        "faint": "#30363d",
        "line": ("#58a6ff", "#bc8cff"),
        "fill": "#58a6ff",
        "fill_opacity": "0.45",
    },
    "light": {
        "bg": ("#ffffff", "#f3f6fc"),
        "border": "#d0d7de",
        "text": "#1f2328",
        "subtext": "#57606a",
        "faint": "#d8dee4",
        "line": ("#0969da", "#8250df"),
        "fill": "#0969da",
        "fill_opacity": "0.34",
    },
}


def post(query: str, variables: dict, token: str) -> dict:
    payload = json.dumps({"query": query, "variables": variables})
    req = urllib.request.Request(
        API,
        data=payload.encode("utf-8"),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme generator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            body = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # the error body can echo request headers back — never surface it
        raise SystemExit(f"GitHub API request failed: HTTP {e.code}") from None
    if body.get("errors"):
        messages = "; ".join(err.get("message", "?") for err in body["errors"])
        raise SystemExit(f"GitHub API returned errors: {messages}")
    user = body.get("data", {}).get("user")
    if not user:
        raise SystemExit("no such user, or the token cannot see it")
    return user


def fetch_lifetime(login: str, token: str, first_year: int) -> tuple[int, list[date]]:
    """Lifetime total, and every day carrying at least one contribution.

    The total comes from the API's per-year figure rather than from summing the
    daily grid, which can still be missing the current day when the aggregate
    already counts it. Active days and streaks are necessarily grid-derived, so
    they carry that lag until the next run.
    """
    today = datetime.now(timezone.utc).date()
    # contributionsCollection spans at most one year, so query a slice per year
    slices = []
    for year in range(first_year, today.year + 1):
        start = date(year, 1, 1)
        end = min(date(year, 12, 31), today)
        slices.append(
            f'y{year}: contributionsCollection(from: "{start}T00:00:00Z", '
            f'to: "{end}T23:59:59Z") {{ contributionCalendar {{ totalContributions '
            f"weeks {{ contributionDays {{ date contributionCount }} }} }} }}"
        )
    user = post(
        "query($login: String!) { user(login: $login) { " + " ".join(slices) + " } }",
        {"login": login},
        token,
    )

    total = 0
    active: set[date] = set()
    for value in user.values():
        calendar = value["contributionCalendar"]
        total += calendar["totalContributions"]
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                if day["contributionCount"]:
                    active.add(date.fromisoformat(day["date"]))
    return total, sorted(active)


def smooth_path(points: list[tuple[float, float]], top: float, bottom: float) -> str:
    """Catmull-Rom through every point, emitted as cubic beziers.

    Control points are clamped to the plot band. A bezier stays inside the convex
    hull of its control points, so clamping is what keeps the curve off the header
    above and the month labels below.
    """
    if len(points) < 2:
        return ""

    def clamp(y: float) -> float:
        return min(bottom, max(top, y))

    d = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i else points[0]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else points[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, clamp(p1[1] + (p2[1] - p0[1]) / 6))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, clamp(p2[1] - (p3[1] - p1[1]) / 6))
        d.append(
            f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
        )
    return "".join(d)


def month_ticks(first_days: list[date], every: int = 3) -> list[tuple[int, str]]:
    """A coarse axis: one labelled month per quarter, carrying its year."""
    months: list[tuple[int, date]] = []
    seen: set[tuple[int, int]] = set()
    for i, day in enumerate(first_days):
        key = (day.year, day.month)
        if key not in seen:
            seen.add(key)
            months.append((i, day))
    return [
        (i, f"{MONTHS[day.month - 1]} {day.year}")
        for n, (i, day) in enumerate(months)
        if n % every == 0
    ]


def build(
    theme_name: str,
    weekly: list[int],
    first_days: list[date],
    stats: list[tuple[str, str]],
    since: int,
) -> str:
    t = THEMES[theme_name]
    summary = ", ".join(f"{value} {label}" for value, label in stats)
    peak = max(weekly) or 1
    step = (PLOT_RIGHT - PLOT_X) / (len(weekly) - 1)
    points = [
        (PLOT_X + i * step, BASE - value / peak * GRAPH_H)
        for i, value in enumerate(weekly)
    ]
    line = smooth_path(points, GRAPH_TOP, BASE)

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'role="img" aria-label="GitHub activity, private repositories included. '
            f'Since {since}: {summary}. Last 12 months shown as a weekly trend.">'
        )
    ]
    parts.append(f"""<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="{WIDTH}" y2="{HEIGHT}" gradientUnits="userSpaceOnUse">
      <stop stop-color="{t["bg"][0]}"/><stop offset="1" stop-color="{t["bg"][1]}"/>
    </linearGradient>
    <linearGradient id="stroke" x1="{PLOT_X}" y1="0" x2="{PLOT_RIGHT}" y2="0" gradientUnits="userSpaceOnUse">
      <stop stop-color="{t["line"][0]}"/><stop offset="1" stop-color="{t["line"][1]}"/>
    </linearGradient>
    <linearGradient id="under" x1="0" y1="{GRAPH_TOP}" x2="0" y2="{BASE}" gradientUnits="userSpaceOnUse">
      <stop stop-color="{t["fill"]}" stop-opacity="{t["fill_opacity"]}"/>
      <stop offset="1" stop-color="{t["fill"]}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="tick" x1="0" y1="0" x2="0" y2="1">
      <stop stop-color="{t["line"][0]}"/><stop offset="1" stop-color="{t["line"][1]}"/>
    </linearGradient>
  </defs>""")

    figure_delays = " ".join(
        f".f{i} {{ animation-delay: {0.15 + i * 0.12:.2f}s; }}"
        for i in range(len(stats))
    )
    parts.append(f"""<style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .fadeup {{ opacity: 0; animation: fadeup 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards; }}
    @keyframes fadeup {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    {figure_delays}
    .draw {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 1.8s cubic-bezier(0.4, 0, 0.2, 1) 0.3s forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    .wash {{ opacity: 0; animation: wash 1.2s ease-out 1s forwards; }}
    @keyframes wash {{ to {{ opacity: 1; }} }}
    .late {{ opacity: 0; animation: wash 0.8s ease-out 1.3s forwards; }}
  </style>""")

    parts.append(
        f'<rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="16" '
        f'fill="url(#bg)" stroke="{t["border"]}" stroke-width="2"/>'
    )

    parts.append('<g class="fadeup">')
    parts.append(
        f'<text x="{COL_X}" y="{HEADER_Y}" font-size="11" fill="{t["subtext"]}" '
        f'letter-spacing="0.6">all time</text>'
    )
    parts.append(
        f'<text x="{PLOT_RIGHT}" y="{HEADER_Y}" text-anchor="end" font-size="12" '
        f'fill="{t["subtext"]}">last 12 months</text>'
    )
    parts.append("</g>")

    for i, (value, label) in enumerate(stats):
        top = COL_TOP + i * COL_STEP
        parts.append(f'<g class="fadeup f{i}">')
        parts.append(
            f'<rect x="{COL_X}" y="{top}" width="{TICK_W}" height="{TICK_H}" rx="1.5" '
            f'fill="url(#tick)"/>'
        )
        parts.append(
            f'<text x="{COL_X + 14}" y="{top + 17}" font-size="21" font-weight="700" '
            f'fill="{t["text"]}">{value}</text>'
        )
        parts.append(
            f'<text x="{COL_X + 14}" y="{top + 33}" font-size="11" '
            f'fill="{t["subtext"]}">{label}</text>'
        )
        parts.append("</g>")

    parts.append(
        f'<line class="late" x1="{DIVIDER_X}" y1="{COL_TOP - 4}" x2="{DIVIDER_X}" '
        f'y2="{MONTH_Y - 6}" stroke="{t["faint"]}" stroke-width="1"/>'
    )

    parts.append(
        f'<line x1="{PLOT_X}" y1="{BASE}" x2="{PLOT_RIGHT}" y2="{BASE}" '
        f'stroke="{t["faint"]}" stroke-width="1"/>'
    )
    parts.append(
        f'<path class="wash" d="{line}L{points[-1][0]:.1f},{BASE}L{points[0][0]:.1f},'
        f'{BASE}Z" fill="url(#under)"/>'
    )
    parts.append(
        f'<path class="draw" pathLength="1" d="{line}" fill="none" stroke="url(#stroke)" '
        f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    parts.append('<g class="late">')
    for i, name in month_ticks(first_days):
        x = PLOT_X + i * step
        # anchor the outermost labels inward, clear of the divider and the card edge
        if i == 0:
            anchor, x = "start", PLOT_X
        elif x > PLOT_RIGHT - 34:
            anchor, x = "end", PLOT_RIGHT
        else:
            anchor = "middle"
        parts.append(
            f'<text x="{x:.1f}" y="{MONTH_Y}" text-anchor="{anchor}" '
            f'font-size="11" fill="{t["subtext"]}">{name}</text>'
        )
    parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    token = os.environ.get("ACTIVITY_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "set ACTIVITY_TOKEN or GITHUB_TOKEN (read:user scope is enough)"
        )
    login = os.environ.get("GITHUB_REPOSITORY_OWNER", DEFAULT_LOGIN)

    user = post(RECENT_QUERY, {"login": login}, token)
    joined = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).date()
    since = joined.year
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    first_days = [date.fromisoformat(w["firstDay"]) for w in weeks]

    total, active = fetch_lifetime(login, token, since)
    print(
        f"{login}: {total:,} contributions on {len(active):,} days since {since}; "
        f"last 12 months peak week {max(weekly):,}"
    )
    if not total:
        # a token missing read:user still answers, it just answers with zeroes
        raise SystemExit("got 0 contributions — the token likely lacks read:user")

    stats = [
        (f"{total:,}", "contributions"),
        (f"{len(active):,}", "active days"),
        (f"{total / len(active):.1f}" if active else "0.0", "per active day"),
        (f"{MONTHS[joined.month - 1]} {joined.day}, {joined.year}", "joined"),
    ]

    out_dir = ROOT / "assets"
    out_dir.mkdir(exist_ok=True)
    for theme in THEMES:
        path = out_dir / f"activity-{theme}.svg"
        path.write_text(
            build(theme, weekly, first_days, stats, since), encoding="utf-8"
        )
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
