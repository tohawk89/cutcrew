"""Reusable SVG parts for explainer scenes (1920x1080 canvas). Every function returns an SVG string.

Text uses class "t" (font set by the film's CSS). Ids passed in become animation targets.
"""

NAVY, GREY, WHITE = "#2F2A5B", "#6B6790", "#FFFFFF"


def text(x, y, s, size=40, anchor="middle", color=NAVY, weight=700):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="t" font-size="{size}" '
            f'style="fill:{color};font-weight:{weight}">{s}</text>')


def svg(inner, bg, w=1920, h=1080):
    return (f'<svg class="art" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>{inner}</svg>')


def g(id_, inner, cls=None):
    c = f' class="{cls}"' if cls else ""
    return f'<g id="{id_}"{c}>{inner}</g>' if id_ else f'<g{c}>{inner}</g>'


def crack(cx, top, length, w=9, color="#4A3A32", edge="#FBF6EC"):
    """Filled jagged crack (2 tones: dark body + light edge), drawn top to bottom."""
    n = 8
    pts = [(cx + (14 if i % 2 else -14) * (0.6 + 0.4 * (i % 3) / 2), top + length * i / (n - 1)) for i in range(n)]
    widths = [1, w * .6, w * .9, w, w, w * .8, w * .5, 1]
    left = [(x - ww, y) for (x, y), ww in zip(pts, widths)]
    right = [(x + ww, y) for (x, y), ww in zip(pts, widths)]
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in left + right[::-1])
    edge_p = " ".join(f"{x+4:.0f},{y+3:.0f}" for x, y in left + right[::-1])
    bx, by = pts[3]
    branch = f'<polygon points="{bx:.0f},{by-4:.0f} {bx+length*.18:.0f},{by+length*.06:.0f} {bx:.0f},{by+6:.0f}" fill="{color}"/>'
    return f'<polygon points="{edge_p}" fill="{edge}"/><polygon points="{poly}" fill="{color}"/>{branch}'


def sparkle(x, y, r, color="#F2B630"):
    return (f'<path d="M{x},{y-r} Q{x+r*.18},{y-r*.18} {x+r},{y} Q{x+r*.18},{y+r*.18} {x},{y+r} '
            f'Q{x-r*.18},{y+r*.18} {x-r},{y} Q{x-r*.18},{y-r*.18} {x},{y-r} Z" fill="{color}"/>')


def logo(href, x, y, w, ratio, white=False):
    """Image logo centred on (x, y). ratio = height/width of the file. white=True for dark backgrounds."""
    h = w * ratio
    flt = ' style="filter:brightness(0) invert(1)"' if white else ""
    return f'<image href="{href}" x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}"{flt}/>'


def house(roof=NAVY, roof_sh="#24204A", door="#3FC1AE", door_sh="#30A492", wall="#F7F3EA", wall_sh="#EAE2D3",
          window="#BFE8E1"):
    """Simple 2-tone house, origin at the bottom centre, ~370 wide x 360 tall."""
    return (f'<rect x="-150" y="-230" width="300" height="230" fill="{wall}"/>'
            f'<rect x="20" y="-230" width="130" height="230" fill="{wall_sh}"/>'
            f'<polygon points="-185,-225 0,-360 185,-225" fill="{roof}"/>'
            f'<polygon points="0,-360 185,-225 120,-225" fill="{roof_sh}"/>'
            f'<rect x="85" y="-340" width="34" height="70" fill="#4A4478"/>'
            f'<rect x="-30" y="-120" width="60" height="120" rx="6" fill="{door}"/>'
            f'<rect x="10" y="-120" width="20" height="120" fill="{door_sh}"/>'
            f'<circle cx="-14" cy="-60" r="5" fill="{roof}"/>'
            f'<rect x="-120" y="-170" width="62" height="56" rx="6" fill="{window}"/>'
            f'<rect x="58" y="-170" width="62" height="56" rx="6" fill="{window}"/>')


def card_frame(x, y, label, w=380, h=520, inner_bg="#F1EADF"):
    """White card with a picture area and a label: for 'problem' rows (cracked walls, leaks...)."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="26" fill="#FFFFFF"/>'
            f'<rect x="{x+20}" y="{y+20}" width="{w-40}" height="{w-40}" rx="16" fill="{inner_bg}"/>'
            + text(x + w / 2, y + h - 52, label, 34))


# ---- icons for "how it works" cards (centred on cx, cy) ----
def icon_house_pin(cx, cy, pin="#F08C3A", **house_kw):
    return (f'<g transform="translate({cx},{cy+110}) scale(0.62)">{house(**house_kw)}</g>'
            f'<path d="M{cx+95},{cy-120} c-36,0 -52,26 -52,50 c0,36 52,84 52,84 c0,0 52,-48 52,-84 c0,-24 -16,-50 -52,-50 Z" fill="{pin}"/>'
            f'<circle cx="{cx+95}" cy="{cy-70}" r="18" fill="#FFFFFF"/>')


def icon_checklist(cx, cy, board=NAVY, tick="#3FC1AE"):
    s = (f'<rect x="{cx-110}" y="{cy-140}" width="220" height="270" rx="18" fill="{board}"/>'
         f'<rect x="{cx-92}" y="{cy-112}" width="184" height="226" rx="10" fill="#FFFFFF"/>'
         f'<rect x="{cx-40}" y="{cy-158}" width="80" height="36" rx="10" fill="#4A4478"/>')
    for r in range(3):
        ry = cy - 80 + r * 64
        s += (f'<rect x="{cx-70}" y="{ry}" width="40" height="40" rx="8" fill="#E4F5F1"/>'
              f'<path d="M{cx-62},{ry+20} l10,10 l18,-20" stroke="{tick}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
              f'<rect x="{cx-16}" y="{ry+12}" width="{90 - r*14}" height="16" rx="8" fill="#D9D6E6"/>')
    return s


def icon_camera(cx, cy, body=NAVY, lens="#3FC1AE"):
    return (f'<rect x="{cx-120}" y="{cy-80}" width="240" height="170" rx="26" fill="{body}"/>'
            f'<rect x="{cx-50}" y="{cy-110}" width="100" height="44" rx="12" fill="{body}"/>'
            f'<circle cx="{cx}" cy="{cy+6}" r="62" fill="#FFFFFF"/><circle cx="{cx}" cy="{cy+6}" r="44" fill="{lens}"/>'
            f'<circle cx="{cx-14}" cy="{cy-8}" r="12" fill="#FFFFFF" opacity="0.7"/>'
            + sparkle(cx + 130, cy - 120, 34) + sparkle(cx + 160, cy - 60, 16))


def icon_report(cx, cy, arrow="#3FC1AE", tag="#F08C3A"):
    """PDF sheet -> generic chat bubble + envelope (no brand logos)."""
    return (f'<rect x="{cx-150}" y="{cy-130}" width="170" height="220" rx="14" fill="#F1EEF6"/>'
            f'<rect x="{cx-150}" y="{cy-60}" width="96" height="44" rx="10" fill="{tag}"/>'
            + text(cx - 102, cy - 28, "PDF", 30, color="#FFFFFF") +
            f'<rect x="{cx-128}" y="{cy}" width="120" height="14" rx="7" fill="#D9D6E6"/>'
            f'<rect x="{cx-128}" y="{cy+28}" width="90" height="14" rx="7" fill="#D9D6E6"/>'
            f'<path d="M{cx+30},{cy-20} L{cx+80},{cy-20}" stroke="{arrow}" stroke-width="10" stroke-linecap="round"/>'
            f'<path d="M{cx+66},{cy-38} L{cx+86},{cy-20} L{cx+66},{cy-2}" stroke="{arrow}" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{cx+140}" cy="{cy-80}" r="44" fill="#3DBE6B"/><path d="M{cx+110},{cy-48} l-14,26 l30,-12 Z" fill="#3DBE6B"/>'
            f'<rect x="{cx+96}" y="{cy+10}" width="92" height="64" rx="10" fill="{NAVY}"/>'
            f'<path d="M{cx+100},{cy+16} L{cx+142},{cy+48} L{cx+184},{cy+16}" stroke="#FFFFFF" stroke-width="6" fill="none" stroke-linejoin="round"/>')


ICONS = {"house": icon_house_pin, "checklist": icon_checklist, "camera": icon_camera, "report": icon_report}


def step_cards(steps, num_bg="#23897A", id_prefix="hw-c", y=190):
    """'How it works' cards. steps = [(title, [benefit lines], icon_name_or_svg_fn)], up to 4 in a row.
    Returns (svg, ids) so each card can rise in on its voice line."""
    n = len(steps)
    w, gapx = 410, 40
    x0 = (1920 - (n * w + (n - 1) * gapx)) / 2
    out, ids = "", []
    for i, (title, lines, icon) in enumerate(steps):
        x = x0 + i * (w + gapx)
        cx = x + w / 2
        body = (f'<rect x="{x}" y="{y}" width="{w}" height="640" rx="28" fill="#FFFFFF"/>'
                f'<circle cx="{x+56}" cy="{y+56}" r="32" fill="{num_bg}"/>' + text(x + 56, y + 70, str(i + 1), 38, color="#FFFFFF"))
        fn = ICONS.get(icon, icon) if isinstance(icon, str) else icon
        if callable(fn):
            body += fn(cx, y + 290)
        body += text(cx, y + 500, title, 34)
        for k, line in enumerate(lines):
            body += text(cx, y + 552 + k * 36, line, 29, color=GREY, weight=500)
        ids.append(f"{id_prefix}{i}")
        out += g(ids[-1], body)
    return out, ids


def badge(text_s, y=880, bg=NAVY, w=1000):
    x = (1920 - w) / 2
    return (f'<rect x="{x}" y="{y}" width="{w}" height="84" rx="42" fill="{bg}"/>'
            + text(960, y + 55, text_s, 30, color="#FFFFFF", weight=600))


def step_list(labels, id_prefix="sl", x=1260, y0=300, dy=130, now="#C95A14", done="#23897A"):
    """List of steps beside the phone. Each row has 3 layers: #<p>-base<i> (grey), #<p>-now<i>, #<p>-done<i>.
    Use Film.step_list_states() to light them up in time."""
    rows = ""
    for i, label in enumerate(labels):
        y = y0 + i * dy
        rows += (f'<g id="{id_prefix}-row{i}"><g id="{id_prefix}-base{i}"><circle cx="{x}" cy="{y}" r="34" fill="#E3DED4"/>'
                 + text(x, y + 13, str(i + 1), 34, color=GREY) + text(x + 60, y + 14, label, 42, anchor="start", color=GREY, weight=600) + '</g>'
                 + f'<g id="{id_prefix}-now{i}" opacity="0"><circle cx="{x}" cy="{y}" r="34" fill="{now}"/>' + text(x, y + 13, str(i + 1), 34, color="#FFFFFF")
                 + text(x + 60, y + 14, label, 42, anchor="start", color=NAVY) + '</g>'
                 + f'<g id="{id_prefix}-done{i}" opacity="0"><circle cx="{x}" cy="{y}" r="34" fill="{done}"/>' + text(x, y + 13, "✓", 34, color="#FFFFFF")
                 + text(x + 60, y + 14, label, 42, anchor="start", color=NAVY, weight=600) + '</g></g>')
    return f'<g id="{id_prefix}-rows">{rows}</g>'


def credits(rows, logo_svg="", url="", url_color="#3FC1AE", line="#4A4478",
            label_color="#9C98C2", value_color="#FFFFFF", link_color="#7FD9CB"):
    """Approved credits card: logo + url on top, a line, then two columns. rows = [(label, value, link_or_None)].
    Rows get class 's-cr-row' for a staggered entrance."""
    cr = f'<line x1="560" y1="465" x2="1360" y2="465" stroke="{line}" stroke-width="2"/>'
    top = 540 if len(rows) <= 5 else 500
    for i, (lbl, val, extra) in enumerate(rows):
        y = top + i * 66
        tail = (f'<tspan dx="16" style="fill:{link_color};font-weight:500" font-size="28">· {extra}</tspan>') if extra else ""
        cr += ('<g class="s-cr-row">' + text(800, y, (lbl or "").upper(), 24, anchor="end", color=label_color, weight=600)
               + f'<text x="836" y="{y}" text-anchor="start" class="t" font-size="34" '
                 f'style="fill:{value_color};font-weight:{700 if i == 0 else 600}">{val}{tail}</text></g>')
    return (g("cr-logo", logo_svg) + (g("cr-url", text(960, 400, url, 44, color=url_color)) if url else "") + g("cr-rows", cr))


def phone_rig(clips, start, end, skin="#F4A07F", skin_sh="#DE8467", sleeve="#3FC1AE", sleeve_sh="#30A492",
              body="#2F2A5B", tilt=-5):
    """Cartoon hand holding a phone that plays real 9:16 clips (user-approved grip: round fist behind the
    bottom-right corner, thumb on the edge). clips = [(src, offset_in_scene, duration, media_start, rate)].
    Returns (html, css). The rig lives at the root (videos can't sit inside a timed element):
    #rig-back, #phone-rig, #rig-front. Move them together with Film.phone_in_out()."""
    vids = "".join(
        f'<video id="pv{i}" src="{src}" muted playsinline data-start="{round(start+off,3)}" data-duration="{round(d,3)}" '
        f'data-media-start="{ms}" data-playback-rate="{r}" data-track-index="{31+i}"></video>'
        for i, (src, off, d, ms, r) in enumerate(clips))
    back = (f'<svg class="art" viewBox="0 0 1920 1080" width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">'
            f'<polygon points="990,990 1120,880 1560,1180 1290,1180" fill="{sleeve}"/>'
            f'<polygon points="990,990 1045,944 1380,1180 1290,1180" fill="{sleeve_sh}"/>'
            f'<polygon points="1005,978 1120,880 1165,915 1050,1015" fill="{sleeve_sh}"/>'
            f'<circle cx="1010" cy="905" r="128" fill="{skin}"/>'
            f'<path d="M1110,825 A128,128 0 0,1 1030,1031 A140,140 0 0,0 1110,825 Z" fill="{skin_sh}"/></svg>')
    front = (f'<svg class="art" viewBox="0 0 1920 1080" width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">'
             f'<ellipse cx="1052" cy="810" rx="46" ry="32" fill="{skin}" transform="rotate(-30 1052 810)"/>'
             f'<ellipse cx="1030" cy="803" rx="17" ry="11" fill="{skin_sh}" opacity="0.65" transform="rotate(-30 1030 803)"/></svg>')
    d = round(end - start, 3)
    html = (f'<div class="rig" id="rig-back"><div id="rig-back-art" class="clip" data-start="{start}" data-duration="{d}" data-track-index="30">{back}</div></div>'
            f'<div id="phone-rig"><div id="phone-body" class="clip" data-start="{start}" data-duration="{d}" data-track-index="30"></div>'
            f'<div class="screen">{vids}</div>'
            f'<div id="phone-notch" class="clip" data-start="{start}" data-duration="{d}" data-track-index="30"></div></div>'
            f'<div class="rig" id="rig-front"><div id="rig-front-art" class="clip" data-start="{start}" data-duration="{d}" data-track-index="36">{front}</div></div>')
    css = (".rig { position: absolute; inset: 0; }\n"
           "#phone-rig { position: absolute; left: 500px; top: 20px; width: 534px; height: 920px; }\n"
           f"#phone-body {{ position: absolute; inset: 0; background: {body}; border-radius: 58px; }}\n"
           ".screen { position: absolute; left: 20px; top: 22px; width: 494px; height: 876px; border-radius: 42px; overflow: hidden; }\n"
           ".screen video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }\n"
           f"#phone-notch {{ position: absolute; left: 217px; top: 36px; width: 100px; height: 22px; border-radius: 11px; background: {body}; right: auto; bottom: auto; }}\n")
    setup = f'gsap.set("#phone-rig", {{ rotation: {tilt}, transformOrigin: "50% 50%" }});'
    return html, css, setup
