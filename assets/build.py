#!/usr/bin/env python3
"""Generate the README's themed SVG assets.

Run from the repo root: python3 assets/build.py. It rewrites the constellation in the hand-drawn
banner-dark.svg from the STARS list (edit that list to add or remove a skill), keeps the alt text in
the SVG and README in step, and derives banner-light.svg from the dark one by recolouring it.

It also draws the "Selected work" cards into assets/cards from the WORK list (edit that list to add,
remove or reword a project) and rewrites that section of the README to show them.
"""
import html
import re
from pathlib import Path

OUT = Path(__file__).parent
# the constellation's colours, shared by the banner and the project cards so the 2 always match
CHART = {"dark": {"star": "#ffd772", "line": "#8ea6dc"}, "light": {"star": "#c98a12", "line": "#6d80a6"}}
LABELS = {"dark": "#c8d3ec", "light": "#34425c"}     # the banner's skill names
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


def label_offset(i, y, neighbours, n):
    """Where a star's label sits: above peaks, below dips, so it never crosses the lines either side."""
    if i == n - 1:
        return -10, -20            # the brightest star is a peak, so its label sits above it too
    above = y <= sum(neighbours) / len(neighbours)
    return (0, -16) if above else (0, 27)


STARS = ["Rust", "Python", "Go", "TypeScript", "SQL", "PostgreSQL", "GraphQL", "Docker", "Kafka",
         "Redpanda", "Ansible", "Kubernetes", "Proxmox", "Solidity"]


def constellation():
    """Rewrite the banner's constellation from STARS: a rising zigzag, 1 labelled star per skill.

    The line draws from 4.5% to 32% of a single 22s run, each star lights as the line reaches it, and the
    finished chart then holds rather than looping, so it can be read.
    """
    import math
    p = OUT / "banner-dark.svg"
    s = p.read_text()
    n = len(STARS)
    x0, x1, y0, y1, amp = 165, 1110, 240, 55, 26
    pts = []
    for i, name in enumerate(STARS):
        f = i / (n - 1)
        x = round(x0 + (x1 - x0) * f)
        y = round(y0 + (y1 - y0) * f + (0 if i == n - 1 else (amp if i % 2 == 0 else -amp)))
        pts.append((name, x, y))
    L, cum = 0, [0]
    for i in range(n - 1):
        L += math.dist(pts[i][1:], pts[i + 1][1:])
        cum.append(L)
    dash = int(math.ceil(L / 10) * 10)
    # timing rules
    css, names = [], []
    for i in range(n):
        cls = "vspark" if i == n - 1 else f"v{i+1}"
        names.append("." + cls)
        css.append(f"      .{cls} {{ animation: ignite{i+1} 22s linear 1 both; }}")
    css.append("      .caption { animation: captionIn 22s linear 1 both; }")
    for i in range(n):
        start = 4.5 + 27.5 * cum[i] / L
        css.append(f"      @keyframes ignite{i+1} {{ 0%, {start:.1f}% {{ opacity: 0; }} {start+1.5:.1f}% {{ opacity: 1; }} 100% {{ opacity: 1; }} }}")
    # the telescope's sight line appears only once the last star is fully lit
    lit = start + 1.5
    s, count = re.subn(r'@keyframes sightIn \{ 0%, [\d.]+% \{ opacity: 0; \} [\d.]+% \{',
                       f'@keyframes sightIn {{ 0%, {lit:.1f}% {{ opacity: 0; }} {lit + 2.5:.1f}% {{', s)
    assert count == 1, "sight line timing not found"
    s = re.sub(r'      \.v1 \{ animation: ignite1.*?@keyframes ignite\d+ \{[^\n]*\n(?=      @keyframes captionIn)', "\n".join(css) + "\n", s, flags=re.S)
    s, count = re.subn(r'\.cline, (\.v\d+, )+\.vspark, \.caption,', '.cline, ' + ", ".join(names) + ', .caption,', s)
    assert count == 1, 'reduced-motion selector not found'
    s = re.sub(r'stroke-dasharray: \d+;', f'stroke-dasharray: {dash};', s)
    s = re.sub(r'(0%|4\.5%)(\s+)\{ stroke-dashoffset: \d+; \}', rf'\1\2{{ stroke-dashoffset: {dash}; }}', s)
    s = re.sub(r'(32%|100%)(\s+)\{ stroke-dashoffset: \d+; \}', r'\1\2{ stroke-dashoffset: 0; }', s)
    # vertices
    poly = " ".join(f"{x},{y}" for _, x, y in pts)
    verts = []
    for i, (t, x, y) in enumerate(pts):
        nb = [pts[j][2] for j in (i - 1, i + 1) if 0 <= j < n]
        dx, dy = label_offset(i, y, nb, n)
        label = (f'<text x="{x+dx}" y="{y+dy}" text-anchor="middle" font-family="{SANS}" font-size="15" '
                 f'font-weight="600" fill="{LABELS["dark"]}">{t}</text>')
        star = CHART["dark"]["star"]
        if i == n - 1:
            verts.append(f'      <g class="vspark">\n        <circle cx="{x}" cy="{y}" r="13" fill="{star}" fill-opacity="0.28"/>\n        <use href="#sparkle" transform="translate({x},{y}) scale(1.5)"/>\n        {label}\n      </g>')
        else:
            verts.append(f'      <g class="v{i+1}">\n        <circle cx="{x}" cy="{y}" r="11" fill="{star}" fill-opacity="0.28"/>\n        <circle cx="{x}" cy="{y}" r="5" fill="{star}"/>\n        {label}\n      </g>')
    a = s.index('      <polyline class="cline"')
    b = s.index('\n    </g>', a) + 1         # the end of the constellation's group
    s = (s[:a] + f'      <polyline class="cline" points="{poly}"\n                fill="none" stroke="{CHART['dark']['line']}" stroke-opacity="0.85" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>\n'
         + "\n".join(verts) + "\n" + s[b:])
    s, count = re.subn(r'(<g id="sparkle">\s*<path [^>]*? fill=")#\w+"', rf'\g<1>{CHART["dark"]["star"]}"', s)
    assert count == 1, "sparkle for the brightest star not found"
    # point the telescope at the final star and run the sight line from its far end to the star
    ex, ey = pts[-1][1], pts[-1][2]
    ground = int(re.search(r'<g transform="translate\(0,(\d+)\)">\s*<!-- the moon surface -->', s).group(1))
    tx, ty = map(int, re.search(r'<!-- the bot peering through its telescope.*?<g transform="translate\((\d+),(\d+)\)">',
                                s, re.S).groups())
    ty += ground                                 # the telescope's pivot, in banner rather than moon coordinates
    angle = math.degrees(math.atan2(ex - tx, ty - ey))   # 0 is straight up, positive leans right
    s = re.sub(r'<g transform="rotate\(-?[\d.]+\)">', f'<g transform="rotate({angle:.0f})">', s)
    sx = round(tx + 16 * math.sin(math.radians(angle)))   # 16 units up the tilted tube, at its far end
    sy = round(ty - 16 * math.cos(math.radians(angle))) - ground
    s = re.sub(r'<line class="sight" x1="-?\d+" y1="-?\d+" x2="-?\d+" y2="-?\d+"', f'<line class="sight" x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey - ground + 8}"', s)
    # background stars must not sit inside a label; drop any that do (labels are 15px mono, ~9px per glyph)
    boxes = []
    for i, (t, x, y) in enumerate(pts):
        nb = [pts[j][2] for j in (i - 1, i + 1) if 0 <= j < n]
        dx, dy = label_offset(i, y, nb, n)
        half = 9 * len(t) / 2 + 4
        boxes.append((x + dx - half, y + dy - 14, x + dx + half, y + dy + 5))
    def keep(m):
        cx, cy = float(m.group(1)), float(m.group(2))
        return "" if any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in boxes) else m.group(0)
    a = s.index('<g class="stars"')
    b = s.index('</g>', a)
    stars_block = re.sub(r'\s*<circle cx="([\d.]+)" cy="([\d.]+)" r="[\d.]+" fill-opacity="[\d.]+"/>', keep, s[a:b])
    s = s[:a] + stars_block + s[b:]
    listed = ", ".join(STARS[:-1]) + " and " + STARS[-1]
    s = re.sub(r'with a star for each of .*? and \w+,', f'with a star for each of {listed},', s)
    p.write_text(s)
    print(f"constellation: {n} stars, path {round(L)}, dash {dash}")
    return listed


def swap(text, old, new):
    """Replace old with new, stopping the build if the hand-drawn banner no longer contains old."""
    assert old in text, f"banner-dark.svg no longer contains: {old[:70]}"
    return text.replace(old, new)


def light_banner():
    """Recolour the hand-drawn dark banner into a dawn edition: a pale sky warming towards the horizon."""
    s = (OUT / "banner-dark.svg").read_text()
    # sky: a soft blue-grey dawn, warming to off-white at the horizon
    s = re.sub(r'(<linearGradient id="sky".*?</linearGradient>)',
               '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
               '<stop offset="0%" stop-color="#CFDCF0"/><stop offset="100%" stop-color="#F3EEE6"/></linearGradient>', s, flags=re.S)
    s = swap(s, 'stop-color="#CFCAC0"', 'stop-color="#DCD8CF"')      # the moon, a little paler by day
    s = swap(s, 'stop-color="#A29D93"', 'stop-color="#D2CDC3"')
    # the background stars turn slate and the shooting star navy; the constellation and planet take their
    # light versions
    head, rest = s.split('<!-- background starfield -->', 1)
    sky, ground = rest.split('<!-- the moon surface -->', 1)
    sky = swap(sky, '<g class="stars" fill="#FFFFFF">', '<g class="stars" fill="#5B6B8A">')
    sky = swap(sky, '#FFFFFF', '#1F2440')
    for part in ("star", "line"):
        sky = swap(sky, CHART["dark"][part], CHART["light"][part])
    sky = swap(sky, LABELS["dark"], LABELS["light"])
    sky = swap(sky, '#5D6F99', '#9AAED0')
    ground = swap(ground, 'stroke="#EAE5DB" stroke-opacity="0.8"', 'stroke="#C4BFB3" stroke-opacity="1"')
    ground = swap(ground, 'fill="#3F4452" fill-opacity="0.85">star chart', 'fill="#5C6474" fill-opacity="1">star chart')
    ground = swap(ground, 'stroke="#F2F4FA"', 'stroke="#1F2440"')
    ground = swap(ground, 'stroke="#E8EAF2"', 'stroke="#1F2440"')
    ground = swap(ground, 'stroke="#B7A6FF"', 'stroke="#3A22A6"')
    ground = swap(ground, 'fill="#0B0725"', 'fill="#4A3DB8"')
    ground = swap(ground, 'stroke="#FFD98A" stroke-opacity="0.25"', 'stroke="#3B4A8C" stroke-opacity="0.45"')
    # the bot stays white but gets an outline so it reads against the pale sky
    ground = swap(ground, '<line x1="13" y1="-4" x2="19" y2="-11" stroke="#FFFFFF" stroke-opacity="0.93"', '<line x1="13" y1="-4" x2="19" y2="-11" stroke="#9A8CF0" stroke-opacity="0.95"')
    ground = swap(ground, '<circle cx="20" cy="-13" r="3" fill="#FFFFFF" fill-opacity="0.95"/>', '<circle cx="20" cy="-13" r="3" fill="#FFFFFF" fill-opacity="0.95" stroke="#9A8CF0" stroke-width="1"/>')
    head = swap(head, '<rect x="-14" y="-26" width="28" height="34" rx="8" fill="#FFFFFF" fill-opacity="0.93"/>',
                '<rect x="-14" y="-26" width="28" height="34" rx="8" fill="#FFFFFF" fill-opacity="0.93" stroke="#9A8CF0" stroke-width="1.2"/>')
    # the sparkle and the bot's antenna stalk are shared definitions, so recolour them here too
    head = swap(head, f'Z" fill="{CHART["dark"]["star"]}"', f'Z" fill="{CHART["light"]["star"]}"')
    head = swap(head, '<line x1="0" y1="-26" x2="0" y2="-33" stroke="#FFFFFF" stroke-opacity="0.9"', '<line x1="0" y1="-26" x2="0" y2="-33" stroke="#1F2440" stroke-opacity="0.9"')
    # white legs vanish against the pale horizon, so they take the outline's purple
    for x in (-6, 6):
        head = swap(head, f'<line x1="{x}" y1="8" x2="{x}" y2="15" stroke="#FFFFFF"', f'<line x1="{x}" y1="8" x2="{x}" y2="15" stroke="#9A8CF0"')
    head = swap(head, 'A quiet moonscape at night', 'A quiet moonscape at dawn')
    out = head + '<!-- background starfield -->' + sky + '<!-- the moon surface -->' + ground
    (OUT / "banner-light.svg").write_text(out)
    print("wrote banner-light.svg", f"{len(out)//1024} KB")



WORK = [  # (organisation, [(repo, name, suffix, language, summary), ...]); cards sit 2 to a row
    ("The Graph", [
        ("edgeandnode/dipper", "dipper", "", "Rust",
         "The direct indexer payments gateway for The Graph. Sends and manages the state of indexing agreements."),
        ("graphprotocol/indexer-rs", "indexer-rs", "", "Rust",
         "The service that indexers run to receive, verify and answer indexing agreement proposals."),
        ("edgeandnode/subgraph-dips-indexer-selection", "subgraph-dips-indexer-selection", "(IISA)", "Python",
         "This service uses a selection algorithm to pick indexers to serve paid indexing agreements, "
         "minimising gateway cost and latency while maximising decentralisation, success "
         "rate and uptime."),
        ("graphprotocol/rewards-eligibility-oracle", "rewards-eligibility-oracle", "", "Python",
         "This oracle decides which indexers qualify for indexing rewards, using a binary "
         "eligibility algorithm and records the decision into the RewardsEligibilityOracle contract on Arbitrum."),
    ]),
]
# the portfolio sits under WORK as its own group: 1 wide card that links to the site
SITE = ("https://moonboi9001.github.io/", "moonboi9001.github.io",
        "The story behind the work above, with numbers from production, plus my smart contract security and "
        "cross-chain GRT work. Outside work: an at-home LLM GPU workstation, a stock options data pipeline and my "
        "own Graph indexer and archive nodes.")
LANGUAGES = {"Rust": "#dea584", "Python": "#3572A5", "Go": "#00ADD8", "TypeScript": "#3178c6"}  # GitHub's colours
CARD_THEMES = {
    "light": {"top": "#eaf0fa", "bottom": "#fbfaf7", "edge": "#d1d9e0", "ink": "#1f2328", "muted": "#59636e",
              "line": CHART["light"]["line"], "star": CHART["light"]["star"], "strip": "#f6f8fa", "link": "#0969da",
              "rule": "#d1d9e0", "glow": "#ffffff", "glow_opacity": "0.9", "moon_edge": "#c4bfb3"},
    "dark": {"top": "#121b31", "bottom": "#0d1117", "edge": "#2e3a52", "ink": "#f0f6fc", "muted": "#9198a1",
             "line": CHART["dark"]["line"], "star": CHART["dark"]["star"], "strip": "#151b23", "link": "#4493f8",
             "rule": "#3d444d", "glow": "#f5f2e4", "glow_opacity": "0.14", "moon_edge": "#b7b4a4"},
}
MERGED = "/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged"
CARDS = OUT / "cards"
WRAP = 57          # characters per summary line; 57 fits the 440-wide card in GitHub's system fonts
MOTIF = [(350, 44), (363, 33), (376, 37), (390, 22), (403, 26), (417, 12)]   # a tiny rising star chart


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def wrap(text, w=440):
    """Break a summary into lines for a card w units wide; the text keeps 24 units clear of each side."""
    limit = WRAP * (w - 48) // (440 - 48)
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{html.escape(label)}" font-family="{SANS}">\n{body}\n</svg>\n')


def card(palette, w, h, label, dot, title, summary, corner, alt):
    """A dot and label, a bold title and a wrapped summary on a soft gradient, with art in the top right corner."""
    lines = "".join(f'<tspan x="24" y="{104 + i * 21}">{html.escape(t)}</tspan>' for i, t in enumerate(wrap(summary, w)))
    return svg(w, h, alt, f"""  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{palette['top']}"/><stop offset="1" stop-color="{palette['bottom']}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="url(#bg)" stroke="{palette['edge']}" stroke-width="1.5"/>
{corner}
  <circle cx="29" cy="34" r="5" fill="{dot}"/>
  <text x="41" y="38.5" font-size="13" fill="{palette['muted']}">{html.escape(label)}</text>
  <text x="24" y="74" font-size="18" font-weight="700" fill="{palette['ink']}">{title}</text>
  <text font-size="14.5" fill="{palette['ink']}" fill-opacity="0.88">{lines}</text>""")


def project(palette, name, suffix, language, summary, h):
    """1 project: language, name and summary, with a tiny rising star chart in the corner."""
    e = html.escape
    chart = " ".join(f"{x},{y}" for x, y in MOTIF)
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="{2.8 if i == len(MOTIF) - 1 else 1.9}"/>' for i, (x, y) in enumerate(MOTIF))
    corner = (f'  <polyline points="{chart}" fill="none" stroke="{palette["line"]}" stroke-width="1.2" stroke-opacity="0.55"/>\n'
              f'  <g fill="{palette["star"]}">{dots}</g>')
    title = e(name) + (f' <tspan font-weight="400" fill="{palette["muted"]}">{e(suffix)}</tspan>' if suffix else "")
    return card(palette, 440, h, language, LANGUAGES[language], title, summary, corner,
                f"{name} {suffix}".strip() + f", {language}: {summary}")


def moon(palette, cx, cy):
    """The portfolio site's moon, lit from the top left, with 2 craters and a few stars beside it."""
    return f"""  <defs>
    <radialGradient id="moon" cx="0.38" cy="0.34" r="0.75">
      <stop offset="0" stop-color="#f5f2e4"/><stop offset="0.55" stop-color="#d9d6c6"/><stop offset="1" stop-color="#b7b4a4"/>
    </radialGradient>
    <radialGradient id="glow">
      <stop offset="0.6" stop-color="{palette['glow']}" stop-opacity="{palette['glow_opacity']}"/><stop offset="1" stop-color="{palette['glow']}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="{cx}" cy="{cy}" r="36" fill="url(#glow)"/>
  <circle cx="{cx}" cy="{cy}" r="22" fill="url(#moon)" stroke="{palette['moon_edge']}" stroke-width="1"/>
  <g fill="#b7b4a4" fill-opacity="0.6"><circle cx="{cx - 7}" cy="{cy - 6}" r="5"/><circle cx="{cx + 9}" cy="{cy + 7}" r="3.2"/></g>
  <g fill="{palette['star']}"><circle cx="{cx - 58}" cy="{cy - 14}" r="1.9"/><circle cx="{cx - 44}" cy="{cy + 16}" r="1.4"/><circle cx="{cx - 80}" cy="{cy + 4}" r="1.2"/></g>"""


def strip(palette, text, w=440):
    """A link bar under a card, such as 'See my merged changes'; cards that share one differ only in the link."""
    return svg(w, 40, text, f"""  <rect x="1" y="1" width="{w - 2}" height="38" rx="10" fill="{palette['strip']}" stroke="{palette['edge']}" stroke-width="1.5"/>
  <text x="{w // 2}" y="25" text-anchor="middle" font-size="14" font-weight="500" fill="{palette['link']}">{html.escape(text)}</text>""")


def header(palette, organisation, count=""):
    """The organisation's name, a rule, and how many projects follow if any, lined up with the cards' text."""
    rule_start = round(31 + len(organisation) * 13.8 + 18)                 # 13.8 is roughly 1 bold 24px character
    rule_end = round(867 - len(count) * 7 - 18) if count else 867          # 7 is roughly 1 regular 13px character
    tally = f'\n  <text x="867" y="37" text-anchor="end" font-size="13" fill="{palette["muted"]}">{count}</text>' if count else ""
    return svg(900, 64, organisation, f"""  <text x="31" y="41" font-size="24" font-weight="700" fill="{palette['ink']}">{html.escape(organisation)}</text>
  <line x1="{rule_start}" y1="32" x2="{rule_end}" y2="32" stroke="{palette['rule']}" stroke-width="1.5"/>{tally}""")


def picture(name, alt, width):
    src = f"./assets/cards/{name}"
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{src}-dark.svg">'
            f'<img src="{src}-light.svg" width="{width}" alt="{html.escape(alt)}"></picture>')


def portfolio():
    """The portfolio group: a header, 1 card as wide as a row of 2 so its text lines up, and a bar linking to the site.

    The card and bar take 98.5% of the page rather than 98% to cover the gap between the 2 cards in a row above.
    """
    url, name, summary = SITE
    w = 2 * 440
    h = 126 + 21 * (len(wrap(summary, w)) - 1)
    for theme, palette in CARD_THEMES.items():
        (CARDS / f"portfolio-{theme}.svg").write_text(header(palette, "Portfolio"))
        (CARDS / f"site-{theme}.svg").write_text(
            card(palette, w, h, "Website", palette["star"], html.escape(name), summary, moon(palette, w - 46, 40), f"{name}, my portfolio: {summary}"))
        (CARDS / f"visit-{theme}.svg").write_text(strip(palette, "Visit my portfolio", w))
    return (f'<p align="center">{picture("portfolio", "Portfolio", "100%")}</p>\n\n'
            f'<p align="center">\n<a href="{url}">{picture("site", f"{name}, my portfolio: {summary}", "98.5%")}</a>\n<br>\n'
            f'<a href="{url}">{picture("visit", "Visit my portfolio", "98.5%")}</a>\n</p>')


def work_cards():
    """Write every card, strip and header as a light and dark SVG, and return the README markup for them."""
    for old in CARDS.glob("*.svg"):
        old.unlink()
    CARDS.mkdir(exist_ok=True)
    for theme, palette in CARD_THEMES.items():
        (CARDS / f"merged-{theme}.svg").write_text(strip(palette, "See my merged changes"))
    sections = []
    for organisation, projects in WORK:
        count = f"{len(projects)} selected project{'s' if len(projects) != 1 else ''}"
        for theme, palette in CARD_THEMES.items():
            (CARDS / f"{slug(organisation)}-{theme}.svg").write_text(header(palette, organisation, count))
        rows = [f'<p align="center">{picture(slug(organisation), organisation, "100%")}</p>']
        for i in range(0, len(projects), 2):
            row = projects[i:i + 2]
            h = 126 + 21 * (max(len(wrap(p[4])) for p in row) - 1)   # both cards in a row share a height
            cards, strips = [], []
            for repo, name, suffix, language, summary in row:
                for theme, palette in CARD_THEMES.items():
                    (CARDS / f"{slug(name)}-{theme}.svg").write_text(project(palette, name, suffix, language, summary, h))
                title = f"{name} {suffix}".strip()
                cards.append(f'<a href="https://github.com/{repo}">'
                             f'{picture(slug(name), f"{title}, {language}: {summary}", "49%")}</a>')
                strips.append(f'<a href="https://github.com/{repo}{MERGED}">'
                              f'{picture("merged", f"See my merged changes to {name}", "49%")}</a>')
            rows.append('<p align="center">\n' + "\n".join(cards) + "\n<br>\n" + "\n".join(strips) + "\n</p>")
        sections.append("\n\n".join(rows))
    sections.append(portfolio())
    print(f"wrote {len(list(CARDS.glob('*.svg')))} card SVGs")
    return "\n\n".join(sections)


listed = constellation()
light_banner()
readme = OUT.parent / "README.md"
text, count = re.subn(r"a star for each of .*? and \w+", f"a star for each of {listed}", readme.read_text())
assert count == 1, "banner alt text not found in README.md"
section = work_cards()
text, count = re.subn(r"(<!-- selected work: generated by assets/build.py -->\n).*?(\n<!-- end of selected work -->)",
                      lambda m: m.group(1) + section + m.group(2), text, flags=re.S)
assert count == 1, "selected work markers not found in README.md"
readme.write_text(text)
