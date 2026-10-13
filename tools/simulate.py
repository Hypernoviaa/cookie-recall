"""Balance simulation: a player reviewing N cards a day, buying greedily."""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cookierecall import content as C  # noqa: E402
from cookierecall.game import Game, fmt_num  # noqa: E402


def best_purchase(g: Game):
    """Greedy: best payback (cost / gain in per-review value)."""
    base_now = g.per_review_base()
    best = None
    for b in C.BUILDINGS:
        if not g.building_visible(b.id):
            continue
        cost = g.building_cost(b.id)
        gain = g.building_cpr(b.id) * g.mult_total()
        score = cost / max(gain, 1e-9)
        if best is None or score < best[0]:
            best = (score, cost, "b", b.id)
    for u in C.UPGRADES:
        if g.has_upgrade(u.id) or not g.upgrade_unlocked(u):
            continue
        # estimate gain by applying it on a copy
        g.s["upgrades"].append(u.id)
        after = g.per_review_base()
        g.s["upgrades"].pop()
        gain = after - base_now
        score = u.cost / gain if gain > 0 else u.cost / max(base_now * 0.02, 1e-9)
        if best is None or score < best[0]:
            best = (score, u.cost, "u", u.id)
    return best


def run(reviews_per_day=200, days=365, seed=1, verbose_days=(1, 2, 3, 7, 14, 30, 60, 90, 180, 365)):
    rng = random.Random(seed)
    g = Game()
    now = 1_000_000.0
    mature = 0
    first_seen = {}
    graduated_days = []
    for day in range(days):
        g.ensure_day(day)
        reviews_today = max(10, int(rng.gauss(reviews_per_day, reviews_per_day * 0.2)))
        n = 0
        while n < reviews_today:
            session = min(reviews_today - n, rng.randint(25, 80))
            for _ in range(session):
                now += max(1.2, rng.gauss(8, 3))
                ev = g.on_answer(card_id=rng.randrange(10**9), was_new=rng.random() < 0.15, ivl_before=rng.choice([0, 3, 10, 30, 60]),
                                 seconds=max(0.5, rng.gauss(6, 3)), is_preview=False, day_id=day, now=now, hour=14, rng=rng)
                for e in ev["events"]:
                    if e["type"] == "golden_spawn" and rng.random() < 0.8:
                        g.click_golden(e["token"], now + 3, rng)
                n += 1
                # buy greedily (every few reviews, like a human glancing at the shop)
                for _ in range(50 if n % 5 == 0 else 0):
                    bp = best_purchase(g)
                    if not bp or bp[1] > g.s["cookies"]:
                        break
                    if bp[2] == "b":
                        g.buy_building(bp[3])
                    else:
                        g.buy_upgrade(bp[3])
            now += rng.uniform(600, 7200)  # break between sessions kills combo
        mature += int(reviews_per_day * 0.08)
        g.set_mature(mature)
        if rng.random() < 0.9:
            g.on_clear_check(0, day)
        if g.s["streak"]["count"] >= 3 and g.s["streak"]["freezes"] < g.freeze_cap():
            g.buy_freeze()
        for b in C.BUILDINGS:
            if g.owned(b.id) and b.id not in first_seen:
                first_seen[b.id] = day + 1
        # graduate when it would at least double diplomas (simple heuristic)
        if g.diplomas_pending() >= max(1, g.s["diplomas"]):
            res = g.graduate()
            graduated_days.append((day + 1, res.get("diplomas")))
            for p in C.PERKS:
                g.buy_perk(p.id)
        if day + 1 in verbose_days:
            print(f"  jour {day + 1:3d}: banque {fmt_num(g.s['cookies']):>10} | /révision {fmt_num(g.per_review_base()):>10} | "
                  f"cuits {fmt_num(g.s['baked_total']):>10} | bâtiments {sum(g.s['buildings'].values()):4d} | "
                  f"améliorations {len(g.s['upgrades']):3d} | succès {len(g.s['achievements']):3d} | diplômes {g.s['diplomas']}")
        now += 3600 * 12
    print("  premier achat par bâtiment (jour):", {k: v for k, v in first_seen.items()})
    print("  remises de diplôme (jour, diplômes):", graduated_days[:8])
    return g


if __name__ == "__main__":
    for rpd in (50, 200, 500):
        print(f"\n=== {rpd} révisions / jour ===")
        run(rpd)
