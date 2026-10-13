"""Cookie Recall game engine.

Pure Python, no Anki imports: the Anki integration feeds it events (an answer,
a click on a golden cookie, a purchase) and persists `Game.state`, a plain
JSON-serialisable dict kept small enough for the collection config (synced).

Design rules (see README):
  * no passive income: cookies are only earned by reviewing;
  * every grade is worth the same, so lying to the scheduler never pays;
  * farming is damped (same card again today, answers that are too fast,
    new cards beyond a daily cap);
  * the most valuable rewards follow real learning: clearing all due cards
    (daily jackpot + streak), and the "Savoir" multiplier from mature cards.
"""

from __future__ import annotations

import copy
import math
import random
import uuid
from typing import Any

from . import content as C
from . import i18n

STATE_VERSION = 1

BASE_PER_REVIEW = 3.0
COMBO_WINDOW_S = 120.0
COMBO_STEP = 0.01
COMBO_CAP = 50
GOLDEN_CHANCE = 1 / 40
GOLDEN_LIFE_S = 14.0
FRENZY_MULT = 7.0
FRENZY_REVIEWS = 7
STREAK_STEP = 0.03
STREAK_MAX_DAYS = 30
SAVOIR_PER_MATURE = 0.0004  # +1 % per 25 mature cards
DIPLOMA_BONUS = 0.01
DIPLOMA_UNIT = 1e12  # cookies baked (all time) for the first diploma
MATURE_IVL = 21

DEFAULT_RULES = {
    "new_cards_full_reward_per_day": 50,
    "min_answer_seconds": 0.8,
}


def _default_state() -> dict[str, Any]:
    return {
        "v": STATE_VERSION,
        "cookies": 0.0,
        "baked_run": 0.0,
        "baked_total": 0.0,
        "buildings": {},
        "upgrades": [],
        "achievements": [],
        "seen_achievements": 0,
        "diplomas": 0,
        "diplomas_spent": 0,
        "perks": [],
        "ascensions": 0,
        "flags": [],
        "mature": 0,
        "stats": {
            "reviews_total": 0,
            "reviews_run": 0,
            "golden_clicked": 0,
            "jackpots": 0,
            "max_combo": 0,
            "quests_done": 0,
            "day_reviews_best": 0,
            "last_review_day": -1,
        },
        "streak": {"count": 0, "best": 0, "last_day": -1, "freezes": 0},
        "day": {
            "id": -1,
            "reviews": 0,
            "baked": 0.0,
            "new_rewarded": 0,
            "cleared": False,
            "max_combo": 0,
            "golden": 0,
            "bought": 0,
            "mature_reviews": 0,
            "quests": [],
        },
        "combo": {"count": 0, "last_ts": 0.0},
        "frenzy": {"left": 0},
    }


def _merge(default: Any, data: Any) -> Any:
    """Fill missing keys of `data` from `default`, recursively; drop wrong types."""
    if isinstance(default, dict):
        if not isinstance(data, dict):
            return copy.deepcopy(default)
        out = {}
        for k, dv in default.items():
            out[k] = _merge(dv, data[k]) if k in data else copy.deepcopy(dv)
        # keep unknown keys only for open-ended maps (buildings)
        if not default:
            out = {k: v for k, v in data.items()}
        return out
    if isinstance(default, float):
        return float(data) if isinstance(data, (int, float)) and math.isfinite(data) else default
    if isinstance(default, bool):
        return bool(data) if isinstance(data, bool) else default
    if isinstance(default, int):
        return int(data) if isinstance(data, (int, float)) and not isinstance(data, bool) else default
    if isinstance(default, list):
        return list(data) if isinstance(data, list) else list(default)
    return data if type(data) is type(default) else default


def fmt_num(x: float) -> str:
    """French short number format: 1 234 / 12,3 k / 4,56 M / 7,8 Md ..."""
    if x < 0:
        return "-" + fmt_num(-x)
    if x < 1_000:
        return f"{x:.1f}".rstrip("0").rstrip(".").replace(".", ",") if x < 10 and x != int(x) else f"{int(x)}"
    if x < 1_000_000:
        return f"{int(x):,}".replace(",", " ")
    names = ["M", "Md", "Bn", "Bd", "Tn", "Td", "Qn", "Qd", "Qt", "Qtd", "Sx", "Sxd"]
    exp = int(math.floor(math.log10(x) / 3)) - 2
    if exp >= len(names):
        return f"{x:.2e}".replace(".", ",")
    v = x / 10 ** ((exp + 2) * 3)
    s = f"{v:.3g}" if v < 100 else f"{v:.0f}"
    return f"{s.replace('.', ',')} {names[exp]}"


class Game:
    def __init__(self, state: dict | None = None, rules: dict | None = None):
        self.state: dict[str, Any] = _merge(_default_state(), state or {})
        self.state["v"] = STATE_VERSION
        self.rules = {**DEFAULT_RULES, **(rules or {})}
        # runtime only (not persisted)
        self.card_answers_today: dict[int, int] = {}
        self.golden: dict | None = None
        self._rt_day = -1

    # ------------------------------------------------------------------ helpers
    @property
    def s(self) -> dict:
        return self.state

    def owned(self, bid: str) -> int:
        return int(self.s["buildings"].get(bid, 0))

    def has_upgrade(self, uid: str) -> bool:
        return uid in self.s["upgrades"]

    def has_perk(self, pid: str) -> bool:
        return pid in self.s["perks"]

    def _effects(self) -> dict:
        """Aggregated upgrade effects, cached until the upgrade list changes."""
        ups = self.s["upgrades"]
        key = (len(ups), ups[-1] if ups else "")
        if getattr(self, "_fx_key", None) == key:
            return self._fx
        sums: dict[tuple[str, str], float] = {}
        bcount: dict[str, int] = {}
        gmult = 1.0
        for uid in ups:
            u = C.UPGRADE_BY_ID.get(uid)
            if not u:
                continue
            if u.kind == "building":
                bcount[u.target] = bcount.get(u.target, 0) + 1
            elif u.kind == "global":
                gmult *= 1 + u.value
            sums[(u.kind, u.target)] = sums.get((u.kind, u.target), 0.0) + u.value
            sums[(u.kind, "*")] = sums.get((u.kind, "*"), 0.0) + u.value
        self._fx = {"sums": sums, "bmult": {b: 2.0**n for b, n in bcount.items()}, "gmult": gmult}
        self._fx_key = key
        return self._fx

    def _upg_sum(self, kind: str, target: str | None = None) -> float:
        return self._effects()["sums"].get((kind, "*" if target is None else target), 0.0)

    # ---------------------------------------------------------------- multipliers
    def building_mult(self, bid: str) -> float:
        return self._effects()["bmult"].get(bid, 1.0)

    def building_cpr(self, bid: str) -> float:
        """Cookies per review from ONE unit of this building (before global multipliers)."""
        return C.BUILDING_BY_ID[bid].cpr * self.building_mult(bid)

    def raw_per_review(self) -> float:
        return BASE_PER_REVIEW + sum(self.owned(b.id) * self.building_cpr(b.id) for b in C.BUILDINGS)

    def mult_global_upgrades(self) -> float:
        return self._effects()["gmult"]

    def mult_achievements(self) -> float:
        per = 0.01 + self._upg_sum("milk")
        return 1 + len(self.s["achievements"]) * per

    def mult_savoir(self) -> float:
        k = SAVOIR_PER_MATURE * (1 + self._upg_sum("savoir"))
        if self.has_perk("erudition"):
            k *= 1.5
        return 1 + self.s["mature"] * k

    def streak_step(self) -> float:
        step = STREAK_STEP + self._upg_sum("streak", "streak_step")
        if self.has_perk("glacage"):
            step *= 1.5
        return step

    def mult_streak(self) -> float:
        return 1 + self.streak_step() * min(self.s["streak"]["count"], STREAK_MAX_DAYS)

    def mult_diplomas(self) -> float:
        m = 1 + DIPLOMA_BONUS * self.s["diplomas"]
        if self.has_perk("these"):
            m *= 1.25
        return m

    def mult_total(self) -> float:
        return (
            self.mult_global_upgrades()
            * self.mult_achievements()
            * self.mult_savoir()
            * self.mult_streak()
            * self.mult_diplomas()
        )

    def per_review_base(self) -> float:
        """Value of one full-value review without combo or frenzy."""
        return self.raw_per_review() * self.mult_total()

    # combo -----------------------------------------------------------------
    def combo_window(self) -> float:
        w = COMBO_WINDOW_S * (1 + self._upg_sum("combo", "window"))
        if self.has_perk("memoire"):
            w *= 2
        return w

    def combo_cap(self) -> int:
        cap = COMBO_CAP + self._upg_sum("combo", "cap")
        if self.has_perk("memoire"):
            cap += 25
        return int(cap)

    def combo_step(self) -> float:
        return COMBO_STEP + self._upg_sum("combo", "step")

    def combo_mult(self, count: int | None = None) -> float:
        c = self.s["combo"]["count"] if count is None else count
        return 1 + self.combo_step() * min(c, self.combo_cap())

    def combo_alive(self, now: float) -> bool:
        return self.s["combo"]["count"] > 0 and now - self.s["combo"]["last_ts"] <= self.combo_window()

    # golden ------------------------------------------------------------------
    def golden_chance(self) -> float:
        c = GOLDEN_CHANCE * (1 + self._upg_sum("golden", "freq"))
        if self.has_perk("flair"):
            c *= 1.3
        return min(c, 0.25)

    def golden_life(self) -> float:
        return GOLDEN_LIFE_S * (1 + self._upg_sum("golden", "life"))

    def frenzy_length(self) -> int:
        n = FRENZY_REVIEWS * (1 + self._upg_sum("golden", "frenzy"))
        if self.has_perk("sucre"):
            n *= 2
        return int(round(n))

    def freeze_cap(self) -> int:
        cap = 1 + self._upg_sum("streak", "freeze_cap")
        if self.has_perk("glacage"):
            cap += 1
        return int(cap)

    def freeze_cost(self) -> float:
        return max(2_000.0, self.per_review_base() * 300)

    # -------------------------------------------------------------- prices
    def building_cost(self, bid: str, qty: int = 1) -> float:
        b = C.BUILDING_BY_ID[bid]
        n = self.owned(bid)
        disc = 0.95 if self.has_perk("negoce") else 1.0
        r = C.COST_GROWTH
        # geometric series: base * r^n * (r^qty - 1) / (r - 1)
        return math.ceil(b.base_cost * disc * (r**n) * (r**qty - 1) / (r - 1))

    def max_affordable(self, bid: str) -> int:
        b = C.BUILDING_BY_ID[bid]
        disc = 0.95 if self.has_perk("negoce") else 1.0
        r = C.COST_GROWTH
        first = b.base_cost * disc * r ** self.owned(bid)
        if self.s["cookies"] < first:
            return 0
        q = int(math.floor(math.log(self.s["cookies"] * (r - 1) / first + 1, r)))
        while q > 0 and self.building_cost(bid, q) > self.s["cookies"]:
            q -= 1
        return q

    # ---------------------------------------------------------------- metrics
    def metric(self, name: str) -> float:
        st = self.s["stats"]
        if name.startswith("own:"):
            return self.owned(name[4:])
        if name.startswith("flag:"):
            return 1 if name[5:] in self.s["flags"] else 0
        return {
            "reviews_total": st["reviews_total"],
            "reviews_run": st["reviews_run"],
            "baked_total": self.s["baked_total"],
            "buildings_total": sum(self.s["buildings"].values()),
            "max_combo": st["max_combo"],
            "golden_clicked": st["golden_clicked"],
            "jackpots": st["jackpots"],
            "streak_best": self.s["streak"]["best"],
            "streak": self.s["streak"]["count"],
            "mature": self.s["mature"],
            "quests_done": st["quests_done"],
            "upgrades_owned": len(self.s["upgrades"]),
            "ascensions": self.s["ascensions"],
            "day_reviews_best": st["day_reviews_best"],
            "achievements": len(self.s["achievements"]),
            "none": 0,
        }.get(name, 0)

    def upgrade_unlocked(self, u: C.Upgrade) -> bool:
        metric, thr = u.unlock
        return self.metric(metric) >= thr

    def check_achievements(self) -> list[dict]:
        new = []
        owned = set(self.s["achievements"])
        for a in C.ACHIEVEMENTS:
            if a.id not in owned and self.metric(a.metric) >= a.threshold:
                self.s["achievements"].append(a.id)
                owned.add(a.id)
                name, desc = i18n.achievement(a)
                new.append({"type": "achievement", "id": a.id, "name": name, "desc": desc, "icon": a.icon})
        return new

    def _flag(self, name: str) -> None:
        if name not in self.s["flags"]:
            self.s["flags"].append(name)

    # ------------------------------------------------------------------ income
    def _earn(self, amount: float) -> float:
        amount = max(0.0, float(amount))
        if not math.isfinite(amount):
            amount = 0.0
        self.s["cookies"] += amount
        self.s["baked_run"] += amount
        self.s["baked_total"] += amount
        self.s["day"]["baked"] += amount
        return amount

    # ------------------------------------------------------------------ days
    def ensure_day(self, day_id: int) -> list[dict]:
        """Roll the day over if needed. Returns events (freeze used, streak lost...)."""
        events: list[dict] = []
        d = self.s["day"]
        if self._rt_day != day_id:
            self._rt_day = day_id
            if d["id"] != day_id:
                self.card_answers_today.clear()
        if d["id"] == day_id:
            return events
        st = self.s["streak"]
        if st["count"] > 0 and st["last_day"] >= 0:
            missed = day_id - st["last_day"] - 1
            if missed > 0:
                if st["freezes"] >= missed:
                    st["freezes"] -= missed
                    st["last_day"] = day_id - 1
                    self._flag("freeze_used")
                    events.append({"type": "freeze_used", "count": missed})
                else:
                    events.append({"type": "streak_lost", "count": st["count"]})
                    st["count"] = 0
        self.s["day"] = {
            "id": day_id,
            "reviews": 0,
            "baked": 0.0,
            "new_rewarded": 0,
            "cleared": False,
            "max_combo": 0,
            "golden": 0,
            "bought": 0,
            "mature_reviews": 0,
            "quests": self._make_quests(day_id),
        }
        return events

    def _make_quests(self, day_id: int) -> list[dict]:
        rng = random.Random(day_id * 7919 + 17)
        kinds = [q.kind for q in C.QUESTS]
        # "clear" is the core loop: offer it most days
        chosen = ["clear"] if rng.random() < 0.6 else []
        pool = [k for k in kinds if k not in chosen]
        rng.shuffle(pool)
        chosen += pool[: 3 - len(chosen)]
        out = []
        for kind in chosen:
            t = C.QUEST_BY_KIND[kind]
            i = rng.randrange(len(t.targets))
            out.append({"kind": kind, "n": t.targets[i], "reward": t.reward_reviews[i], "progress": 0, "done": False})
        return out

    def _quest_progress(self) -> list[dict]:
        d = self.s["day"]
        values = {
            "reviews": d["reviews"],
            "combo": d["max_combo"],
            "golden": d["golden"],
            "clear": 1 if d["cleared"] else 0,
            "buy": d["bought"],
            "mature_reviews": d["mature_reviews"],
        }
        events = []
        for q in d["quests"]:
            q["progress"] = min(values.get(q["kind"], 0), q["n"])
            if not q["done"] and q["progress"] >= q["n"]:
                q["done"] = True
                gain = self._earn(self.per_review_base() * q["reward"])
                self.s["stats"]["quests_done"] += 1
                events.append({"type": "quest", "text": quest_text(q), "gain": gain})
        return events

    # ----------------------------------------------------------------- answers
    def on_answer(
        self,
        *,
        card_id: int,
        was_new: bool,
        ivl_before: int,
        seconds: float,
        is_preview: bool,
        day_id: int,
        now: float,
        hour: int,
        rng: random.Random | None = None,
    ) -> dict:
        rng = rng or random.Random()
        events = self.ensure_day(day_id)
        st, d = self.s["stats"], self.s["day"]

        # anti-farm factor -------------------------------------------------
        factor = 1.0
        reason = ""
        seen = self.card_answers_today.get(card_id, 0)
        self.card_answers_today[card_id] = seen + 1
        if seen == 1:
            factor *= 0.5
            reason = "repeat"
        elif seen >= 2:
            factor *= 0.2
            reason = "repeat"
        if was_new and seen == 0:
            if d["new_rewarded"] >= int(self.rules["new_cards_full_reward_per_day"]):
                factor *= 0.25
                reason = reason or "new_cap"
            d["new_rewarded"] += 1
        if is_preview:
            factor *= 0.25
            reason = reason or "preview"
        too_fast = seconds < float(self.rules["min_answer_seconds"])
        if too_fast:
            factor *= 0.2
            reason = "too_fast"

        # combo (persistence, never speed: too-fast answers do not feed it) --
        combo = self.s["combo"]
        if now - combo["last_ts"] <= self.combo_window() and combo["count"] > 0:
            if not too_fast:
                combo["count"] += 1
        else:
            combo["count"] = 0 if too_fast else 1
        combo["last_ts"] = now
        st["max_combo"] = max(st["max_combo"], combo["count"])
        d["max_combo"] = max(d["max_combo"], combo["count"])

        # frenzy -------------------------------------------------------------
        frenzy = 1.0
        if self.s["frenzy"]["left"] > 0:
            frenzy = FRENZY_MULT
            self.s["frenzy"]["left"] -= 1
            if self.s["frenzy"]["left"] == 0:
                events.append({"type": "frenzy_end"})
            if combo["count"] >= 50:
                self._flag("storm")

        base = self.per_review_base()
        gain = self._earn(base * self.combo_mult() * frenzy * factor)

        # bookkeeping ---------------------------------------------------------
        st["reviews_total"] += 1
        st["reviews_run"] += 1
        d["reviews"] += 1
        st["day_reviews_best"] = max(st["day_reviews_best"], d["reviews"])
        if ivl_before >= MATURE_IVL:
            d["mature_reviews"] += 1
        if 0 <= hour < 4:
            self._flag("night")
        elif 5 <= hour < 7:
            self._flag("dawn")
        last = st["last_review_day"]
        if last >= 0 and day_id - last >= 7:
            self._flag("comeback")
        st["last_review_day"] = day_id

        # golden cookie spawn --------------------------------------------------
        if self.golden and self.golden["expires"] < now:
            self.golden = None
        if not self.golden and not too_fast and rng.random() < self.golden_chance():
            self.golden = {"token": uuid.uuid4().hex[:12], "expires": now + self.golden_life()}
            events.append({"type": "golden_spawn", "token": self.golden["token"], "life": self.golden_life()})

        events += self._quest_progress()
        events += self.check_achievements()
        return {
            "gain": gain,
            "factor": factor,
            "reason": reason,
            "combo": combo["count"],
            "combo_mult": self.combo_mult(),
            "frenzy": self.s["frenzy"]["left"],
            "events": events,
        }

    def click_golden(self, token: str, now: float, rng: random.Random | None = None) -> dict:
        rng = rng or random.Random()
        g = self.golden
        if not g or g["token"] != token or g["expires"] < now - 1.5:  # small latency grace
            return {"ok": False}
        self.golden = None
        self.s["stats"]["golden_clicked"] += 1
        self.s["day"]["golden"] += 1
        base = self.per_review_base() * self.combo_mult()
        roll = rng.random()
        if roll < 0.45:
            lucky = 1 + self._upg_sum("golden", "lucky")
            gain = self._earn(min(self.s["cookies"] * 0.15 + 13, base * 60) * lucky)
            res = {"ok": True, "kind": "lucky", "gain": gain}
        elif roll < 0.85:
            self.s["frenzy"]["left"] = self.frenzy_length()
            res = {"ok": True, "kind": "frenzy", "gain": 0, "reviews": self.frenzy_length(), "mult": FRENZY_MULT}
        else:
            gain = self._earn(base * 30)
            res = {"ok": True, "kind": "rain", "gain": gain}
        res["events"] = self._quest_progress() + self.check_achievements()
        return res

    def on_clear_check(self, due_left: int, day_id: int) -> list[dict]:
        """Call when a study session ends. due_left = review + learning cards still due."""
        events = self.ensure_day(day_id)
        d = self.s["day"]
        if d["cleared"] or due_left > 0 or d["reviews"] < 1:
            return events
        d["cleared"] = True
        st = self.s["streak"]
        if st["last_day"] != day_id:
            st["count"] = st["count"] + 1 if st["last_day"] == day_id - 1 else 1
            st["last_day"] = day_id
            st["best"] = max(st["best"], st["count"])
        self.s["stats"]["jackpots"] += 1
        if d["reviews"] >= 300:
            self._flag("big_clear")
        gain = self._earn(self.per_review_base() * (60 + d["reviews"]))
        events.append({"type": "jackpot", "gain": gain, "reviews": d["reviews"], "streak": st["count"]})
        events += self._quest_progress()
        events += self.check_achievements()
        return events

    def set_mature(self, n: int) -> list[dict]:
        self.s["mature"] = max(0, int(n))
        return self.check_achievements()

    # ---------------------------------------------------------------- spending
    def buy_building(self, bid: str, qty: int | str = 1) -> dict:
        if bid not in C.BUILDING_BY_ID or not self.building_visible(bid):
            return {"ok": False, "error": "unknown"}
        if qty == "max":
            qty = self.max_affordable(bid)
        qty = int(qty)
        if qty < 1:
            return {"ok": False, "error": "funds"}
        cost = self.building_cost(bid, qty)
        if cost > self.s["cookies"]:
            return {"ok": False, "error": "funds"}
        self.s["cookies"] -= cost
        self.s["buildings"][bid] = self.owned(bid) + qty
        self.s["day"]["bought"] += qty
        return {"ok": True, "events": self._quest_progress() + self.check_achievements()}

    def buy_upgrade(self, uid: str) -> dict:
        u = C.UPGRADE_BY_ID.get(uid)
        if not u or self.has_upgrade(uid) or not self.upgrade_unlocked(u):
            return {"ok": False, "error": "unavailable"}
        if u.cost > self.s["cookies"]:
            return {"ok": False, "error": "funds"}
        self.s["cookies"] -= u.cost
        self.s["upgrades"].append(uid)
        return {"ok": True, "events": self.check_achievements()}

    def buy_freeze(self) -> dict:
        st = self.s["streak"]
        if st["freezes"] >= self.freeze_cap():
            return {"ok": False, "error": "cap"}
        cost = self.freeze_cost()
        if cost > self.s["cookies"]:
            return {"ok": False, "error": "funds"}
        self.s["cookies"] -= cost
        st["freezes"] += 1
        return {"ok": True, "events": []}

    def buy_perk(self, pid: str) -> dict:
        p = C.PERK_BY_ID.get(pid)
        if not p or self.has_perk(pid) or (p.requires and not self.has_perk(p.requires)):
            return {"ok": False, "error": "unavailable"}
        if self.diplomas_available() < p.cost:
            return {"ok": False, "error": "funds"}
        self.s["diplomas_spent"] += p.cost
        self.s["perks"].append(pid)
        return {"ok": True, "events": []}

    # ---------------------------------------------------------------- prestige
    def diplomas_potential(self) -> int:
        return int(math.floor((self.s["baked_total"] / DIPLOMA_UNIT) ** (1 / 3) + 1e-9))

    def diplomas_pending(self) -> int:
        return max(0, self.diplomas_potential() - self.s["diplomas"])

    def diplomas_available(self) -> int:
        return self.s["diplomas"] - self.s["diplomas_spent"]

    def next_diploma_at(self) -> float:
        return ((self.diplomas_potential() + 1) ** 3) * DIPLOMA_UNIT

    def graduate(self) -> dict:
        pending = self.diplomas_pending()
        if pending < 1:
            return {"ok": False, "error": "not_ready"}
        prev_run = self.s["baked_run"]
        self.s["diplomas"] += pending
        self.s["ascensions"] += 1
        self.s["cookies"] = prev_run * 0.01 if self.has_perk("pate") else 0.0
        self.s["baked_run"] = 0.0
        self.s["buildings"] = {}
        self.s["upgrades"] = []
        self.s["combo"] = {"count": 0, "last_ts": 0.0}
        self.s["frenzy"] = {"left": 0}
        self.s["stats"]["reviews_run"] = 0
        self.golden = None
        if self.has_perk("souschef"):
            self.s["buildings"] = {"mamie": 10, "four": 5}
        return {"ok": True, "diplomas": pending, "events": self.check_achievements()}

    # -------------------------------------------------------------- visibility
    def building_visible(self, bid: str) -> bool:
        idx = next(i for i, b in enumerate(C.BUILDINGS) if b.id == bid)
        if idx == 0 or self.owned(bid) > 0:
            return True
        prev = C.BUILDINGS[idx - 1]
        return self.owned(prev.id) > 0 or self.s["baked_run"] >= C.BUILDINGS[idx].base_cost * 0.5

    # ---------------------------------------------------------------- snapshot
    def snapshot(self, now: float) -> dict:
        """Everything the UI needs, as plain JSON."""
        s = self.s
        base = self.per_review_base()
        alive = self.combo_alive(now)
        combo_count = s["combo"]["count"] if alive else 0
        cur_mult = self.combo_mult(combo_count) * (FRENZY_MULT if s["frenzy"]["left"] > 0 else 1)
        per_now = base * cur_mult
        total_raw = self.raw_per_review()

        buildings = []
        shown_locked = False
        for b in C.BUILDINGS:
            vis = self.building_visible(b.id)
            if not vis:
                if shown_locked:
                    continue
                shown_locked = True
            each = self.building_cpr(b.id) * self.mult_total()
            b_name, b_plural, b_desc = i18n.building(b)
            buildings.append({
                "id": b.id,
                "name": b_name if vis else "???",
                "plural": b_plural,
                "desc": b_desc if vis else i18n.misc("locked_desc"),
                "owned": self.owned(b.id),
                "cost1": self.building_cost(b.id, 1),
                "cost10": self.building_cost(b.id, 10),
                "cost100": self.building_cost(b.id, 100),
                "max": self.max_affordable(b.id),
                "each": each,
                "share": (self.owned(b.id) * self.building_cpr(b.id) / total_raw) if total_raw else 0,
                "locked": not vis,
            })

        upgrades = []
        for u in C.UPGRADES:
            if not self.has_upgrade(u.id) and self.upgrade_unlocked(u):
                u_name, u_desc = i18n.upgrade(u)
                upgrades.append({"id": u.id, "name": u_name, "desc": u_desc, "cost": u.cost, "icon": u.icon, "tier": u.tier, "kind": u.kind})
        upgrades.sort(key=lambda x: x["cost"])
        owned_upgrades = [
            {"id": u.id, "name": i18n.upgrade(u)[0], "desc": i18n.upgrade(u)[1], "icon": u.icon, "tier": u.tier}
            for uid in s["upgrades"]
            if (u := C.UPGRADE_BY_ID.get(uid))
        ]

        ach_owned = set(s["achievements"])
        achievements = [
            {
                "id": a.id,
                "name": i18n.achievement(a)[0] if (a.id in ach_owned or not a.hidden) else "???",
                "desc": i18n.achievement(a)[1] if (a.id in ach_owned or not a.hidden) else i18n.misc("secret_desc"),
                "icon": a.icon,
                "owned": a.id in ach_owned,
            }
            for a in C.ACHIEVEMENTS
        ]

        perks = [
            {
                "id": p.id,
                "name": i18n.perk(p)[0],
                "desc": i18n.perk(p)[1],
                "cost": p.cost,
                "owned": self.has_perk(p.id),
                "available": (not p.requires) or self.has_perk(p.requires),
                "requires": i18n.perk(C.PERK_BY_ID[p.requires])[0] if p.requires else "",
            }
            for p in C.PERKS
        ]

        # next goal: cheapest thing not yet affordable (or affordable now)
        goal = None
        candidates = [(bb["cost1"], bb["name"] if not bb["locked"] else i18n.misc("mystery"), "building", bb["id"]) for bb in buildings]
        candidates += [(u["cost"], u["name"], "upgrade", u["id"]) for u in upgrades]
        if candidates:
            # the motivating target is the cheapest thing not yet affordable
            # (affordable items are already flagged in the shop)
            ahead = [c for c in candidates if c[0] > s["cookies"]]
            cost, name, kind, iid = min(ahead or candidates, key=lambda c: c[0])
            need = max(0.0, cost - s["cookies"])
            goal = {
                "name": name,
                "kind": kind,
                "id": iid,
                "cost": cost,
                "progress": min(1.0, s["cookies"] / cost) if cost else 1.0,
                "reviews": int(math.ceil(need / per_now)) if need > 0 and per_now > 0 else 0,
            }

        d = s["day"]
        return {
            "cookies": s["cookies"],
            "baked_run": s["baked_run"],
            "baked_total": s["baked_total"],
            "per_review": per_now,
            "per_review_base": base,
            "raw": total_raw,
            "mult": {
                "upgrades": self.mult_global_upgrades(),
                "achievements": self.mult_achievements(),
                "savoir": self.mult_savoir(),
                "streak": self.mult_streak(),
                "diplomas": self.mult_diplomas(),
                "total": self.mult_total(),
            },
            "combo": {
                "count": combo_count,
                "mult": self.combo_mult(combo_count),
                "cap": self.combo_cap(),
                "window": self.combo_window(),
                "remaining": max(0.0, self.combo_window() - (now - s["combo"]["last_ts"])) if alive else 0,
                "step": self.combo_step(),
            },
            "frenzy": {"left": s["frenzy"]["left"], "mult": FRENZY_MULT},
            "golden": {"token": self.golden["token"], "remaining": max(0.0, self.golden["expires"] - now)} if self.golden and self.golden["expires"] > now else None,
            "buildings": buildings,
            "upgrades": upgrades,
            "owned_upgrades": owned_upgrades,
            "achievements": achievements,
            "achievements_count": len(ach_owned),
            "perks": perks,
            "prestige": {
                "diplomas": s["diplomas"],
                "available": self.diplomas_available(),
                "pending": self.diplomas_pending(),
                "next_at": self.next_diploma_at(),
                "baked_total": s["baked_total"],
                "ascensions": s["ascensions"],
            },
            "streak": {**s["streak"], "cap": self.freeze_cap(), "freeze_cost": self.freeze_cost(), "step": self.streak_step(), "max_days": STREAK_MAX_DAYS},
            "mature": s["mature"],
            "day": {
                "reviews": d["reviews"],
                "baked": d["baked"],
                "cleared": d["cleared"],
                "max_combo": d["max_combo"],
                "quests": [{**q, "text": quest_text(q)} for q in d["quests"]],
                "jackpot_preview": base * (60 + d["reviews"]),
            },
            "stats": dict(s["stats"]),
            "goal": goal,
        }


def quest_text(q: dict) -> str:
    text = i18n.quest_template(q["kind"])
    return text.format(n=q["n"]) if text else "?"
