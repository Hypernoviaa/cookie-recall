"""Cookie Recall theme: re-skins the whole Anki interface in the bakery universe.

Anki generates every colour of its UI from one token set (aqt.colors, built
from _root-vars.scss). Native Qt windows read those tokens through
theme_manager; web pages read the same tokens as CSS variables.
So the theme works in three layers, all through supported entry points:

  1. Qt windows (browser, add dialog, menus, preferences...):
     the token values are swapped in aqt.colors, then the palette and the
     stylesheet are rebuilt; extra Qt rules go through gui_hooks.style_did_init.
  2. Classic web pages (deck list, overview, top/bottom bars...):
     webview_will_set_content adds the CSS variables + theme.css.
  3. Svelte pages (editor, statistics, deck options, card info, import...):
     webview_did_inject_style_into_page injects the same styles.

Card content (reviewer card area, previewer, card layout) is never touched:
it belongs to the user's note types.
"""

from __future__ import annotations

import traceback
from pathlib import Path

from aqt import colors, gui_hooks, mw
from aqt.theme import theme_manager

WEB_DIR = Path(__file__).parent / "web"

# token: (light "Boulangerie de jour", dark "Boulangerie de nuit")
TOKENS: dict[str, tuple[str, str]] = {
    "FG": ("#3b2416", "#f3efe2"),
    "FG_SUBTLE": ("#86664e", "#b5c2b6"),
    "FG_DISABLED": ("#b29a83", "#6f8a80"),
    "FG_FAINT": ("#cdb99f", "#4f6e64"),
    "FG_LINK": ("#2e6f57", "#f5c542"),
    "CANVAS": ("#f6eedf", "#1b302a"),
    "CANVAS_ELEVATED": ("#fffaf1", "#223d36"),
    "CANVAS_INSET": ("#fffdf8", "#172a25"),
    "CANVAS_OVERLAY": ("#fffaf1", "#223d36"),
    "CANVAS_CODE": ("#fffdf8", "#152520"),
    "CANVAS_GLASS": ("rgba(255, 250, 241, 0.55)", "rgba(34, 61, 54, 0.55)"),
    "BORDER": ("#e2cfb3", "#365a50"),
    "BORDER_SUBTLE": ("#ede0cb", "#2b4a42"),
    "BORDER_STRONG": ("#c4a57f", "#4d776b"),
    "BORDER_FOCUS": ("#5e9447", "#8dbf6a"),
    "BUTTON_BG": ("#fff6e8", "#284840"),
    "BUTTON_GRADIENT_START": ("#fffaf2", "#2e5249"),
    "BUTTON_GRADIENT_END": ("#f6e7cf", "#244139"),
    "BUTTON_HOVER_BORDER": ("#c4a57f", "#5e8a7c"),
    "BUTTON_DISABLED": ("#efe4d3", "#22392f"),
    "BUTTON_PRIMARY_BG": ("#1e3b34", "#d98e1a"),
    "BUTTON_PRIMARY_GRADIENT_START": ("#2c5249", "#e6a133"),
    "BUTTON_PRIMARY_GRADIENT_END": ("#1e3b34", "#c97f12"),
    "BUTTON_PRIMARY_DISABLED": ("#7f968e", "#8a6a3a"),
    "SCROLLBAR_BG": ("#dcc8aa", "#365a50"),
    "SCROLLBAR_BG_HOVER": ("#c9ae8a", "#4a7468"),
    "SCROLLBAR_BG_ACTIVE": ("#b39270", "#5e8a7c"),
    "SHADOW": ("#d8c4a6", "#0e1c18"),
    "SHADOW_INSET": ("#e6d6bd", "#11211c"),
    "SHADOW_SUBTLE": ("#efe3cf", "#152822"),
    "SHADOW_FOCUS": ("#8dbf6a", "#8dbf6a"),
    "ACCENT_CARD": ("#c97f12", "#f5c542"),
    "ACCENT_NOTE": ("#5e9447", "#8dbf6a"),
    "ACCENT_DANGER": ("#d43d52", "#f0707f"),
    "STATE_NEW": ("#3f8fb8", "#7fc8e8"),
    "STATE_LEARN": ("#d43d52", "#f0707f"),
    "STATE_REVIEW": ("#4f8a3a", "#8dbf6a"),
    "STATE_MARKED": ("#8a5cc2", "#b48cff"),
    "HIGHLIGHT_BG": ("#cfe3bd", "#3d6a52"),
    "HIGHLIGHT_FG": ("#3b2416", "#f3efe2"),
    "SELECTED_BG": ("#ecdcc0", "#2f5148"),
    "SELECTED_FG": ("#3b2416", "#f3efe2"),
}

_ORIGINAL: dict[str, tuple[str, str]] = {}
_enabled = False
_base = ""


def _css_name(token: str) -> str:
    return "--" + token.lower().replace("_", "-")


def css_vars() -> str:
    """CSS variables for both themes, with enough specificity to beat Anki's own."""
    light = ";".join(f"{_css_name(k)}:{v[0]}" for k, v in TOKENS.items())
    dark = ";".join(f"{_css_name(k)}:{v[1]}" for k, v in TOKENS.items())
    return f":root:root{{{light}}}:root.night-mode:root{{{dark}}}"


def font_face() -> str:
    return (
        f'@font-face{{font-family:"CookieRecallFredoka";src:url("{_base}/fonts/fredoka-latin-wght-normal.woff2") format("woff2");'
        "font-weight:300 700;font-display:swap}"
        f'@font-face{{font-family:"CookieRecallFredoka";src:url("{_base}/fonts/fredoka-latin-ext-wght-normal.woff2") format("woff2");'
        "font-weight:300 700;font-display:swap;unicode-range:U+0100-02BA,U+1E00-1E9F}"
    )


def full_css() -> str:
    rules = (WEB_DIR / "theme.css").read_text(encoding="utf-8")
    return font_face() + css_vars() + rules


# ------------------------------------------------------------------ Qt layer
def _swap_tokens(enabled: bool) -> None:
    for name, (light, dark) in TOKENS.items():
        token = getattr(colors, name, None)
        if not isinstance(token, dict) or "light" not in token:
            continue  # token not present in this Anki version: skip quietly
        _ORIGINAL.setdefault(name, (token["light"], token["dark"]))
        token["light"], token["dark"] = (light, dark) if enabled else _ORIGINAL[name]


def _refresh_qt() -> None:
    app = mw.app
    try:
        theme_manager._apply_palette(app)
        theme_manager._apply_style(app)
    except AttributeError:
        # older/newer Anki without these helpers: fall back to a full re-apply
        theme_manager.apply_style()


def on_style_init(buf: str) -> str:
    if not _enabled:
        return buf
    fg_subtle = theme_manager.var(colors.FG_SUBTLE)
    border = theme_manager.var(colors.BORDER)
    elevated = theme_manager.var(colors.CANVAS_ELEVATED)
    return buf + f"""
QPushButton {{ border-radius: 9px; padding: 4px 12px; }}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ border-radius: 8px; }}
QMenu {{ border-radius: 10px; padding: 6px; border: 1px solid {border}; background: {elevated}; }}
QMenu::item {{ border-radius: 6px; padding: 5px 18px 5px 12px; }}
QToolTip {{ border-radius: 8px; padding: 6px 8px; border: 1px solid {border}; }}
QHeaderView::section {{ color: {fg_subtle}; font-weight: 600; }}
QGroupBox {{ border: 1px solid {border}; border-radius: 12px; margin-top: 14px; padding-top: 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: {fg_subtle}; }}
"""


# ------------------------------------------------------------------ web layers
def _skip(context) -> bool:
    """Pages that display card content: leave them to the note type's styling."""
    import aqt.browser.previewer
    import aqt.clayout
    import aqt.reviewer

    return isinstance(context, (aqt.reviewer.Reviewer, aqt.browser.previewer.Previewer, aqt.clayout.CardLayout))


def on_set_content(web_content, context) -> None:
    if not _enabled or _skip(context):
        return
    # no inline <script> here: some Anki pages (the editor) forbid it via CSP
    web_content.head += f'<style id="cookierecall-theme-vars">{font_face()}{css_vars()}</style>'
    web_content.css.append(f"{_base}/theme.css")


SKIP_KINDS = {"previewer", "card layout"}


def on_inject_style(webview) -> None:
    if not _enabled:
        return
    kind = getattr(getattr(webview, "kind", None), "value", "")
    if kind in SKIP_KINDS:
        return
    import json

    css = json.dumps(full_css())
    webview.eval(
        "(function(){var s=document.getElementById('cookierecall-theme');"
        "if(!s){s=document.createElement('style');s.id='cookierecall-theme';document.head.appendChild(s);}"
        f"s.textContent={css};}})();"
    )


# ------------------------------------------------------------------ public
def setup(base: str, enabled: bool) -> None:
    global _base
    _base = base
    gui_hooks.style_did_init.append(_safe_filter(on_style_init))
    gui_hooks.webview_will_set_content.append(_safe(on_set_content))
    gui_hooks.webview_did_inject_style_into_page.append(_safe(on_inject_style))
    set_enabled(enabled, refresh=True)


def set_enabled(enabled: bool, refresh: bool = True) -> None:
    global _enabled
    _enabled = bool(enabled)
    _swap_tokens(_enabled)
    if refresh:
        _refresh_qt()
        if mw.col and mw.state in ("deckBrowser", "overview", "review"):
            try:
                mw.toolbar.draw()
                mw.reset()
            except Exception:  # noqa: BLE001
                traceback.print_exc()


def _safe(fn):
    def wrapper(*args):
        try:
            fn(*args)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    return wrapper


def _safe_filter(fn):
    def wrapper(buf):
        try:
            return fn(buf)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            return buf

    return wrapper
