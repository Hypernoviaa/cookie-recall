"""Generates the SVG sticker art in cookierecall/web/img.

Every icon is drawn on a 64x64 grid, then wrapped in a "sticker": a thick
cream outline and a soft cocoa drop shadow, so the whole set reads as one
family on both the light home page and the dark chalkboard shop.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "cookierecall" / "web" / "img"

COCOA = "#3B2416"
CHOC = "#5A3522"
CHIP = "#4A2A17"
DOUGH = "#E3A857"
DOUGH_D = "#C27F35"
DOUGH_L = "#F4CC86"
CREAM = "#FFF4DF"
GOLD = "#F5C542"
GOLD_D = "#D98E1A"
RASP = "#E2475B"
PIST = "#8DBF6A"
PIST_D = "#5E9447"
SKY = "#7FC8E8"
SKY_D = "#4E9CC0"
PLUM = "#7A5CC2"
PLUM_D = "#553D96"
STEEL = "#8A9BA8"
STEEL_D = "#5F6F7B"
BRICK = "#C0573F"
BRICK_D = "#8E3B2A"


def sticker(name: str, body: str, defs: str = "") -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 72 72" width="72" height="72">
<defs>
  <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
    <feMorphology in="SourceAlpha" operator="dilate" radius="3" result="fat"/>
    <feFlood flood-color="{CREAM}"/><feComposite in2="fat" operator="in" result="rim"/>
    <feGaussianBlur in="fat" stdDeviation="1.6" result="blur"/>
    <feOffset in="blur" dy="2.2" result="off"/>
    <feFlood flood-color="{COCOA}" flood-opacity=".35"/><feComposite in2="off" operator="in" result="shadow"/>
    <feMerge><feMergeNode in="shadow"/><feMergeNode in="rim"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>{defs}
</defs>
<g filter="url(#sh)">{body}</g>
</svg>
"""
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")


def cookie_body(base=DOUGH, rim=DOUGH_D, light=DOUGH_L, chip=CHIP, bite=True) -> str:
    bite_mask = """<mask id="bite"><rect x="-4" y="-4" width="72" height="72" fill="#fff"/>
      <circle cx="56" cy="10" r="9" fill="#000"/><circle cx="60" cy="20" r="6" fill="#000"/></mask>""" if bite else ""
    m = ' mask="url(#bite)"' if bite else ""
    return f"""{bite_mask}<g{m}>
  <circle cx="32" cy="33" r="27" fill="{rim}"/>
  <circle cx="32" cy="31" r="26" fill="{base}"/>
  <path d="M12 24c4-10 14-17 26-16" stroke="{light}" stroke-width="4" stroke-linecap="round" fill="none" opacity=".9"/>
  <ellipse cx="22" cy="24" rx="4.2" ry="3.4" fill="{chip}" transform="rotate(-20 22 24)"/>
  <ellipse cx="38" cy="20" rx="3.4" ry="2.8" fill="{chip}"/>
  <ellipse cx="44" cy="35" rx="4.6" ry="3.6" fill="{chip}" transform="rotate(25 44 35)"/>
  <ellipse cx="28" cy="40" rx="3.8" ry="3" fill="{chip}"/>
  <ellipse cx="18" cy="38" rx="2.6" ry="2.2" fill="{chip}"/>
  <ellipse cx="35" cy="48" rx="3" ry="2.4" fill="{chip}"/>
  <circle cx="30" cy="30" r="1.2" fill="{rim}"/><circle cx="48" cy="26" r="1" fill="{rim}"/><circle cx="22" cy="48" r="1.1" fill="{rim}"/>
</g>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    sticker("cookie", cookie_body())
    sticker("golden", cookie_body(GOLD, GOLD_D, "#FFF0A8", "#B5651D", bite=False) + f"""
  <path d="M52 6l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#fff"/>
  <path d="M10 46l1.4 3.4 3.4 1.4-3.4 1.4L10 55.6l-1.4-3.4-3.4-1.4 3.4-1.4z" fill="#fff"/>""")

    # ---- buildings -------------------------------------------------------
    sticker("b_mamie", f"""
  <circle cx="32" cy="14" r="9" fill="#D9D6E3"/><circle cx="32" cy="14" r="5" fill="#C4C0D3"/>
  <ellipse cx="32" cy="36" rx="20" ry="21" fill="#D9D6E3"/>
  <ellipse cx="32" cy="38" rx="16" ry="17" fill="#F2C9A0"/>
  <circle cx="25" cy="36" r="5.5" fill="#fff" stroke="{COCOA}" stroke-width="2"/>
  <circle cx="39" cy="36" r="5.5" fill="#fff" stroke="{COCOA}" stroke-width="2"/>
  <path d="M30.5 36h3" stroke="{COCOA}" stroke-width="2"/>
  <circle cx="25" cy="36.5" r="1.8" fill="{COCOA}"/><circle cx="39" cy="36.5" r="1.8" fill="{COCOA}"/>
  <circle cx="21" cy="45" r="3" fill="{RASP}" opacity=".45"/><circle cx="43" cy="45" r="3" fill="{RASP}" opacity=".45"/>
  <path d="M27 47q5 4 10 0" stroke="{COCOA}" stroke-width="2.2" fill="none" stroke-linecap="round"/>""")

    sticker("b_four", f"""
  <path d="M6 56V34a26 26 0 0 1 52 0v22z" fill="{BRICK}"/>
  <path d="M6 56V34a26 26 0 0 1 52 0v22z" fill="none" stroke="{BRICK_D}" stroke-width="2"/>
  <path d="M10 30h8M24 22h8M40 22h8M46 34h8M8 44h6M50 46h6" stroke="{BRICK_D}" stroke-width="2.4" stroke-linecap="round"/>
  <path d="M18 56V40a14 14 0 0 1 28 0v16z" fill="{COCOA}"/>
  <path d="M24 56c-2-6 4-8 3-14 5 4 8 8 6 14z" fill="{GOLD}"/>
  <path d="M33 56c-1-4 3-6 3-10 4 4 5 7 3 10z" fill="#FF8A3D"/>
  <rect x="4" y="54" width="56" height="6" rx="3" fill="{CHOC}"/>""")

    sticker("b_champ", f"""
  <g stroke="{DOUGH_D}" stroke-width="2.6" stroke-linecap="round"><path d="M32 60V14M32 60L20 18M32 60l12-42"/></g>
  {''.join(f'<ellipse cx="{x}" cy="{y}" rx="3.6" ry="6" fill="{GOLD}" transform="rotate({r} {x} {y})"/>' for x, y, r in [(32,10,0),(28,18,-30),(36,18,30),(28,26,-30),(36,26,30),(18,14,-15),(22,22,-40),(15,22,10),(46,14,15),(42,22,40),(49,22,-10)])}
  <path d="M22 44h20" stroke="{RASP}" stroke-width="5" stroke-linecap="round"/>""")

    sticker("b_moulin", f"""
  <path d="M22 60l5-34h10l5 34z" fill="{CREAM}" stroke="{DOUGH_D}" stroke-width="2"/>
  <path d="M25 26l7-8 7 8z" fill="{BRICK}"/>
  <rect x="29" y="48" width="6" height="12" rx="3" fill="{CHOC}"/>
  <g transform="rotate(20 32 26)" fill="{SKY}" stroke="{SKY_D}" stroke-width="1.6">
    <path d="M32 26L30 4h6z"/><path d="M32 26l22-2v6z"/><path d="M32 26l2 22h-6z"/><path d="M32 26L10 28v-6z"/>
  </g><circle cx="32" cy="26" r="3.4" fill="{COCOA}"/>""")

    sticker("b_usine", f"""
  <rect x="40" y="8" width="8" height="24" fill="{STEEL_D}"/><rect x="40" y="8" width="8" height="4" fill="{RASP}"/>
  <circle cx="46" cy="6" r="4" fill="#E8E4EF"/><circle cx="52" cy="3" r="3" fill="#E8E4EF"/>
  <path d="M6 58V30l12 8v-8l12 8v-8l12 8V22h16v36z" fill="{STEEL}"/>
  <rect x="6" y="52" width="52" height="6" fill="{STEEL_D}"/>
  <rect x="12" y="42" width="7" height="7" rx="1.5" fill="{GOLD}"/><rect x="24" y="42" width="7" height="7" rx="1.5" fill="{GOLD}"/>
  <circle cx="44" cy="44" r="6" fill="{DOUGH}"/><circle cx="42" cy="42" r="1.3" fill="{CHIP}"/><circle cx="46" cy="46" r="1.3" fill="{CHIP}"/>""")

    sticker("b_banque", f"""
  <path d="M4 22L32 6l28 16z" fill="{PIST}" stroke="{PIST_D}" stroke-width="2" stroke-linejoin="round"/>
  <rect x="6" y="22" width="52" height="6" fill="{CREAM}" stroke="{PIST_D}" stroke-width="1.5"/>
  {''.join(f'<rect x="{x}" y="28" width="6" height="22" fill="{CREAM}" stroke="{PIST_D}" stroke-width="1.5"/>' for x in (10, 22, 36, 48))}
  <rect x="4" y="50" width="56" height="8" rx="2" fill="{PIST_D}"/>
  <rect x="27" y="10" width="10" height="9" rx="2" fill="#fff" stroke="{STEEL}" stroke-width="1.2"/>
  <path d="M27 13h10M30 10v9" stroke="#E4E9EE" stroke-width="1"/>""")

    sticker("b_temple", f"""
  <path d="M6 24L32 8l26 16z" fill="{CHOC}"/>
  <path d="M10 22h44" stroke="{DOUGH_L}" stroke-width="1.5" opacity=".6"/>
  {''.join(f'<rect x="{x}" y="24" width="7" height="26" rx="2" fill="#7A4A2E"/><rect x="{x}" y="24" width="2.4" height="26" rx="1" fill="#9A6644"/>' for x in (9, 21, 36, 48))}
  <rect x="4" y="50" width="56" height="8" rx="2" fill="{CHOC}"/>
  <path d="M32 12l2 4 4 .6-3 3 .8 4-3.8-2-3.8 2 .8-4-3-3 4-.6z" fill="{GOLD}"/>""")

    sticker("b_tour", f"""
  <path d="M20 60l4-34h16l4 34z" fill="{PLUM}"/>
  <path d="M24 26l2 34h-6z" fill="{PLUM_D}" opacity=".5"/>
  <path d="M18 28L32 2l14 26z" fill="{PLUM_D}"/>
  <path d="M28 8l8 0" stroke="{GOLD}" stroke-width="0"/>
  <circle cx="32" cy="38" r="4.5" fill="{GOLD}"/><rect x="29" y="50" width="6" height="10" rx="3" fill="{COCOA}"/>
  <path d="M46 10l1.5 3.5 3.5 1.5-3.5 1.5L46 20l-1.5-3.5L41 15l3.5-1.5z" fill="{GOLD}"/>
  <circle cx="14" cy="16" r="1.6" fill="{GOLD}"/><circle cx="52" cy="30" r="1.4" fill="{GOLD}"/>""")

    sticker("b_fusee", f"""
  <path d="M26 46c-4 6-4 10-2 14 4-2 6-6 8-8M38 46c4 6 4 10 2 14-4-2-6-6-8-8" fill="{RASP}"/>
  <path d="M28 52c2 6 4 8 4 10 0-2 2-4 4-10z" fill="{GOLD}"/>
  <path d="M32 2c10 8 12 24 8 46H24C20 26 22 10 32 2z" fill="#F3F0F7"/>
  <path d="M32 2c4 4 7 9 8 14H24c1-5 4-10 8-14z" fill="{RASP}"/>
  <circle cx="32" cy="28" r="7" fill="{DOUGH}" stroke="{STEEL}" stroke-width="2.4"/>
  <circle cx="30" cy="26" r="1.4" fill="{CHIP}"/><circle cx="34" cy="30" r="1.4" fill="{CHIP}"/>""")

    sticker("b_labo", f"""
  <rect x="26" y="4" width="12" height="16" rx="2" fill="#E9F3F7" stroke="{STEEL}" stroke-width="2"/>
  <rect x="24" y="2" width="16" height="5" rx="2" fill="{CHOC}"/>
  <circle cx="32" cy="40" r="20" fill="#E9F3F7" stroke="{STEEL}" stroke-width="2"/>
  <path d="M13 42a19 19 0 0 0 38 0c-6-3-12 3-19 0s-13-3-19 0z" fill="{PIST}"/>
  <circle cx="26" cy="48" r="3" fill="#C8EBA9"/><circle cx="37" cy="44" r="2" fill="#C8EBA9"/><circle cx="32" cy="16" r="2" fill="#C8EBA9"/>
  <path d="M20 30a14 14 0 0 1 8-8" stroke="#fff" stroke-width="3" stroke-linecap="round" fill="none"/>
  <path d="M44 52l3-6 3 6-3 3z" fill="{GOLD}"/>""")

    sticker("b_portail", f"""
  <ellipse cx="32" cy="32" rx="26" ry="28" fill="{PLUM_D}"/>
  <ellipse cx="32" cy="32" rx="20" ry="22" fill="{PLUM}"/>
  <ellipse cx="32" cy="32" rx="13" ry="15" fill="#5FD1C9"/>
  <path d="M32 18c8 2 9 12 2 14-6 2-6 8 0 10" stroke="#E8FFFC" stroke-width="3" fill="none" stroke-linecap="round"/>
  <circle cx="14" cy="14" r="2" fill="{GOLD}"/><circle cx="52" cy="50" r="2" fill="{GOLD}"/><circle cx="50" cy="12" r="1.4" fill="#fff"/>""")

    sticker("b_horloge", f"""
  <circle cx="32" cy="32" r="27" fill="{GOLD_D}"/>
  <circle cx="32" cy="32" r="22" fill="{CREAM}"/>
  {''.join(f'<rect x="31" y="12" width="2" height="5" rx="1" fill="{COCOA}" transform="rotate({a} 32 32)"/>' for a in range(0, 360, 30))}
  <path d="M32 32V18" stroke="{COCOA}" stroke-width="3" stroke-linecap="round"/>
  <path d="M32 32l9 7" stroke="{RASP}" stroke-width="3" stroke-linecap="round"/>
  <circle cx="32" cy="32" r="3" fill="{COCOA}"/>
  <path d="M8 14a28 28 0 0 1 8-8" stroke="{SKY}" stroke-width="3" stroke-linecap="round" fill="none"/>
  <path d="M5 10l3 4 4-3" stroke="{SKY}" stroke-width="3" stroke-linecap="round" fill="none"/>""")

    books = [(6, 22, 9, RASP), (16, 14, 8, SKY), (25, 18, 10, PIST), (36, 10, 8, GOLD), (45, 20, 12, PLUM)]
    sticker("b_biblio", "".join(
        f'<rect x="{x}" y="{y}" width="{w}" height="{58 - y}" rx="2" fill="{c}"/>'
        f'<rect x="{x}" y="{y + 6}" width="{w}" height="3" fill="#fff" opacity=".55"/>'
        f'<rect x="{x}" y="{52}" width="{w}" height="2" fill="{COCOA}" opacity=".25"/>' for x, y, w, c in books
    ) + f'<rect x="4" y="56" width="56" height="5" rx="2.5" fill="{CHOC}"/>')

    sticker("b_prisme", f"""
  <path d="M2 40l18-3" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
  {''.join(f'<path d="M40 34L62 {y}" stroke="{c}" stroke-width="4" stroke-linecap="round"/>' for y, c in [(22, RASP), (28, GOLD), (34, PIST), (40, SKY), (46, PLUM)])}
  <path d="M30 8L50 50H10z" fill="#DDF3FB" stroke="{SKY_D}" stroke-width="2.4" stroke-linejoin="round"/>
  <path d="M30 8L22 50H10z" fill="#fff" opacity=".7"/>""")

    # ---- upgrades & achievements ------------------------------------------
    sticker("u_brain", f"""
  <path d="M32 10c-6-6-18-2-18 8-8 2-10 14-4 18-2 8 4 16 12 14 4 6 14 4 10-4z" fill="#F4A6B8"/>
  <path d="M32 10c6-6 18-2 18 8 8 2 10 14 4 18 2 8-4 16-12 14-4 6-14 4-10-4z" fill="#EE8FA5"/>
  <path d="M32 12v40M20 22c4 0 6 4 6 8M44 22c-4 0-6 4-6 8M16 36c4-2 8 0 10 4M48 36c-4-2-8 0-10 4" stroke="#C25E78" stroke-width="2.2" fill="none" stroke-linecap="round"/>""")
    flame = f"""<path d="M32 4c4 10 18 16 18 32a18 18 0 0 1-36 0c0-8 4-12 8-16 0 6 2 10 6 10-4-10 0-20 4-26z" fill="#FF7A2F"/>
  <path d="M32 26c2 6 10 8 10 18a10 10 0 0 1-20 0c0-6 4-8 6-10 0 4 2 6 4 6-2-6 0-10 0-14z" fill="{GOLD}"/>"""
    sticker("u_flame", flame)
    sticker("a_flame", flame)
    sticker("u_golden", cookie_body(GOLD, GOLD_D, "#FFF0A8", "#B5651D", bite=False))
    sticker("a_golden", cookie_body(GOLD, GOLD_D, "#FFF0A8", "#B5651D", bite=False) + '<path d="M50 4l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#fff"/>')
    sticker("u_cat", f"""
  <path d="M10 26L12 6l14 12h12l14-12 2 20c4 6 4 12 0 18-6 10-34 10-40 0-4-6-4-12 0-18z" fill="{DOUGH_L}"/>
  <path d="M14 12l8 8M50 12l-8 8" stroke="#F2A0A0" stroke-width="3" stroke-linecap="round"/>
  <ellipse cx="24" cy="34" rx="3" ry="4" fill="{COCOA}"/><ellipse cx="40" cy="34" rx="3" ry="4" fill="{COCOA}"/>
  <path d="M30 42h4l-2 3z" fill="{RASP}"/><path d="M32 45q-3 4-7 2M32 45q3 4 7 2" stroke="{COCOA}" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <path d="M6 40l12 1M6 46l12-2M58 40l-12 1M58 46l-12-2" stroke="{COCOA}" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M8 56h48" stroke="#fff" stroke-width="6" stroke-linecap="round"/><path d="M8 56h48" stroke="#E9F3FF" stroke-width="3" stroke-linecap="round"/>""")
    sapling = f"""<path d="M32 58V30" stroke="{CHOC}" stroke-width="4" stroke-linecap="round"/>
  <path d="M32 34C20 34 12 26 12 14c12 0 20 8 20 20z" fill="{PIST}"/>
  <path d="M32 28c0-12 8-20 20-20 0 12-8 20-20 20z" fill="{PIST_D}"/>
  <path d="M16 18c6 2 10 8 14 14M48 12c-6 2-10 6-14 14" stroke="#C8EBA9" stroke-width="2" fill="none"/>
  <ellipse cx="32" cy="58" rx="16" ry="4" fill="{CHOC}"/>"""
    sticker("u_sapling", sapling)
    sticker("a_sapling", sapling)
    freeze = f"""<path d="M8 22c0-8 6-12 24-12s24 4 24 12v6c-2 4-6 2-8 6s-6 2-8 0-6 6-10 2-6-2-8-4-6 4-10 0-4-4-4-8z" fill="#E6F6FF"/>
  <path d="M8 26c0 8 4 6 8 10 2 2 6-2 8 0 4 4 6 2 10-2 4 4 8 6 10 2s6-2 8-6" fill="none"/>
  <rect x="8" y="32" width="48" height="24" rx="10" fill="{DOUGH}"/>
  <path d="M8 34c4 6 8 2 12 6s8-2 12 2 8 0 12-4 8 2 12-2V26H8z" fill="#E6F6FF"/>
  <path d="M46 12l2 4 4 1-4 2-2 4-2-4-4-2 4-1z" fill="{SKY}"/>"""
    sticker("u_freeze", freeze)
    sticker("a_freeze", freeze)
    cal = f"""<rect x="6" y="10" width="52" height="48" rx="8" fill="#fff"/>
  <path d="M6 18a8 8 0 0 1 8-8h36a8 8 0 0 1 8 8v8H6z" fill="{RASP}"/>
  <rect x="17" y="4" width="5" height="12" rx="2.5" fill="{COCOA}"/><rect x="42" y="4" width="5" height="12" rx="2.5" fill="{COCOA}"/>
  <path d="M20 42l8 8 16-16" stroke="{PIST_D}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>"""
    sticker("u_calendar", cal)
    sticker("a_calendar", cal)

    sticker("a_card", f"""
  <rect x="14" y="8" width="40" height="48" rx="6" fill="#E9E3D6" transform="rotate(10 34 32)"/>
  <rect x="10" y="8" width="40" height="48" rx="6" fill="#fff" stroke="{STEEL}" stroke-width="1.5"/>
  <path d="M18 22h24M18 30h18" stroke="{STEEL}" stroke-width="3" stroke-linecap="round"/>
  <path d="M18 42h24" stroke="{SKY}" stroke-width="3" stroke-linecap="round"/>
  <path d="M38 46l4 4 8-10" stroke="{PIST_D}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>""")
    sticker("a_cookie", cookie_body())
    sticker("a_oven", (OUT / "b_four.svg").read_text().split('<g filter="url(#sh)">')[1].rsplit("</g>", 1)[0])
    sticker("a_check", f"""
  <rect x="6" y="20" width="52" height="38" rx="8" fill="{BRICK}"/>
  <rect x="12" y="26" width="40" height="26" rx="5" fill="{COCOA}"/>
  <path d="M20 39l8 7 16-14" stroke="{GOLD}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M18 14c2-4-2-6 0-10M32 14c2-4-2-6 0-10M46 14c2-4-2-6 0-10" stroke="{STEEL}" stroke-width="2.6" fill="none" stroke-linecap="round"/>""")
    sticker("a_scroll", f"""
  <rect x="14" y="10" width="38" height="44" rx="3" fill="#FFF0CC"/>
  <rect x="8" y="6" width="44" height="10" rx="5" fill="{DOUGH}"/><rect x="14" y="48" width="44" height="10" rx="5" fill="{DOUGH}"/>
  <path d="M22 24h22M22 31h22M22 38h14" stroke="{CHOC}" stroke-width="2.6" stroke-linecap="round"/>
  <circle cx="44" cy="42" r="6" fill="{RASP}"/><path d="M41 48l-2 8 5-3 5 3-2-8" fill="{RASP}"/>""")
    sticker("a_star", f"""
  <path d="M32 4l8 17 18 2-14 12 4 19-16-9-16 9 4-19L6 23l18-2z" fill="{GOLD}" stroke="{GOLD_D}" stroke-width="2" stroke-linejoin="round"/>
  <path d="M24 22l8-14" stroke="#FFF0A8" stroke-width="3" stroke-linecap="round"/>""")
    sticker("a_diploma", f"""
  <path d="M4 22L32 10l28 12-28 12z" fill="{COCOA}"/>
  <path d="M16 28v12c0 6 32 6 32 0V28l-16 7z" fill="{CHOC}"/>
  <path d="M54 24v14" stroke="{GOLD}" stroke-width="2.4"/><circle cx="54" cy="40" r="3" fill="{GOLD}"/>
  <rect x="12" y="46" width="40" height="12" rx="6" fill="#FFF0CC" stroke="{DOUGH_D}" stroke-width="1.5"/>
  <path d="M30 46v12" stroke="{RASP}" stroke-width="4"/>""")
    sticker("a_moon", f"""
  <g mask="url(#cres)"><circle cx="30" cy="34" r="25" fill="#F7E7A8"/>
  <circle cx="22" cy="40" r="3.5" fill="#E5CF7F"/><circle cx="30" cy="52" r="4" fill="#E5CF7F"/><circle cx="14" cy="28" r="2.5" fill="#E5CF7F"/></g>
  <path d="M50 10l1.6 3.4 3.4 1.6-3.4 1.6L50 20l-1.6-3.4-3.4-1.6 3.4-1.6z" fill="#fff"/>""",
            '<mask id="cres"><rect x="-4" y="-4" width="72" height="72" fill="#fff"/><circle cx="44" cy="24" r="20" fill="#000"/></mask>')
    sticker("a_sun", f"""
  {''.join(f'<rect x="30" y="2" width="4" height="10" rx="2" fill="{GOLD_D}" transform="rotate({a} 32 32)"/>' for a in range(0, 360, 45))}
  <circle cx="32" cy="32" r="16" fill="{GOLD}"/>
  <path d="M24 30a8 8 0 0 1 6-6" stroke="#FFF0A8" stroke-width="3" stroke-linecap="round" fill="none"/>""")

    print("wrote", len(list(OUT.glob("*.svg"))), "icons to", OUT)


if __name__ == "__main__":
    main()
