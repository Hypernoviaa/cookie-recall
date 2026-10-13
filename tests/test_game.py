import json
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cookierecall import content as C  # noqa: E402
from cookierecall.game import BASE_PER_REVIEW, Game, fmt_num  # noqa: E402


def answer(g, card=1, day=0, now=1000.0, secs=5.0, new=False, ivl=0, preview=False, hour=14, rng=None):
    return g.on_answer(card_id=card, was_new=new, ivl_before=ivl, seconds=secs, is_preview=preview,
                       day_id=day, now=now, hour=hour, rng=rng or random.Random(0))


class NoGolden(random.Random):
    def random(self):
        return 0.99


class TestEngine(unittest.TestCase):
    def test_corrupt_state_is_repaired(self):
        g = Game({"cookies": "lots", "stats": None, "buildings": {"mamie": 3}, "streak": {"count": 2.0}})
        self.assertEqual(g.s["cookies"], 0.0)
        self.assertEqual(g.s["stats"]["reviews_total"], 0)
        self.assertEqual(g.owned("mamie"), 3)
        self.assertEqual(g.s["streak"]["count"], 2)

    def test_first_answer_value(self):
        g = Game()
        r = answer(g, rng=NoGolden())
        self.assertAlmostEqual(r["gain"], BASE_PER_REVIEW * 1.01)
        self.assertIn("r0", g.s["achievements"])

    def test_every_grade_is_equal(self):
        # the engine never receives the grade: by construction it cannot reward lying
        import inspect
        self.assertNotIn("ease", inspect.signature(Game.on_answer).parameters)

    def test_repeat_card_is_damped(self):
        g = Game()
        a = answer(g, card=7, now=1000, rng=NoGolden())["gain"]
        b = answer(g, card=7, now=1010, rng=NoGolden())["gain"]
        c = answer(g, card=7, now=1020, rng=NoGolden())["gain"]
        self.assertLess(b, a * 0.6)
        self.assertLess(c, b)

    def test_too_fast_does_not_feed_combo(self):
        g = Game()
        answer(g, card=1, now=1000, rng=NoGolden())
        r = answer(g, card=2, now=1001, secs=0.3, rng=NoGolden())
        self.assertEqual(r["combo"], 1)
        self.assertEqual(r["reason"], "too_fast")

    def test_combo_breaks_after_window(self):
        g = Game()
        for i in range(10):
            answer(g, card=i, now=1000 + i * 10, rng=NoGolden())
        self.assertEqual(g.s["combo"]["count"], 10)
        r = answer(g, card=99, now=1000 + 10 * 10 + 500, rng=NoGolden())
        self.assertEqual(r["combo"], 1)

    def test_new_card_cap(self):
        g = Game(rules={"new_cards_full_reward_per_day": 2})
        res = [answer(g, card=i, now=1000 + i * 600, new=True, rng=NoGolden()) for i in range(3)]
        self.assertEqual([r["factor"] for r in res], [1.0, 1.0, 0.25])
        self.assertEqual(res[2]["reason"], "new_cap")

    def test_day_rollover_resets_repeat_tracking(self):
        g = Game()
        answer(g, card=5, day=0, rng=NoGolden())
        r = answer(g, card=5, day=1, now=99999, rng=NoGolden())
        self.assertEqual(r["factor"], 1.0)

    def test_golden_cookie(self):
        g = Game()

        class Always(random.Random):
            def random(self):
                return 0.0

        r = answer(g, rng=Always())
        spawn = [e for e in r["events"] if e["type"] == "golden_spawn"]
        self.assertEqual(len(spawn), 1)
        self.assertFalse(g.click_golden("wrong", 1001)["ok"])
        res = g.click_golden(spawn[0]["token"], 1002, rng=random.Random(3))
        self.assertTrue(res["ok"])
        self.assertFalse(g.click_golden(spawn[0]["token"], 1003)["ok"])  # single use

    def test_golden_expires(self):
        g = Game()
        g.golden = {"token": "abc", "expires": 1000.0}
        self.assertFalse(g.click_golden("abc", 1010.0)["ok"])

    def test_clear_jackpot_and_streak(self):
        g = Game()
        answer(g, day=0, rng=NoGolden())
        self.assertEqual(g.on_clear_check(due_left=3, day_id=0), [])
        ev = g.on_clear_check(due_left=0, day_id=0)
        self.assertTrue(any(e["type"] == "jackpot" for e in ev))
        self.assertEqual(g.s["streak"]["count"], 1)
        self.assertFalse(any(e["type"] == "jackpot" for e in g.on_clear_check(0, 0)))  # once a day
        answer(g, day=1, now=99999, rng=NoGolden())
        g.on_clear_check(0, 1)
        self.assertEqual(g.s["streak"]["count"], 2)

    def test_clear_needs_a_review(self):
        g = Game()
        self.assertEqual(g.on_clear_check(0, 0), [])

    def test_streak_lost_or_frozen(self):
        g = Game()
        answer(g, day=0, rng=NoGolden())
        g.on_clear_check(0, 0)
        ev = g.ensure_day(3)  # missed days 1 and 2
        self.assertTrue(any(e["type"] == "streak_lost" for e in ev))
        self.assertEqual(g.s["streak"]["count"], 0)

        g2 = Game()
        answer(g2, day=0, rng=NoGolden())
        g2.on_clear_check(0, 0)
        g2.s["streak"]["freezes"] = 1
        ev = g2.ensure_day(2)  # missed day 1 only
        self.assertTrue(any(e["type"] == "freeze_used" for e in ev))
        self.assertEqual(g2.s["streak"]["count"], 1)
        self.assertEqual(g2.s["streak"]["freezes"], 0)

    def test_buying(self):
        g = Game()
        self.assertFalse(g.buy_building("mamie")["ok"])
        g.s["cookies"] = 1000
        self.assertEqual(g.building_cost("mamie"), 15)
        self.assertTrue(g.buy_building("mamie")["ok"])
        self.assertEqual(g.building_cost("mamie"), 18)  # ceil(15 * 1.15)
        self.assertFalse(g.buy_building("prisme")["ok"])  # not visible yet
        q = g.max_affordable("mamie")
        self.assertLessEqual(g.building_cost("mamie", q), g.s["cookies"])
        self.assertGreater(g.building_cost("mamie", q + 1), g.s["cookies"])
        before = g.per_review_base()
        self.assertTrue(g.buy_upgrade("b_mamie_0")["ok"])
        self.assertGreater(g.per_review_base(), before)
        self.assertFalse(g.buy_upgrade("b_mamie_0")["ok"])  # owned
        self.assertFalse(g.buy_upgrade("b_mamie_1")["ok"])  # needs 5 mamies

    def test_graduation(self):
        g = Game()
        self.assertFalse(g.graduate()["ok"])
        g.s["baked_total"] = 8.5e12
        g.s["baked_run"] = 8.5e12
        g.s["buildings"] = {"mamie": 50}
        self.assertEqual(g.diplomas_pending(), 2)
        self.assertTrue(g.graduate()["ok"])
        self.assertEqual(g.s["diplomas"], 2)
        self.assertEqual(g.s["buildings"], {})
        self.assertTrue(g.buy_perk("souschef")["ok"])
        self.assertFalse(g.buy_perk("memoire")["ok"])  # requires flair
        self.assertAlmostEqual(g.mult_diplomas(), 1.02)

    def test_mature_bonus_and_achievements(self):
        g = Game()
        g.set_mature(1000)
        self.assertAlmostEqual(g.mult_savoir(), 1.4)
        self.assertIn("m3", g.s["achievements"])

    def test_snapshot_is_json(self):
        g = Game()
        for i in range(30):
            answer(g, card=i, now=1000 + i * 5, rng=NoGolden())
        g.s["cookies"] = 1e6
        g.buy_building("mamie", "max")
        snap = g.snapshot(1200)
        json.dumps(snap)
        self.assertIsNotNone(snap["goal"])
        self.assertEqual(len(snap["day"]["quests"]), 3)

    def test_content_integrity(self):
        ids = [a.id for a in C.ACHIEVEMENTS]
        self.assertEqual(len(ids), len(set(ids)))
        ids = [u.id for u in C.UPGRADES]
        self.assertEqual(len(ids), len(set(ids)))
        for p in C.PERKS:
            self.assertTrue(not p.requires or p.requires in C.PERK_BY_ID)

    def test_fmt(self):
        self.assertEqual(fmt_num(12), "12")
        self.assertEqual(fmt_num(12345), "12 345")
        self.assertEqual(fmt_num(1.5e6), "1,5 M")
        self.assertEqual(fmt_num(2e9), "2 Md")


if __name__ == "__main__":
    unittest.main()
