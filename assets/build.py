#!/usr/bin/env python3
"""Generate the README's themed SVG assets.

Run from the repo root: python3 assets/build.py. It rewrites the constellation in the hand-drawn
banner-dark.svg from the STARS list (edit that list to add or remove a skill), keeps the alt text in
the SVG and README in step, and derives banner-light.svg from the dark one by recolouring it.
"""
import re
from pathlib import Path

OUT = Path(__file__).parent


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
    a = s.index('<g class="stars"')
    b = s.index('</g>', a)
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
text, count = re.subn(r"a star for each of .*? and \w+", f"a star for each of {listed}", readme.read_text())
assert count == 1, "banner alt text not found in README.md"
readme.write_text(text)
