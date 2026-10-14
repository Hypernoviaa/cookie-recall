"""Anki integration for Cookie Recall.

Hooks used (all from aqt.gui_hooks, no monkey-patching):
  profile_did_open / profile_will_close / sync_did_finish   load & save state
  reviewer_will_answer_card   capture the card BEFORE it is rescheduled
  reviewer_did_answer_card    award cookies, push the reward to the HUD
  state_will_change           end of a study session -> "four vidé" check
                              (before the next screen renders, so it can celebrate)
  webview_will_set_content    inject the UI in reviewer, deck list, overview
  webview_did_receive_js_message   pycmd("cookierecall:...") bridge
  top_toolbar_did_init_links  "Cookie Recall" link in the top bar

State lives in the collection config (col.set_config), so it follows the
collection and syncs through AnkiWeb. It is kept to a few kilobytes.
"""

from __future__ import annotations

import json
import random
import time
import traceback
from typing import Any, Callable

from anki.consts import CARD_TYPE_NEW, QUEUE_TYPE_PREVIEW
from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowser
from aqt.operations import QueryOp
from aqt.overview import Overview
from aqt.qt import QAction
from aqt.reviewer import Reviewer
from aqt.utils import askUser, openLink, tooltip

from . import i18n, theme
from . import palette as P
from .game import Game, fmt_num

MODULE = __name__
STATE_KEY = "cookierecall_state"
MSG_PREFIX = "cookierecall:"

DEFAULT_CFG: dict[str, Any] = {
    "sound": False,
    "volume": 0.4,
    "hud": True,
    "hud_position": "top-right",
    "hud_goal": True,
    "hud_tiny": False,
    "reduced_motion": False,
    "show_bakery_on_home": True,
    "bakery_collapsed": False,
    "toolbar_link": True,
    "theme": True,
    "palette": "pistachio",
    "card_style": True,
    "rate_prompt": "",
    "language": "auto",
    "new_cards_full_reward_per_day": 50,
    "min_answer_seconds": 0.8,
}
UI_SETTINGS = {"sound", "hud", "hud_position", "hud_tiny", "reduced_motion", "bakery_collapsed", "hud_goal", "theme", "language", "palette", "card_style"}
LANGUAGES = {"auto", "fr", "en"}
KOFI_URL = "https://ko-fi.com/ankinovia"
ISSUES_URL = "https://github.com/Hypernoviaa/cookie-recall/issues"
POSITIONS = {"top-right", "top-left", "bottom-right", "bottom-left"}


# --------------------------------------------------------------------------- safety
_error_shown = False


def safe(default: Any = None) -> Callable:
    """Never let an add-on bug break reviewing: log, warn once, return a default.

    Anki removes a hook that raises, so swallowing here also keeps Cookie Recall alive.
    For filter hooks the default is the first positional argument (passed through)."""

    def deco(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            global _error_shown
            try:
                return fn(*args, **kwargs)
            except Exception:  # noqa: BLE001
                traceback.print_exc()
                if not _error_shown:
                    _error_shown = True
                    try:
                        tooltip(i18n.msg("error"), period=5000)
                    except Exception:  # noqa: BLE001
                        pass
                if default == "passthrough":
                    return args[0] if args else None
                return default

        wrapper.__name__ = fn.__name__
        return wrapper

    return deco


# --------------------------------------------------------------------------- core
class CookieRecall:
    def __init__(self) -> None:
        self.game: Game | None = None
        self.pending: dict[int, dict] = {}
        self.queued: list[dict] = []  # events to show on the next home/overview render
        self.scroll_next = False
        self.rng = random.Random()
        self.folder = mw.addonManager.addonFromModule(MODULE)
        self.base = f"/_addons/{self.folder}/web"
        self._mature_running = False

    # ---- config
    def cfg(self) -> dict[str, Any]:
        conf = mw.addonManager.getConfig(MODULE) or {}
        return {**DEFAULT_CFG, **conf}

    def write_cfg(self, key: str, value: Any) -> None:
        conf = self.cfg()
        conf[key] = value
        mw.addonManager.writeConfig(MODULE, conf)
        self.apply_rules()

    def apply_rules(self) -> None:
        if self.game:
            c = self.cfg()
            self.game.rules.update({
                "new_cards_full_reward_per_day": int(c["new_cards_full_reward_per_day"]),
                "min_answer_seconds": float(c["min_answer_seconds"]),
            })

    # ---- persistence
    def load(self) -> None:
        if not mw.col:
            return
        data = mw.col.get_config(STATE_KEY, None)
        self.game = Game(data if isinstance(data, dict) else None)
        self.apply_rules()
        self.queued += self.game.ensure_day(self.today())
        self.save()
        self.refresh_mature()

    def save(self) -> None:
        if self.game and mw.col:
            mw.col.set_config(STATE_KEY, self.game.state)

    def today(self) -> int:
        return int(mw.col.sched.today)

    def ready(self) -> bool:
        if self.game is None and mw.col:
            self.load()
        return self.game is not None and mw.col is not None

    # ---- data from the collection
    def refresh_mature(self) -> None:
        if not mw.col or self._mature_running:
            return
        self._mature_running = True

        def op(col) -> int:
            return len(col.find_cards("prop:ivl>=21 -is:suspended"))

        def done(n: int) -> None:
            self._mature_running = False
            if not self.game:
                return
            changed = n != self.game.s["mature"]
            events = self.game.set_mature(n)
            if changed or events:
                self.save()
                self.push_update(events)

        def failed(exc: Exception) -> None:
            self._mature_running = False
            print("Cookie Recall: mature count failed:", exc)

        QueryOp(parent=mw, op=op, success=done).failure(failed).run_in_background()

    def due_left(self) -> int:
        tree = mw.col.sched.deck_due_tree()
        return sum(child.review_count + child.learn_count for child in tree.children)

    # ---- snapshots
    def snap(self) -> dict:
        return self.game.snapshot(time.time())

    def hud_snap(self) -> dict:
        s = self.snap()
        for k in ("buildings", "upgrades", "owned_upgrades", "achievements", "perks"):
            s.pop(k, None)
        return s

    def ui_cfg(self) -> dict:
        c = self.cfg()
        out = {k: c[k] for k in (*UI_SETTINGS, "volume", "new_cards_full_reward_per_day")}
        pid = P.valid(str(c.get("palette")))
        out["palette"] = pid
        out["palette_vars"] = P.bakery_vars(pid)
        out["card_vars"] = P.card_vars(pid)
        names = P.NAMES.get(i18n.LANG, P.NAMES["en"])
        out["palettes"] = [{"id": k, "name": names[k], **P.swatch(k)} for k in P.PALETTES]
        out["show_rate"] = self.should_ask_rating()
        return out

    # ---- support links & rating
    def rate_url(self) -> str:
        # installed from AnkiWeb -> the add-on folder name is its AnkiWeb id
        if self.folder.isdigit():
            return f"https://ankiweb.net/shared/review/{self.folder}"
        return "https://ankiweb.net/shared/addons?search=Cookie%20Recall"

    def should_ask_rating(self) -> bool:
        """Ask once the player clearly enjoys it: 300 reviews and 3 ovens cleared.
        "Later" snoozes for 14 days; "never" / "done" stop for good."""
        if not self.game or not mw.col:
            return False
        state = str(self.cfg().get("rate_prompt") or "")
        if state in ("done", "never"):
            return False
        if state.startswith("later:"):
            try:
                if self.today() < int(state[6:]):
                    return False
            except ValueError:
                pass
        st = self.game.s["stats"]
        return st["reviews_total"] >= 300 and st["jackpots"] >= 3

    # ---- pushing to webviews
    def push_update(self, events: list[dict] | None = None) -> None:
        if not self.game:
            return
        state = mw.state
        try:
            if state == "deckBrowser" and self.cfg()["show_bakery_on_home"]:
                web, snap = mw.deckBrowser.web, self.snap()
            elif state == "review":
                web, snap = mw.reviewer.web, self.hud_snap()
            elif state == "overview":
                web, snap = mw.overview.web, self.hud_snap()
            else:
                return
            js = f"window.CookieRecall && CookieRecall.update({_js(snap)});"
            if events:
                js += f"window.CookieRecall && CookieRecall.events({_js(events)});"
            web.eval(js)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    def take_queued(self) -> list[dict]:
        ev, self.queued = self.queued, []
        return ev


F: CookieRecall | None = None


def _js(obj: Any) -> str:
    # JSON is valid JS; escape "</" so it can never close a <script> tag
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# --------------------------------------------------------------------------- hooks
@safe()
def on_profile_open() -> None:
    F.game = None
    F.pending.clear()
    F.load()


@safe()
def on_profile_close() -> None:
    F.save()
    F.game = None


@safe()
def on_sync_done() -> None:
    # another device may have played: reload what the sync brought in
    F.load()


@safe(default="passthrough")
def on_will_answer(ease_tuple: tuple[bool, int], reviewer: Reviewer, card) -> tuple[bool, int]:
    proceed, _ease = ease_tuple
    if proceed and card is not None:
        F.pending[card.id] = {
            "was_new": card.type == CARD_TYPE_NEW,
            "ivl": int(card.ivl or 0),
            "seconds": card.time_taken() / 1000.0,
            "preview": card.queue == QUEUE_TYPE_PREVIEW,
        }
    return ease_tuple


@safe()
def on_did_answer(reviewer: Reviewer, card, ease: int) -> None:
    if not F.ready():
        return
    info = F.pending.pop(card.id, None) or {"was_new": False, "ivl": 0, "seconds": 5.0, "preview": False}
    now = time.time()
    res = F.game.on_answer(
        card_id=int(card.id),
        was_new=info["was_new"],
        ivl_before=info["ivl"],
        seconds=info["seconds"],
        is_preview=info["preview"],
        day_id=F.today(),
        now=now,
        hour=time.localtime(now).tm_hour,
        rng=F.rng,
    )
    F.save()
    if F.cfg()["hud"]:
        payload = {**res, "snap": F.hud_snap()}
        reviewer.web.eval(f"window.CookieRecall && CookieRecall.reward({_js(payload)});")


@safe()
def on_state_change(new_state: str, old_state: str) -> None:
    if old_state != "review" or not F.ready():
        return
    events = F.game.on_clear_check(F.due_left(), F.today())
    if events:
        F.save()
        F.queued += events
        jackpot = next((e for e in events if e["type"] == "jackpot"), None)
        if jackpot and new_state == "overview":
            # Anki's "congratulations" screen is a Svelte page we can't inject into
            tooltip(i18n.msg("jackpot_tip", gain=fmt_num(jackpot["gain"]), streak=jackpot["streak"]), period=4500)
    F.refresh_mature()


@safe()
def on_set_content(web_content, context) -> None:
    if isinstance(context, Reviewer):
        mode = "hud"
    elif isinstance(context, DeckBrowser):
        mode = "bakery"
    elif isinstance(context, Overview):
        mode = "mini"
    else:
        return
    if not F.ready():
        return
    cfg = F.cfg()
    if mode == "hud" and not cfg["hud"]:
        if not cfg["card_style"]:
            return
        mode = "card"  # no counter, but still style the cards
    if mode == "bakery" and not cfg["show_bakery_on_home"]:
        return
    F.game.ensure_day(F.today())
    boot = {
        "mode": mode,
        "base": F.base,
        "snap": F.snap() if mode == "bakery" else F.hud_snap(),
        "cfg": F.ui_cfg(),
        "events": F.take_queued() if mode != "hud" else [],
        "scroll": F.scroll_next if mode == "bakery" else False,
        "lang": i18n.LANG,
    }
    if mode == "bakery":
        F.scroll_next = False
        web_content.body += '<div id="cookierecall-root"></div>'
    elif mode == "mini":
        web_content.body += '<div id="cookierecall-root" style="text-align:center"></div>'
    web_content.head += f"<script>window.COOKIERECALL_BOOT = {_js(boot)};</script>"
    web_content.js.append(f"{F.base}/strings.js")
    web_content.js.append(f"{F.base}/cookierecall.js")


@safe(default="passthrough")
def on_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    if not message.startswith(MSG_PREFIX):
        return handled
    if not isinstance(context, (Reviewer, DeckBrowser, Overview)) or not F.ready():
        return (True, json.dumps({"ok": False}))
    try:
        data = json.loads(message[len(MSG_PREFIX):])
    except ValueError:
        return (True, json.dumps({"ok": False}))
    res = dispatch(data, context)
    return (True, json.dumps(res, ensure_ascii=False))


def dispatch(data: dict, context: Any) -> dict:
    g = F.game
    a = data.get("a")
    now = time.time()
    if a == "golden":
        res = g.click_golden(str(data.get("token", "")), now, F.rng)
        if res.get("ok"):
            F.save()
            res["snap"] = F.hud_snap()
        return res
    if a == "buy":
        qty = data.get("qty", 1)
        qty = "max" if qty == "max" else max(1, min(1000, int(qty)))
        res = g.buy_building(str(data.get("id")), qty)
    elif a == "upgrade":
        res = g.buy_upgrade(str(data.get("id")))
    elif a == "freeze":
        res = g.buy_freeze()
    elif a == "perk":
        res = g.buy_perk(str(data.get("id")))
    elif a == "graduate":
        res = g.graduate()
        if res.get("ok"):
            res["events"] = [{"type": "graduated", "diplomas": res["diplomas"]}] + res.get("events", [])
    elif a == "setting":
        key, value = data.get("key"), data.get("value")
        if key not in UI_SETTINGS:
            return {"ok": False}
        if key == "hud_position" and value not in POSITIONS:
            return {"ok": False}
        if key == "palette" and value not in P.PALETTES:
            return {"ok": False}
        if key == "language" and value not in LANGUAGES:
            return {"ok": False}
        if key not in ("hud_position", "language", "palette"):
            value = bool(value)
        F.write_cfg(key, value)
        res = {"ok": True, "cfg": F.ui_cfg()}
        if key == "language":
            apply_language()
            if isinstance(context, DeckBrowser):
                mw.progress.single_shot(50, mw.deckBrowser.refresh)
            tooltip(i18n.msg("lang_restart"))
        if key == "palette":
            mw.progress.single_shot(80, lambda: theme.set_palette(value))
        if key == "theme":
            mw.progress.single_shot(50, lambda: theme.set_enabled(value))
        if key == "hud" and isinstance(context, DeckBrowser):
            tooltip(i18n.msg("hud_later"))
    elif a == "study":
        try:
            did = int(data.get("did"))
        except (TypeError, ValueError):
            return {"ok": False}
        if not mw.col.decks.get(did, default=False):
            return {"ok": False}
        mw.progress.single_shot(0, lambda: study_deck(did))
        return {"ok": True}
    elif a == "open_link":
        links = {"kofi": KOFI_URL, "rate": F.rate_url(), "issues": ISSUES_URL}
        url = links.get(str(data.get("which")))
        if not url:
            return {"ok": False}
        if data.get("which") == "rate":
            F.write_cfg("rate_prompt", "done")
        mw.progress.single_shot(0, lambda: openLink(url))
        return {"ok": True, "cfg": F.ui_cfg()}
    elif a == "rate_prompt":
        choice = data.get("value")
        if choice == "later":
            F.write_cfg("rate_prompt", f"later:{F.today() + 14}")
        elif choice == "never":
            F.write_cfg("rate_prompt", "never")
        else:
            return {"ok": False}
        return {"ok": True, "cfg": F.ui_cfg(), "snap": F.snap()}
    elif a == "open_bakery":
        mw.progress.single_shot(0, open_bakery)
        return {"ok": True}
    else:
        return {"ok": False}
    if res.get("ok"):
        F.save()
    res["snap"] = F.snap() if isinstance(context, DeckBrowser) else F.hud_snap()
    return res


# --------------------------------------------------------------------------- UI entry points
def study_deck(did: int) -> None:
    """One click from the deck list straight into reviews (skips the overview screen)."""
    if not mw.col:
        return
    mw.col.decks.select(did)
    mw.col.startTimebox()
    mw.moveToState("review")


def open_bakery() -> None:
    if not mw.col:
        return
    if not F.cfg()["show_bakery_on_home"]:
        F.write_cfg("show_bakery_on_home", True)
    if mw.state == "deckBrowser":
        mw.deckBrowser.web.eval("window.CookieRecall && CookieRecall.scrollIntoView();")
    else:
        F.scroll_next = True
        mw.moveToState("deckBrowser")


@safe()
def on_toolbar_links(links: list[str], toolbar) -> None:
    if not F.cfg()["toolbar_link"]:
        return
    links.append(toolbar.create_link("cookierecall", i18n.msg("toolbar"), open_bakery, tip=i18n.msg("toolbar_tip"), id="cookierecall"))


def reset_game() -> None:
    if not mw.col:
        return
    if not askUser(i18n.msg("reset_q")):
        return
    F.game = Game()
    F.apply_rules()
    F.game.ensure_day(F.today())
    F.save()
    F.refresh_mature()
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    tooltip(i18n.msg("reset_done"))


def apply_language() -> None:
    import anki.lang

    i18n.set_lang(i18n.resolve(str(F.cfg().get("language", "auto")), anki.lang.current_lang))


def on_config_updated(_conf: dict) -> None:
    F.apply_rules()
    apply_language()
    theme._palette = P.valid(str(F.cfg().get("palette")))
    theme.set_enabled(F.cfg()["theme"])


def setup() -> None:
    global F
    F = CookieRecall()
    apply_language()
    mw.addonManager.setWebExports(MODULE, r"web/(cookierecall\.(js|css)|strings\.js|theme\.css|img/.+\.svg|fonts/.+\.woff2)")
    mw.addonManager.setConfigUpdatedAction(MODULE, on_config_updated)
    theme.setup(F.base, F.cfg()["theme"], F.cfg().get("palette", P.DEFAULT))

    gui_hooks.profile_did_open.append(on_profile_open)
    gui_hooks.profile_will_close.append(on_profile_close)
    gui_hooks.sync_did_finish.append(on_sync_done)
    gui_hooks.reviewer_will_answer_card.append(on_will_answer)
    gui_hooks.reviewer_did_answer_card.append(on_did_answer)
    gui_hooks.state_will_change.append(on_state_change)
    gui_hooks.webview_will_set_content.append(on_set_content)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)
    gui_hooks.top_toolbar_did_init_links.append(on_toolbar_links)

    menu = mw.form.menuTools
    menu.addSeparator()
    act = QAction(i18n.msg("menu_open"), mw)
    act.triggered.connect(open_bakery)
    menu.addAction(act)
    act2 = QAction(i18n.msg("menu_reset"), mw)
    act2.triggered.connect(reset_game)
    menu.addAction(act2)


__all__ = ["setup", "fmt_num"]
