"""Generate assets/hero-{dark,light}.svg — the animated profile hero banner.

The structure is defined once; only the color palette differs per theme.
Edit the CONTENT block below and re-run.

Usage: python3 scripts/generate-hero.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- CONTENT ---------------------------------------------------------------

NAME = "Ryz"
GREETING = "Hi there"  # rendered as: {GREETING} 👋 I'm {NAME}
ROLE = "Backend Engineer &#8212; with a full-stack toolbox"
PHRASES = [
    "stack: Ruby on Rails &#183; TypeScript &#183; React",
    "building: web products &#183; AI agents &#183; engineering teams",
    "note: most of my work lives in private repos",
]
LOCATION = "Osaka, Japan"
ARIA_LABEL = "Ryz — Backend Engineer, Osaka, Japan"

# ---- THEME PALETTES --------------------------------------------------------

THEMES = {
    "dark": {
        "bg": ("#0d1117", "#131a2b"),
        "border": "#30363d",
        "accent": ("#58a6ff", "#bc8cff"),
        "glow1": ("#1f6feb", "0.28"),
        "glow2": ("#8957e5", "0.25"),
        "dots": ("#30363d", "0.8"),
        "deco_opacity": "0.1",
        "deco_accent": "#58a6ff",
        "greeting": "#8b949e",
        "role": "#c9d1d9",
        "prompt": "#3fb950",
        "phrase": "#8b949e",
        "cursor": "#58a6ff",
    },
    "light": {
        "bg": ("#ffffff", "#f3f6fc"),
        "border": "#d0d7de",
        "accent": ("#0969da", "#8250df"),
        "glow1": ("#54aeff", "0.22"),
        "glow2": ("#c297ff", "0.20"),
        "dots": ("#d0d7de", "0.9"),
        "deco_opacity": "0.08",
        "deco_accent": "#0969da",
        "greeting": "#57606a",
        "role": "#1f2328",
        "prompt": "#1a7f37",
        "phrase": "#57606a",
        "cursor": "#0969da",
    },
}

# ---- TEMPLATE --------------------------------------------------------------

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 300" role="img" aria-label="{aria_label}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="960" y2="300" gradientUnits="userSpaceOnUse">
      <stop stop-color="{bg0}"/>
      <stop offset="1" stop-color="{bg1}"/>
    </linearGradient>
    <linearGradient id="accent" x1="64" y1="120" x2="360" y2="170" gradientUnits="userSpaceOnUse">
      <stop stop-color="{accent0}"/>
      <stop offset="1" stop-color="{accent1}"/>
    </linearGradient>
    <radialGradient id="glow1" cx="0.5" cy="0.5" r="0.5">
      <stop stop-color="{glow1}" stop-opacity="{glow1_op}"/>
      <stop offset="1" stop-color="{glow1}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="0.5" cy="0.5" r="0.5">
      <stop stop-color="{glow2}" stop-opacity="{glow2_op}"/>
      <stop offset="1" stop-color="{glow2}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace; }}
    .fadeup {{ opacity: 0; animation: fadeup 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards; }}
    .d1 {{ animation-delay: 0.1s; }} .d2 {{ animation-delay: 0.3s; }}
    .d3 {{ animation-delay: 0.5s; }} .d4 {{ animation-delay: 0.7s; }}
    @keyframes fadeup {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .phrase {{ opacity: 0; animation: cycle {cycle_dur}s linear infinite; }}
{phrase_delay_css}
    @keyframes cycle {{ 0% {{ opacity: 0; }} 3% {{ opacity: 1; }} 28% {{ opacity: 1; }} 33% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
    .cursor {{ animation: blink 1.1s steps(2, start) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .float {{ animation: float 7s ease-in-out infinite; }}
    .float2 {{ animation: float 9s ease-in-out 1.2s infinite; }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
  </style>

  <rect x="1" y="1" width="958" height="298" rx="16" fill="url(#bg)" stroke="{border}" stroke-width="2"/>
  <circle cx="820" cy="40" r="240" fill="url(#glow1)"/>
  <circle cx="180" cy="300" r="220" fill="url(#glow2)"/>

  <g fill="{dots}" opacity="{dots_op}">
    <circle cx="620" cy="60" r="2.5"/><circle cx="700" cy="120" r="2"/><circle cx="900" cy="200" r="2.5"/>
    <circle cx="560" cy="230" r="2"/><circle cx="860" cy="90" r="2"/><circle cx="760" cy="250" r="2.5"/>
  </g>

  <g class="float" opacity="{deco_op}">
    <text x="700" y="205" font-size="130" font-weight="700" fill="url(#accent)">&#123;&#8202;&#125;</text>
  </g>
  <g class="float2" opacity="{deco_op}">
    <text x="560" y="120" font-size="64" font-weight="700" fill="{deco_accent}">&lt;/&gt;</text>
  </g>

  <g class="fadeup d3">
    <text x="928" y="52" text-anchor="end" font-size="13" fill="{greeting_c}">&#128205; {location}</text>
  </g>

  <g class="fadeup d1">
    <text x="66" y="102" font-size="19" fill="{greeting_c}">{greeting} <tspan font-size="21">&#128075;</tspan> I&#8217;m <tspan font-size="24" font-weight="700" fill="url(#accent)">{name}</tspan></text>
  </g>
  <g class="fadeup d2">
    <text x="66" y="162" font-size="27" font-weight="600" fill="{role_c}">{role}</text>
    <rect x="67" y="180" width="92" height="4" rx="2" fill="url(#accent)"/>
  </g>

  <g class="fadeup d4">
    <text x="66" y="240" class="mono" font-size="16" fill="{prompt_c}">$</text>
{phrase_nodes}
  </g>
</svg>
"""

PHRASE_NODE = (
    '    <g class="phrase{cls}">\n'
    '      <text x="84" y="240" class="mono" font-size="16" fill="{phrase_c}">'
    '{text} <tspan class="cursor" fill="{cursor_c}">&#9612;</tspan></text>\n'
    "    </g>"
)


def build(theme_name: str) -> str:
    t = THEMES[theme_name]
    seconds_per_phrase = 4
    cycle_dur = seconds_per_phrase * len(PHRASES)
    delay_css = "    " + " ".join(
        f".p{i + 1} {{ animation-delay: {i * seconds_per_phrase}s; }}"
        for i in range(1, len(PHRASES))
    )
    phrase_nodes = "\n".join(
        PHRASE_NODE.format(
            cls=f" p{i + 1}" if i else "",
            text=text,
            phrase_c=t["phrase"],
            cursor_c=t["cursor"],
        )
        for i, text in enumerate(PHRASES)
    )
    return TEMPLATE.format(
        aria_label=ARIA_LABEL,
        bg0=t["bg"][0],
        bg1=t["bg"][1],
        border=t["border"],
        accent0=t["accent"][0],
        accent1=t["accent"][1],
        glow1=t["glow1"][0],
        glow1_op=t["glow1"][1],
        glow2=t["glow2"][0],
        glow2_op=t["glow2"][1],
        dots=t["dots"][0],
        dots_op=t["dots"][1],
        deco_op=t["deco_opacity"],
        deco_accent=t["deco_accent"],
        greeting_c=t["greeting"],
        greeting=GREETING,
        name=NAME,
        location=LOCATION,
        role_c=t["role"],
        role=ROLE,
        prompt_c=t["prompt"],
        cycle_dur=cycle_dur,
        phrase_delay_css=delay_css,
        phrase_nodes=phrase_nodes,
    )


def main() -> None:
    out_dir = ROOT / "assets"
    out_dir.mkdir(exist_ok=True)
    for theme in THEMES:
        path = out_dir / f"hero-{theme}.svg"
        path.write_text(build(theme), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
