#!/usr/bin/env python3
"""Generate the README's themed SVG assets.

Run from the repo root: python3 assets/build.py. It rewrites the constellation in the hand-drawn
banner-dark.svg from the STARS list (edit that list to add or remove a skill), keeps the alt text in
the SVG and README in step, and derives banner-light.svg from the dark one by recolouring it.
"""
import random
import re
from pathlib import Path

OUT = Path(__file__).parent
W = 1200
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "dark": dict(edge="#0d1117", sky="#0F1136", ink="#FFFFFF", star="#FFFFFF"),
    "light": dict(edge="#ffffff", sky="#D9E0F7", ink="#1F2440", star="#3B4A8C"),
}


def stars(T, seed, h, n, avoid):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        x, y = rng.randint(12, W - 12), rng.randint(12, h - 12)
        if avoid(x, y):
            continue
        r = rng.choice([1, 1, 1.2, 1.4])
        o = rng.choice([0.35, 0.4, 0.5, 0.6])
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill-opacity="{o}"/>')
    return f'<g class="stars" fill="{T["star"]}">' + "".join(out) + "</g>"

def label_offset(i, y, neighbours, n):
    """Where a star's label sits: above peaks, below dips, so it never crosses the lines either side."""
    if i == n - 1:
        return -10, -18            # the brightest star is a peak, so its label sits above it too
    above = y <= sum(neighbours) / len(neighbours)
    return (0, -16) if above else (0, 22)


def constellation(theme):
    """The stack as labelled stars joined into 1 constellation that draws itself in."""
    T = THEMES[theme]
    h = 190
    pts = [("Rust", 120, 130), ("Python", 270, 70), ("TypeScript", 410, 140), ("PostgreSQL", 560, 50),
           ("Kafka", 700, 120), ("Redpanda", 820, 40), ("Kubernetes", 960, 130), ("Ethereum", 1100, 62)]
    poly = " ".join(f"{x},{y}" for _, x, y in pts)
    nodes = ""
    for i, (t, x, y) in enumerate(pts):
        dy = 34 if y < 90 else -22
        nodes += f'''
  <g class="fade d{i+1}">
    <circle cx="{x}" cy="{y}" r="9" fill="{T['ink']}" fill-opacity="0.1"/>
    <circle cx="{x}" cy="{y}" r="3" fill="{T['ink']}" fill-opacity="0.95"/>
    <text x="{x}" y="{y+dy}" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{T['ink']}" fill-opacity="0.85">{t}</text>
  </g>'''
    avoid = lambda x, y: any(abs(x - px) < 60 and abs(y - py) < 50 for _, px, py in pts)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="The stack drawn as a constellation: Rust, Python, TypeScript, PostgreSQL, Kafka, Redpanda, Kubernetes and Ethereum">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{T['edge']}"/>
      <stop offset="26%" stop-color="{T['sky']}"/>
      <stop offset="74%" stop-color="{T['sky']}"/>
      <stop offset="100%" stop-color="{T['edge']}"/>
    </linearGradient>
    <style>
      .stars circle {{ animation: twinkle 4.2s ease-in-out infinite alternate; }}
      .stars circle:nth-of-type(2n) {{ animation-duration: 5.4s; animation-delay: 1.1s; }}
      .stars circle:nth-of-type(3n) {{ animation-duration: 6.2s; animation-delay: 2.3s; }}
      .stars circle:nth-of-type(5n) {{ animation-duration: 7s; animation-delay: 0.6s; }}
      @keyframes twinkle {{ from {{ opacity: 1; }} to {{ opacity: 0.3; }} }}
      .draw {{ stroke-dasharray: 1400; stroke-dashoffset: 1400; animation: draw 3s ease-out forwards; }}
      @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
      .fade {{ opacity: 0; animation: fade 1.2s ease-out forwards; }}
      @keyframes fade {{ to {{ opacity: 1; }} }}
      .d1 {{ animation-delay: 0.4s; }} .d2 {{ animation-delay: 0.9s; }} .d3 {{ animation-delay: 1.4s; }}
      .d4 {{ animation-delay: 1.9s; }} .d5 {{ animation-delay: 2.4s; }} .d6 {{ animation-delay: 2.9s; }}
      .d7 {{ animation-delay: 3.4s; }} .d8 {{ animation-delay: 3.9s; }}
      @media (prefers-reduced-motion: reduce) {{
        * {{ animation: none !important; }}
        .draw {{ stroke-dashoffset: 0; }} .fade {{ opacity: 1; }}
      }}
    </style>
  </defs>
  <rect width="{W}" height="{h}" fill="url(#sky)"/>
  {stars(T, 7, h, 40, avoid)}
  <polyline class="draw" points="{poly}" fill="none" stroke="{T['ink']}" stroke-opacity="0.3" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>{nodes}
</svg>
'''
    (OUT / f"stack-{theme}.svg").write_text(svg)
    print(f"wrote stack-{theme}.svg", f"{len(svg)//1024} KB")


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
    x0, x1, y0, y1, amp = 165, 1040, 250, 80, 26
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
            verts.append(f'      <g class="vspark">\n        <circle cx="{x}" cy="{y}" r="7" fill="#FFFFFF" fill-opacity="0.12"/>\n        <use href="#sparkle" transform="translate({x},{y})"/>\n        {label}\n      </g>')
        else:
            r, o = (2.2, 0.95) if i % 2 else (1.9, 0.85)
            verts.append(f'      <g class="v{i+1}">\n        <circle cx="{x}" cy="{y}" r="5" fill="#FFFFFF" fill-opacity="0.1"/>\n        <circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" fill-opacity="{o}"/>\n        {label}\n      </g>')
    a = s.index('      <polyline class="cline"')
    b = s.index('      <text class="caption"')
    s = (s[:a] + f'      <polyline class="cline" points="{poly}"\n                fill="none" stroke="#FFFFFF" stroke-opacity="0.3" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>\n'
         + "\n".join(verts) + "\n" + s[b:])
    # point the telescope at the final star and run the sight line from its eyepiece to the star
    ex, ey = pts[-1][1], pts[-1][2]
    tx, ty = 958, 128 + 190                      # telescope pivot in banner coordinates
    angle = math.degrees(math.atan2(ex - tx, ty - ey))   # 0 is straight up, positive leans right
    s = re.sub(r'<g transform="rotate\(-?[\d.]+\)">', f'<g transform="rotate({angle:.0f})">', s)
    sx = round(tx - 16 * math.sin(math.radians(angle)))
    sy = round(ty - 16 * math.cos(math.radians(angle))) - 190
    s = re.sub(r'<line class="sight" x1="-?\d+" y1="-?\d+" x2="-?\d+" y2="-?\d+"', f'<line class="sight" x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey - 190 + 8}"', s)
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
    a = s.index('<g class="stars"'); b = s.index('</g>', a)
    stars_block = re.sub(r'\s*<circle cx="([\d.]+)" cy="([\d.]+)" r="[\d.]+" fill-opacity="[\d.]+"/>', keep, s[a:b])
    s = s[:a] + stars_block + s[b:]
    listed = ", ".join(STARS[:-1]) + " and " + STARS[-1]
    s = re.sub(r'with a star for each of .*? and \w+,', f'with a star for each of {listed},', s)
    p.write_text(s)
    print(f"constellation: {n} stars, path {round(L)}, dash {dash}")
    return listed


def light_banner():
    """Recolour the hand-drawn dark banner into a dawn edition: pale sky, navy stars and lines."""
    s = (OUT / "banner-dark.svg").read_text()
    # sky: fade from the white page into a pale blue dawn
    s = re.sub(r'(<linearGradient id="sky".*?</linearGradient>)',
               '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffffff"/>'
               '<stop offset="30%" stop-color="#D9E0F7"/><stop offset="100%" stop-color="#B9C7F0"/></linearGradient>', s, flags=re.S)
    s = s.replace('stop-color="#C2C7D6"', 'stop-color="#D3D8E6"').replace('stop-color="#848BA1"', 'stop-color="#AEB5C8"')
    # everything white in the sky (stars, constellation, caption, shooting star, flag pole) becomes navy
    head, rest = s.split('<!-- background starfield -->', 1)
    sky, ground = rest.split('<!-- the moon surface -->', 1)
    sky = sky.replace('#FFFFFF', '#1F2440')
    ground = ground.replace('stroke="#F2F4FA"', 'stroke="#1F2440"').replace('stroke="#E8EAF2"', 'stroke="#1F2440"')
    ground = ground.replace('stroke="#B7A6FF"', 'stroke="#3A22A6"').replace('fill="#0B0725"', 'fill="#4A3DB8"')
    ground = ground.replace('stroke="#FFD98A" stroke-opacity="0.25"', 'stroke="#3B4A8C" stroke-opacity="0.45"')
    # the bot stays white but gets an outline so it reads against the pale sky
    ground = ground.replace('<line x1="-13" y1="-8" x2="-24" y2="-18" stroke="#FFFFFF" stroke-opacity="0.93"', '<line x1="-13" y1="-8" x2="-24" y2="-18" stroke="#9A8CF0" stroke-opacity="0.95"')
    ground = ground.replace('<circle cx="-25" cy="-20" r="3" fill="#FFFFFF" fill-opacity="0.95"/>', '<circle cx="-25" cy="-20" r="3" fill="#FFFFFF" fill-opacity="0.95" stroke="#9A8CF0" stroke-width="1"/>')
    ground = ground.replace('<rect x="-14" y="-26" width="28" height="34" rx="8" fill="#FFFFFF" fill-opacity="0.93"/>',
                            '<rect x="-14" y="-26" width="28" height="34" rx="8" fill="#FFFFFF" fill-opacity="0.93" stroke="#9A8CF0" stroke-width="1.2"/>')
    head = head.replace('<rect x="-14" y="-26" width="28" height="34" rx="8" fill="#FFFFFF" fill-opacity="0.93"/>',
                        '<rect x="-14" y="-26" width="28" height="34" rx="8" fill="#FFFFFF" fill-opacity="0.93" stroke="#9A8CF0" stroke-width="1.2"/>')
    head = head.replace('stop-color="#FFFFFF"', 'stop-color="#1F2440"')
    # the sparkle and the bot's antenna stalk are shared definitions, so recolour them here too
    head = head.replace('Z" fill="#FFFFFF" fill-opacity="0.95"/>', 'Z" fill="#1F2440" fill-opacity="0.95"/>')
    head = head.replace('<line x1="0" y1="-26" x2="0" y2="-33" stroke="#FFFFFF" stroke-opacity="0.9"', '<line x1="0" y1="-26" x2="0" y2="-33" stroke="#1F2440" stroke-opacity="0.9"')
    head = head.replace('A quiet moonscape at night', 'A quiet moonscape at dawn')
    sky = sky.replace('fill-opacity="0.65">star chart, not price chart', 'fill-opacity="0.75">star chart, not price chart')
    out = head + '<!-- background starfield -->' + sky + '<!-- the moon surface -->' + ground
    (OUT / "banner-light.svg").write_text(out)
    print("wrote banner-light.svg", f"{len(out)//1024} KB")



listed = constellation()
light_banner()
readme = OUT.parent / "README.md"
readme.write_text(re.sub(r"1 star for each of .*? and \w+", f"1 star for each of {listed}", readme.read_text()))
