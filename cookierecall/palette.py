"""Colour palettes for the bakery, the review counter, the card style and the Anki theme.

Each palette is defined by five base colours; everything else is derived, so the
bakery, the HUD and the whole-Anki theme always stay in harmony.
"""

from __future__ import annotations

# id: (board, accent, accent_dark, light_canvas, ink)
PALETTES: dict[str, tuple[str, str, str, str, str]] = {
    "pistachio": ("#1e3b34", "#8dbf6a", "#5e9447", "#f6eedf", "#3b2416"),
    "raspberry": ("#4a1f36", "#f29bb8", "#c94f7a", "#fbeff1", "#3d1a2b"),
    "blueberry": ("#1b2d48", "#8cc4ef", "#3f82c2", "#eef3f9", "#1d2a3c"),
    "chocolate": ("#3a2518", "#e3a857", "#b5772c", "#f5ece1", "#3b2416"),
    "lavender": ("#2c2445", "#b9a2ec", "#7a5fc6", "#f3effa", "#2a2240"),
}
DEFAULT = "pistachio"

NAMES = {
    "fr": {"pistachio": "Pistache", "raspberry": "Framboise", "blueberry": "Myrtille", "chocolate": "Chocolat", "lavender": "Lavande"},
    "en": {"pistachio": "Pistachio", "raspberry": "Raspberry", "blueberry": "Blueberry", "chocolate": "Chocolate", "lavender": "Lavender"},
}


def valid(pid: str) -> str:
    return pid if pid in PALETTES else DEFAULT


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    """Linear mix: t=0 -> a, t=1 -> b."""
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return "#%02x%02x%02x" % (round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t))


def bakery_vars(pid: str) -> dict[str, str]:
    """CSS custom properties for the bakery / HUD shadow DOM."""
    board, accent, accent_d, light, _ink = PALETTES[valid(pid)]
    white = "#ffffff"
    return {
        "--board": board,
        "--board-2": mix(board, white, 0.05),
        "--board-3": mix(board, white, 0.1),
        "--board-can": mix(mix(board, accent, 0.22), white, 0.04),
        "--board-can-h": mix(mix(board, accent, 0.3), white, 0.05),
        "--board-muted": mix(board, "#c8c8c8", 0.35),
        "--pist": accent,
        "--pist-d": accent_d,
        "--chalk-dim": mix("#f3efe2", board, 0.28),
        "--paper": light,
    }


def swatch(pid: str) -> dict[str, str]:
    board, accent, _d, _l, _i = PALETTES[pid]
    return {"board": board, "accent": accent}


def anki_tokens(pid: str, base: dict[str, tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Anki colour tokens (light, dark) for a palette. Pistachio keeps the hand-tuned base."""
    pid = valid(pid)
    if pid == DEFAULT:
        return dict(base)
    board, accent, accent_d, light, ink = PALETTES[pid]
    white, black, chalk = "#ffffff", "#000000", "#f3efe2"
    dk_canvas = mix(board, black, 0.08)
    dk_elev = mix(board, white, 0.04)
    t = dict(base)
    t.update({
        "FG": (ink, chalk),
        "FG_SUBTLE": (mix(ink, light, 0.45), mix(chalk, board, 0.3)),
        "FG_DISABLED": (mix(ink, light, 0.6), mix(chalk, board, 0.55)),
        "FG_FAINT": (mix(ink, light, 0.75), mix(chalk, board, 0.7)),
        "FG_LINK": (accent_d, accent),
        "CANVAS": (light, dk_canvas),
        "CANVAS_ELEVATED": (mix(light, white, 0.65), dk_elev),
        "CANVAS_INSET": (mix(light, white, 0.85), mix(board, black, 0.15)),
        "CANVAS_OVERLAY": (mix(light, white, 0.65), dk_elev),
        "CANVAS_CODE": (mix(light, white, 0.85), mix(board, black, 0.2)),
        "BORDER": (mix(light, ink, 0.14), mix(board, white, 0.16)),
        "BORDER_SUBTLE": (mix(light, ink, 0.08), mix(board, white, 0.1)),
        "BORDER_STRONG": (mix(light, ink, 0.28), mix(board, white, 0.28)),
        "BORDER_FOCUS": (accent_d, accent),
        "BUTTON_BG": (mix(light, white, 0.5), mix(board, white, 0.08)),
        "BUTTON_GRADIENT_START": (mix(light, white, 0.75), mix(board, white, 0.12)),
        "BUTTON_GRADIENT_END": (mix(light, ink, 0.05), mix(board, white, 0.06)),
        "BUTTON_HOVER_BORDER": (mix(light, ink, 0.28), mix(board, white, 0.3)),
        "BUTTON_DISABLED": (mix(light, ink, 0.04), mix(board, black, 0.05)),
        "BUTTON_PRIMARY_BG": (board, accent_d),
        "BUTTON_PRIMARY_GRADIENT_START": (mix(board, white, 0.1), mix(accent_d, white, 0.1)),
        "BUTTON_PRIMARY_GRADIENT_END": (board, accent_d),
        "BUTTON_PRIMARY_DISABLED": (mix(board, white, 0.5), mix(accent_d, board, 0.5)),
        "SCROLLBAR_BG": (mix(light, ink, 0.2), mix(board, white, 0.18)),
        "SCROLLBAR_BG_HOVER": (mix(light, ink, 0.3), mix(board, white, 0.26)),
        "SCROLLBAR_BG_ACTIVE": (mix(light, ink, 0.4), mix(board, white, 0.34)),
        "SHADOW": (mix(light, ink, 0.2), mix(board, black, 0.6)),
        "SHADOW_INSET": (mix(light, ink, 0.12), mix(board, black, 0.5)),
        "SHADOW_SUBTLE": (mix(light, ink, 0.07), mix(board, black, 0.4)),
        "SHADOW_FOCUS": (accent, accent),
        "HIGHLIGHT_BG": (mix(white, accent, 0.45), mix(board, accent, 0.4)),
        "HIGHLIGHT_FG": (ink, chalk),
        "SELECTED_BG": (mix(light, accent, 0.28), mix(board, accent, 0.25)),
        "SELECTED_FG": (ink, chalk),
    })
    return t


def card_vars(pid: str) -> dict[str, str]:
    """Colours for the optional card style on the review screen."""
    board, accent, accent_d, light, ink = PALETTES[valid(pid)]
    return {
        "--cr-desk": light,
        "--cr-desk-dark": mix(board, "#000000", 0.12),
        "--cr-paper": mix(light, "#ffffff", 0.6),
        "--cr-paper-dark": mix(board, "#ffffff", 0.06),
        "--cr-ink": ink,
        "--cr-ink-dark": "#f3efe2",
        "--cr-accent": accent,
        "--cr-accent-d": accent_d,
        "--cr-line": mix(light, ink, 0.14),
        "--cr-line-dark": mix(board, "#ffffff", 0.16),
    }
