"""Generate assets/tech-tier-{dark,light}.svg — a game-style tier list of tech icons.

Icons are fetched from skillicons.dev and inlined (GitHub does not load external
images inside README SVGs). Re-run this script after editing TIERS.

Usage: python3 scripts/generate-tier-list.py
"""

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# fmt: off
TIERS = [
    ("S", 3, ["rails", "ruby", "ts", "js", "mysql"], 46),
    ("A", 2, ["py", "react", "nextjs", "tailwind", "docker", "aws", "cloudflare", "githubactions"], 40),
    ("B", 1, ["go", "gatsby", "java", "spring", "postgres", "mongodb", "nginx"], 34),
]
# fmt: on

WIDTH = 960
MARGIN_X = 32
ICONS_X = 140
ROW_PAD = 14

THEMES = {
    "dark": {
        "icon_theme": "dark",
        "bg": ("#0d1117", "#131a2b"),
        "border": "#30363d",
        "title_grad": ("#58a6ff", "#bc8cff"),
        "text": "#c9d1d9",
        "subtext": "#8b949e",
        "row_line": "#21262d",
    },
    "light": {
        "icon_theme": "light",
        "bg": ("#ffffff", "#f3f6fc"),
        "border": "#d0d7de",
        "title_grad": ("#0969da", "#8250df"),
        "text": "#1f2328",
        "subtext": "#57606a",
        "row_line": "#d8dee4",
    },
}

RANK_STYLE = {
    "S": {"grad": ("#ffd34d", "#ff9d2e"), "tint": "#f5c518", "letter": "#3b2300"},
    "A": {"grad": ("#e2e8f0", "#94a3b8"), "tint": "#94a3b8", "letter": "#1e293b"},
    "B": {"grad": ("#e8a05e", "#b06a30"), "tint": "#c77e42", "letter": "#3b2005"},
}

_icon_cache: dict[tuple[str, str], str] = {}


def fetch_icon(slug: str, theme: str) -> str:
    key = (slug, theme)
    if key not in _icon_cache:
        url = f"https://skillicons.dev/icons?i={slug}&theme={theme}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (profile-readme generator)"}
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            _icon_cache[key] = res.read().decode("utf-8")
    return _icon_cache[key]


def embed_icon(svg_text: str, uid: str, x: float, y: float, size: int) -> str:
    svg_text = svg_text.strip()
    open_tag = re.match(r"<svg[^>]*>", svg_text)
    if not open_tag:
        raise ValueError(f"unexpected icon payload for {uid}")
    viewbox = re.search(r'viewBox="([^"]+)"', open_tag.group(0))
    vb = viewbox.group(1) if viewbox else "0 0 256 256"
    inner = svg_text[open_tag.end() : svg_text.rfind("</svg>")]
    # Namespace ids so icons don't clobber each other's gradients/clip paths
    for _id in set(re.findall(r'id="([^"]+)"', inner)):
        inner = inner.replace(f'id="{_id}"', f'id="{uid}-{_id}"')
        inner = inner.replace(f"url(#{_id})", f"url(#{uid}-{_id})")
        inner = inner.replace(f'href="#{_id}"', f'href="#{uid}-{_id}"')
    return (
        f'<svg x="{x:g}" y="{y:g}" width="{size}" height="{size}" '
        f'viewBox="{vb}" fill="none">{inner}</svg>'
    )


def build(theme_name: str) -> str:
    t = THEMES[theme_name]
    rows_h = [max(size, 52) + ROW_PAD * 2 for _, _, _, size in TIERS]
    title_h = 40
    height = title_h + sum(rows_h) + 32

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'role="img" aria-label="Tech stack tier list">'
    )
    parts.append(f"""<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="{WIDTH}" y2="{height}" gradientUnits="userSpaceOnUse">
      <stop stop-color="{t["bg"][0]}"/><stop offset="1" stop-color="{t["bg"][1]}"/>
    </linearGradient>
    <linearGradient id="title" x1="{MARGIN_X}" y1="0" x2="{MARGIN_X + 260}" y2="40" gradientUnits="userSpaceOnUse">
      <stop stop-color="{t["title_grad"][0]}"/><stop offset="1" stop-color="{t["title_grad"][1]}"/>
    </linearGradient>""")
    for rank, style in RANK_STYLE.items():
        parts.append(
            f'<linearGradient id="rank{rank}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop stop-color="{style["grad"][0]}"/>'
            f'<stop offset="1" stop-color="{style["grad"][1]}"/></linearGradient>'
        )
    parts.append("""<clipPath id="badgeClip"><rect x="0" y="0" width="52" height="52" rx="13"/></clipPath>
  </defs>""")

    parts.append("""<style>
    text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }
    .fadeup { opacity: 0; animation: fadeup 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
    .r0 { animation-delay: 0.15s; } .r1 { animation-delay: 0.35s; } .r2 { animation-delay: 0.55s; }
    @keyframes fadeup { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    .shine { animation: shine 4.5s ease-in-out infinite; }
    @keyframes shine { 0%, 55% { transform: translateX(-70px); } 85%, 100% { transform: translateX(130px); } }
    .pulse { animation: pulse 3s ease-in-out infinite; }
    @keyframes pulse { 0%, 100% { opacity: 0.35; } 50% { opacity: 0.8; } }
  </style>""")

    parts.append(
        f'<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="16" '
        f'fill="url(#bg)" stroke="{t["border"]}" stroke-width="2"/>'
    )
    parts.append(
        f'<g class="fadeup"><text x="{WIDTH - MARGIN_X}" y="32" text-anchor="end" font-size="12" '
        f'fill="{t["subtext"]}">usage frequency</text></g>'
    )

    y = title_h
    for i, (rank, bars, slugs, size) in enumerate(TIERS):
        style = RANK_STYLE[rank]
        row_h = rows_h[i]
        cy = y + row_h / 2
        parts.append(f'<g class="fadeup r{i}">')
        # row tint + left accent bar
        parts.append(
            f'<rect x="24" y="{y + 4:g}" width="{WIDTH - 48}" height="{row_h - 8:g}" rx="12" '
            f'fill="{style["tint"]}" opacity="0.05"/>'
        )
        parts.append(
            f'<rect x="24" y="{y + 12:g}" width="4" height="{row_h - 24:g}" rx="2" '
            f'fill="url(#rank{rank})"/>'
        )
        # rank badge (with shine sweep on S)
        bx, by = MARGIN_X + 8, cy - 26
        if rank == "S":
            parts.append(
                f'<rect class="pulse" x="{bx - 5:g}" y="{by - 5:g}" width="62" height="62" rx="16" '
                f'fill="none" stroke="{style["tint"]}" stroke-width="2" opacity="0.5"/>'
            )
        parts.append(
            f'<g transform="translate({bx:g},{by:g})">'
            f'<rect width="52" height="52" rx="13" fill="url(#rank{rank})"/>'
        )
        # signal bars: heights 14/22/30, bottom-aligned; unfilled bars are faint
        for b in range(3):
            bar_h = 14 + b * 8
            bar_x = 10 + b * 12
            opacity = "1" if b < bars else "0.25"
            parts.append(
                f'<rect x="{bar_x}" y="{41 - bar_h}" width="8" height="{bar_h}" rx="3" '
                f'fill="{style["letter"]}" opacity="{opacity}"/>'
            )
        if rank == "S":
            parts.append(
                '<g clip-path="url(#badgeClip)"><g class="shine"><rect x="-10" y="-8" width="18" '
                'height="70" fill="#ffffff" opacity="0.4" transform="skewX(-20)"/></g></g>'
            )
        parts.append("</g>")
        # icons
        x = ICONS_X
        for slug in slugs:
            icon = fetch_icon(slug, t["icon_theme"])
            parts.append(
                embed_icon(icon, f"{theme_name}-{slug}", x, cy - size / 2, size)
            )
            x += size + 12
        parts.append("</g>")
        if i < len(TIERS) - 1:
            parts.append(
                f'<line x1="32" y1="{y + row_h:g}" x2="{WIDTH - 32}" y2="{y + row_h:g}" '
                f'stroke="{t["row_line"]}" stroke-width="1"/>'
            )
        y += row_h

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    out_dir = ROOT / "assets"
    out_dir.mkdir(exist_ok=True)
    for theme in THEMES:
        path = out_dir / f"tech-tier-{theme}.svg"
        path.write_text(build(theme), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
