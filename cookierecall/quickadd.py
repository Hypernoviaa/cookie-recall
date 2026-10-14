"""Quick Add: add notes from a panel inside the main window, without opening
Anki's separate "Add" window.

The panel itself is drawn by web/cookierecall.js (deck list and deck overview).
This module answers its requests through the same pycmd bridge as the bakery.
Adding a note does NOT give cookies: only reviewing does.
"""

from __future__ import annotations

import html
import re

from anki.consts import MODEL_CLOZE
from aqt import mw
from aqt.qt import QKeySequence, QShortcut

_added_since_open = 0
_disabled: list[QShortcut] = []


# ------------------------------------------------------------------ shortcuts
def _is_plain_key(seq: QKeySequence) -> bool:
    """Single printable key, optionally with Shift: these would eat what the user types."""
    text = seq.toString()
    if not text or "," in text:
        return False
    parts = text.split("+")
    key = parts[-1]
    mods = parts[:-1]
    return len(key) == 1 and all(m == "Shift" for m in mods)


def suspend_shortcuts() -> None:
    global _disabled
    restore_shortcuts()
    for sc in mw.findChildren(QShortcut):
        if sc.isEnabled() and _is_plain_key(sc.key()):
            sc.setEnabled(False)
            _disabled.append(sc)


def restore_shortcuts() -> None:
    global _disabled
    for sc in _disabled:
        try:
            sc.setEnabled(True)
        except RuntimeError:
            pass  # deleted with its screen
    _disabled = []


# ------------------------------------------------------------------ data
def init_payload(cfg: dict) -> dict:
    col = mw.col
    decks = [{"id": int(d.id), "name": d.name} for d in col.decks.all_names_and_ids(include_filtered=False)]
    notetypes = []
    for nt in col.models.all_names_and_ids():
        m = col.models.get(nt.id)
        if not m:
            continue
        notetypes.append({
            "id": int(nt.id),
            "name": nt.name,
            "fields": col.models.field_names(m),
            "cloze": m.get("type") == MODEL_CLOZE,
        })
    defaults = col.defaults_for_adding(current_review_card=None)
    did = int(cfg.get("qa_last_deck") or 0) or int(defaults.deck_id)
    ntid = int(cfg.get("qa_last_notetype") or 0) or int(defaults.notetype_id)
    if did not in {d["id"] for d in decks}:
        did = int(col.decks.get_current_id())
    if ntid not in {n["id"] for n in notetypes} and notetypes:
        ntid = notetypes[0]["id"]
    return {"ok": True, "decks": decks, "notetypes": notetypes, "deck": did, "notetype": ntid}


_ALLOWED = re.compile(r"</?(b|i|u|br|sub|sup|div|span)(\s[^>]*)?/?>", re.I)


def _clean(field_html: str) -> str:
    """Keep the few tags a contenteditable produces for bold/italic/line breaks; drop the rest."""
    s = str(field_html or "")
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.I | re.S)
    out, pos = [], 0
    for m in re.finditer(r"<[^>]+>", s):
        out.append(s[pos:m.start()])
        tag = m.group(0)
        if _ALLOWED.fullmatch(tag):
            name = re.match(r"</?(\w+)", tag).group(1).lower()
            closing = tag.startswith("</")
            out.append(f"</{name}>" if closing else f"<{name}>")
        pos = m.end()
    out.append(s[pos:])
    s = "".join(out)
    s = re.sub(r"(<br>\s*)+$", "", s)  # trailing empty lines
    s = re.sub(r"^(<div><br></div>)+|(<div><br></div>)+$", "", s)
    return s.strip()


def add(data: dict) -> dict:
    global _added_since_open
    col = mw.col
    try:
        did = int(data.get("deck"))
        ntid = int(data.get("notetype"))
    except (TypeError, ValueError):
        return {"ok": False, "error": "bad"}
    model = col.models.get(ntid)
    if not model or not col.decks.get(did, default=False):
        return {"ok": False, "error": "bad"}
    fields = data.get("fields") or []
    names = col.models.field_names(model)
    if not isinstance(fields, list) or len(fields) != len(names):
        return {"ok": False, "error": "bad"}
    note = col.new_note(model)
    for i, value in enumerate(fields):
        note.fields[i] = _clean(value)
    tags = str(data.get("tags") or "")
    note.tags = [t for t in re.split(r"\s+", tags.strip()) if t][:50]

    # NoteFieldsCheckResponse.State: 0 normal, 1 empty, 2 duplicate, 3 missing cloze, 4 not a cloze notetype
    state_name = {0: "NORMAL", 1: "EMPTY", 2: "DUPLICATE", 3: "MISSING_CLOZE", 4: "NOTETYPE_NOT_CLOZE"}.get(int(note.fields_check()), "NORMAL")
    if state_name == "EMPTY":
        return {"ok": False, "error": "empty"}
    if state_name == "MISSING_CLOZE":
        return {"ok": False, "error": "cloze"}

    col.add_note(note, did)
    _added_since_open += 1
    preview = re.sub(r"<[^>]+>", " ", note.fields[0])
    preview = html.unescape(re.sub(r"\s+", " ", preview)).strip()[:80]
    return {"ok": True, "cards": len(note.cards()), "duplicate": state_name == "DUPLICATE", "preview": preview, "added": _added_since_open}


def new_deck(name: str) -> dict:
    name = re.sub(r"\s+", " ", str(name or "")).strip()
    if not name or len(name) > 120:
        return {"ok": False}
    did = mw.col.decks.id(name, create=True)
    return {"ok": True, "deck": {"id": int(did), "name": mw.col.decks.name(did)}}


def opened() -> None:
    global _added_since_open
    _added_since_open = 0
    suspend_shortcuts()


def closed() -> int:
    restore_shortcuts()
    n = _added_since_open
    if n:
        mw.update_undo_actions()
        # refresh deck counts once the panel is gone
        if mw.state == "deckBrowser":
            mw.deckBrowser.refresh()
        elif mw.state == "overview":
            mw.overview.refresh()
    return n


def open_full_editor() -> None:
    restore_shortcuts()
    mw.onAddCard()

