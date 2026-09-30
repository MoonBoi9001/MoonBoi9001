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
CHART = {"dark": dict(star="#ffd772", line="#8ea6dc"), "light": dict(star="#c98a12", line="#6d80a6")}


def label_offset(i, y, neighbours, n):
    """Where a star's label sits: above peaks, below dips, so it never crosses the lines either side."""
    if i == n - 1:
        return -10, -18            # the brightest star is a peak, so its label sits above it too
    above = y <= sum(neighbours) / len(neighbours)
    return (0, -16) if above else (0, 22)


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
    x0, x1, y0, y1, amp = 165, 1040, 235, 65, 26
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
    s = re.sub(r'      \.v1 \{ animation: ignite1.*?@keyframes ignite\d+ \{[^\n]*\n(?=      @keyframes captionIn)', "\n".join(css) + "\n", s, flags=re.S)
    s, count = re.subn(r'\.cline, (\.v\d+, )+\.vspark, \.caption,', '.cline, ' + ", ".join(names) + ', .caption,', s)
    assert count == 1, 'reduced-motion selector not found'
    s = re.sub(r'stroke-dasharray: \d+;', f'stroke-dasharray: {dash};', s)
    s = re.sub(r'(0%|4\.5%)(\s+)\{ stroke-dashoffset: \d+; \}', rf'\1\2{{ stroke-dashoffset: {dash}; }}', s)
    s = re.sub(r'(32%|100%)(\s+)\{ stroke-dashoffset: \d+; \}', r'\1\2{ stroke-dashoffset: 0; }', s)
    # vertices
    FONT = 'ui-monospace, SFMono-Regular, Menlo, monospace'
    poly = " ".join(f"{x},{y}" for _, x, y in pts)
    verts = []
    for i, (t, x, y) in enumerate(pts):
        nb = [pts[j][2] for j in (i - 1, i + 1) if 0 <= j < n]
        dx, dy = label_offset(i, y, nb, n)
        label = f'<text x="{x+dx}" y="{y+dy}" text-anchor="middle" font-family="{FONT}" font-size="15" fill="#FFFFFF" fill-opacity="0.8">{t}</text>'
        if i == n - 1:
            verts.append(f'      <g class="vspark">\n        <circle cx="{x}" cy="{y}" r="7" fill="{CHART['dark']['star']}" fill-opacity="0.12"/>\n        <use href="#sparkle" transform="translate({x},{y})"/>\n        {label}\n      </g>')
        else:
            r, o = (2.2, 0.95) if i % 2 else (1.9, 0.85)
            verts.append(f'      <g class="v{i+1}">\n        <circle cx="{x}" cy="{y}" r="5" fill="{CHART['dark']['star']}" fill-opacity="0.1"/>\n        <circle cx="{x}" cy="{y}" r="{r}" fill="{CHART['dark']['star']}" fill-opacity="{o}"/>\n        {label}\n      </g>')
    a = s.index('      <polyline class="cline"')
    b = s.index('      <text class="caption"')
    s = (s[:a] + f'      <polyline class="cline" points="{poly}"\n                fill="none" stroke="{CHART['dark']['line']}" stroke-opacity="0.55" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>\n'
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
    sx = round(tx - 16 * math.sin(math.radians(angle)))
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
    """Recolour the hand-drawn dark banner into a dawn edition: pale sky, navy stars and lines."""
    s = (OUT / "banner-dark.svg").read_text()
    # sky: a pale blue dawn, deepening towards the horizon
    s = re.sub(r'(<linearGradient id="sky".*?</linearGradient>)',
               '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
               '<stop offset="0%" stop-color="#D9E0F7"/><stop offset="100%" stop-color="#B9C7F0"/></linearGradient>', s, flags=re.S)
    s = swap(s, 'stop-color="#C2C7D6"', 'stop-color="#D3D8E6"')
    s = swap(s, 'stop-color="#848BA1"', 'stop-color="#AEB5C8"')
    # everything white in the sky (stars, labels, caption, shooting star, flag pole) becomes navy, and the
    # constellation's gold stars and blue-grey line take their light versions
    head, rest = s.split('<!-- background starfield -->', 1)
    sky, ground = rest.split('<!-- the moon surface -->', 1)
    sky = swap(sky, '#FFFFFF', '#1F2440')
    for part in ("star", "line"):
        sky = swap(sky, CHART["dark"][part], CHART["light"][part])
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
    head = swap(head, 'A quiet moonscape at night', 'A quiet moonscape at dawn')
    sky = swap(sky, 'fill-opacity="0.65">star chart, not price chart', 'fill-opacity="0.75">star chart, not price chart')
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
         "This service uses a selection algorithm to pick the best indexers to serve paid indexing agreements "
         "on each subgraph, minimising gateway cost and latency while maximising decentralisation, success "
         "rate and uptime."),
        ("graphprotocol/rewards-eligibility-oracle", "rewards-eligibility-oracle", "", "Python",
         "This oracle decides which indexers qualify for The Graph's indexing rewards, using a binary "
         "eligibility algorithm and records the decision into the RewardsEligibilityOracle contract on Arbitrum."),
    ]),
]
LANGUAGES = {"Rust": "#dea584", "Python": "#3572A5", "Go": "#00ADD8", "TypeScript": "#3178c6"}  # GitHub's colours
CARD_THEMES = {
    "light": dict(top="#eaf0fa", bottom="#fbfaf7", edge="#d1d9e0", ink="#1f2328", muted="#59636e", line=CHART["light"]["line"],
                  star=CHART["light"]["star"], strip="#f6f8fa", link="#0969da", rule="#d1d9e0"),
    "dark": dict(top="#121b31", bottom="#0d1117", edge="#2e3a52", ink="#f0f6fc", muted="#9198a1", line=CHART["dark"]["line"],
                 star=CHART["dark"]["star"], strip="#151b23", link="#4493f8", rule="#3d444d"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MERGED = "/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged"
CARDS = OUT / "cards"
WRAP = 57          # characters per summary line; 57 fits the 440-wide card in GitHub's system fonts
MOTIF = [(350, 44), (363, 33), (376, 37), (390, 22), (403, 26), (417, 12)]   # a tiny rising star chart


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def wrap(text):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > WRAP:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{html.escape(label)}" font-family="{SANS}">\n{body}\n</svg>\n')


def card(T, name, suffix, language, summary, h):
    """1 project: language, name and summary on a soft gradient, with the star chart in the corner."""
    e = html.escape
    chart = " ".join(f"{x},{y}" for x, y in MOTIF)
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="{2.8 if i == len(MOTIF) - 1 else 1.9}"/>' for i, (x, y) in enumerate(MOTIF))
    title = e(name) + (f' <tspan font-weight="400" fill="{T["muted"]}">{e(suffix)}</tspan>' if suffix else "")
    lines = "".join(f'<tspan x="24" y="{104 + i * 21}">{e(t)}</tspan>' for i, t in enumerate(wrap(summary)))
    return svg(440, h, f"{name} {suffix}".strip() + f", {language}: {summary}", f"""  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{T['top']}"/><stop offset="1" stop-color="{T['bottom']}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="438" height="{h - 2}" rx="12" fill="url(#bg)" stroke="{T['edge']}" stroke-width="1.5"/>
  <polyline points="{chart}" fill="none" stroke="{T['line']}" stroke-width="1.2" stroke-opacity="0.55"/>
  <g fill="{T['star']}">{dots}</g>
  <circle cx="29" cy="34" r="5" fill="{LANGUAGES[language]}"/>
  <text x="41" y="38.5" font-size="13" fill="{T['muted']}">{e(language)}</text>
  <text x="24" y="74" font-size="18" font-weight="700" fill="{T['ink']}">{title}</text>
  <text font-size="14.5" fill="{T['ink']}" fill-opacity="0.88">{lines}</text>""")


def strip(T):
    """The 'See my merged changes' bar under each card; every card shares it, only the link differs."""
    return svg(440, 40, "See my merged changes", f"""  <rect x="1" y="1" width="438" height="38" rx="10" fill="{T['strip']}" stroke="{T['edge']}" stroke-width="1.5"/>
  <text x="220" y="25" text-anchor="middle" font-size="14" font-weight="500" fill="{T['link']}">See my merged changes</text>""")


def header(T, organisation, count):
    """The organisation's name, a rule, and how many projects follow, lined up with the cards' text."""
    rule_start = round(31 + len(organisation) * 13.8 + 18)   # 13.8 is roughly 1 bold 24px character
    rule_end = round(867 - len(count) * 7 - 18)              # 7 is roughly 1 regular 13px character
    return svg(900, 64, organisation, f"""  <text x="31" y="41" font-size="24" font-weight="700" fill="{T['ink']}">{html.escape(organisation)}</text>
  <line x1="{rule_start}" y1="32" x2="{rule_end}" y2="32" stroke="{T['rule']}" stroke-width="1.5"/>
  <text x="867" y="37" text-anchor="end" font-size="13" fill="{T['muted']}">{count}</text>""")


def picture(name, alt, width):
    src = f"./assets/cards/{name}"
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{src}-dark.svg">'
            f'<img src="{src}-light.svg" width="{width}" alt="{html.escape(alt)}"></picture>')


def work_cards():
    """Write every card, strip and header as a light and dark SVG, and return the README markup for them."""
    for old in CARDS.glob("*.svg"):
        old.unlink()
    CARDS.mkdir(exist_ok=True)
    for theme, T in CARD_THEMES.items():
        (CARDS / f"merged-{theme}.svg").write_text(strip(T))
    sections = []
    for organisation, projects in WORK:
        count = f"{len(projects)} selected project{'s' if len(projects) != 1 else ''}"
        for theme, T in CARD_THEMES.items():
            (CARDS / f"{slug(organisation)}-{theme}.svg").write_text(header(T, organisation, count))
        rows = [f'<p align="center">{picture(slug(organisation), organisation, "100%")}</p>']
        for i in range(0, len(projects), 2):
            row = projects[i:i + 2]
            h = 126 + 21 * (max(len(wrap(p[4])) for p in row) - 1)   # both cards in a row share a height
            cards, strips = [], []
            for repo, name, suffix, language, summary in row:
                for theme, T in CARD_THEMES.items():
                    (CARDS / f"{slug(name)}-{theme}.svg").write_text(card(T, name, suffix, language, summary, h))
                title = f"{name} {suffix}".strip()
                cards.append(f'<a href="https://github.com/{repo}">'
                             f'{picture(slug(name), f"{title}, {language}: {summary}", "49%")}</a>')
                strips.append(f'<a href="https://github.com/{repo}{MERGED}">'
                              f'{picture("merged", f"See my merged changes to {name}", "49%")}</a>')
            rows.append('<p align="center">\n' + "\n".join(cards) + "\n<br>\n" + "\n".join(strips) + "\n</p>")
        sections.append("\n\n".join(rows))
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
