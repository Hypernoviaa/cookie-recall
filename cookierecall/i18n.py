"""English translations of the game content and of the Python-side messages.

French is the reference language (content.py). Anything missing here falls
back to French, so a new item can never crash the game, only show in French.
"""

from __future__ import annotations

from . import content as C

LANG = "fr"  # set by integration; "fr" or "en"


def set_lang(code: str) -> None:
    global LANG
    LANG = "fr" if code == "fr" else "en"


def resolve(setting: str, anki_lang: str) -> str:
    """'auto' follows Anki: French interface -> French, anything else -> English."""
    if setting in ("fr", "en"):
        return setting
    return "fr" if (anki_lang or "").lower().startswith("fr") else "en"


# ---------------------------------------------------------------- buildings
BUILDINGS_EN = {
    "mamie": ("Granny", "Grannies", "She bakes cookies while you study. She believes in you."),
    "four": ("Wood oven", "Wood ovens", "Heated white-hot by your focus."),
    "champ": ("Wheat field", "Wheat fields", "Every card you learn grows a new ear of wheat."),
    "moulin": ("Windmill", "Windmills", "Grinds flour to the rhythm of your reviews."),
    "usine": ("Biscuit factory", "Biscuit factories", "Industrial production of sugary knowledge."),
    "banque": ("Sugar bank", "Sugar banks", "Your sugar earns compound interest."),
    "temple": ("Chocolate temple", "Chocolate temples", "Where the spacing effect is worshipped."),
    "tour": ("Wizard tower", "Wizard towers", "Summons cookies out of mnemonics."),
    "fusee": ("Cookie rocket", "Cookie rockets", "Brings back cookies from planet Biscuit."),
    "labo": ("Alchemy lab", "Alchemy labs", "Turns forgetting into gold."),
    "portail": ("Portal", "Portals", "Opens a door to the dough dimension."),
    "horloge": ("Time machine", "Time machines", "Brings back the cookies you would have eaten tomorrow."),
    "biblio": ("Infinite library", "Infinite libraries", "Every book holds a recipe that doesn't exist yet."),
    "prisme": ("Cosmic prism", "Cosmic prisms", "Turns the light of your neurons into cookies."),
}

TIER_NAMES_EN = ["Break-in", "Family recipe", "Organic ingredients", "Perfect bake", "Optimized line", "Ancestral craft", "Starred excellence", "Absolute perfection"]

UPGRADES_EN = {
    "g_0": ("Active recall", "Testing yourself beats rereading. +10% cookies."),
    "g_1": ("Forgetting curve", "You know it, it knows you. +10% cookies."),
    "g_2": ("Spacing effect", "Time between reviews is your friend. +15% cookies."),
    "g_3": ("Interference beaten", "No more mixing up two cards. +15% cookies."),
    "g_4": ("Memory palace", "Every room holds a batch. +20% cookies."),
    "g_5": ("Chunking", "Cut knowledge into bite-sized pieces. +20% cookies."),
    "g_6": ("Deep encoding", "You don't just remember, you understand. +25% cookies."),
    "g_7": ("Eidetic memory", "You've seen it all, kept it all. +30% cookies."),
    "c_0": ("Sturdy kneader", "The combo can climb 25 steps higher."),
    "c_1": ("Lively sourdough", "50% more time before the combo drops."),
    "c_2": ("Continuous batch", "The combo can climb 50 steps higher."),
    "c_3": ("Sacred fire", "Each combo step is worth 1.5% instead of 1%."),
    "c_4": ("Eternal oven", "The combo can climb 75 steps higher."),
    "o_0": ("Baker's luck", "Golden cookies appear 50% more often."),
    "o_1": ("Golden chips", "Frenzies last twice as long."),
    "o_2": ("Golden touch", "Golden cookies stay on screen twice as long."),
    "o_3": ("Golden alchemy", "\"Lucky\" rewards are doubled."),
    "o_4": ("Gold rush", "Golden cookies appear another 50% more often."),
    "m_0": ("Pastry cat", "Each achievement unlocked gives an extra +0.25% cookies."),
    "m_1": ("Apprentice cat", "Each achievement unlocked gives an extra +0.25% cookies."),
    "m_2": ("Chef cat", "Each achievement unlocked gives an extra +0.5% cookies."),
    "m_3": ("Starred cat", "Each achievement unlocked gives an extra +0.5% cookies."),
    "m_4": ("Legendary cat", "Each achievement unlocked gives an extra +1% cookies."),
    "s_0": ("Mature flashcards", "The Knowledge bonus (mature cards) is multiplied by 1.25."),
    "s_1": ("Deep roots", "The Knowledge bonus (mature cards) is multiplied by 1.25."),
    "s_2": ("Tree of knowledge", "The Knowledge bonus (mature cards) is multiplied by 1.5."),
    "s_3": ("Forest of knowledge", "The Knowledge bonus (mature cards) is multiplied by 1.5."),
    "s_4": ("Living library", "The Knowledge bonus (mature cards) is multiplied by 2."),
    "k_0": ("Routine", "You can hold one more Protective frosting for your streak."),
    "k_1": ("Ritual", "Each streak day gives +4% instead of +3%."),
}

PERKS_EN = {
    "souschef": ("Sous-chef", "Every new run starts with 10 Grannies and 5 Wood ovens."),
    "flair": ("Golden instinct", "Golden cookies appear 30% more often."),
    "glacage": ("Eternal frosting", "+1 frosting slot and the streak bonus is 50% higher."),
    "memoire": ("Working memory", "Double combo window and +25 combo steps."),
    "sucre": ("Slow sugar", "Frenzies last twice as long."),
    "negoce": ("Negotiator", "All buildings cost 5% less."),
    "erudition": ("Erudition", "The Knowledge bonus is multiplied by 1.5."),
    "pate": ("Mother dough", "Every new run starts with 1% of the cookies baked in the previous one."),
    "these": ("Thesis", "+25% cookies, forever."),
}

_ACH_EN_ROWS = {
    "r": ("reviews", [
        ("First card", "Do your first review with Cookie Recall."), ("Warm-up", "Do 10 reviews."), ("Getting serious", "Do 100 reviews."),
        ("Regular", "Do 500 reviews."), ("Mille-feuille", "Do 1,000 reviews."), ("Workaholic", "Do 2,500 reviews."),
        ("Review machine", "Do 5,000 reviews."), ("Ten thousand steps", "Do 10,000 reviews."), ("Encyclopedist", "Do 25,000 reviews."),
        ("Elephant memory", "Do 50,000 reviews."), ("Century of knowledge", "Do 100,000 reviews."),
    ]),
    "k": ("baked", [
        ("First batch", "Bake 1,000 cookies in total."), ("Neighbourhood bakery", "Bake 100,000 cookies."), ("Crumb millionaire", "Bake 1 million cookies."),
        ("Biscuit empire", "Bake 100 million cookies."), ("Sugar billionaire", "Bake 1 billion cookies."), ("Cookie economy", "Bake 100 billion cookies."),
        ("Trillion crumbs", "Bake 1 trillion cookies."), ("Chocolate galaxy", "Bake 100 trillion cookies."), ("Quadrillion", "Bake 1 quadrillion cookies."),
        ("Quintillion", "Bake 1 quintillion cookies."), ("Sextillion", "Bake 1 sextillion cookies."), ("Beyond the oven", "Bake 1 septillion cookies."),
    ]),
    "t": ("", [
        ("Craft district", "Own 100 buildings in total."), ("Industrial zone", "Own 500 buildings in total."),
        ("Megalopolis", "Own 1,000 buildings in total."), ("Factory planet", "Own 2,000 buildings in total."),
    ]),
    "c": ("", [
        ("Little flame", "Reach a combo of 10."), ("Wood fire", "Reach a combo of 25."), ("Blaze", "Reach a combo of 50."),
        ("Furnace", "Reach a combo of 100."), ("Forge heart", "Reach a combo of 150."), ("Supernova", "Reach a combo of 250."),
    ]),
    "o": ("", [
        ("A golden gleam", "Catch a golden cookie."), ("Gold hunter", "Catch 7 golden cookies."), ("Rush", "Catch 27 golden cookies."),
        ("Midas", "Catch 77 golden cookies."), ("Golden rain", "Catch 277 golden cookies."), ("Eternal jackpot", "Catch 777 golden cookies."),
    ]),
    "j": ("", [
        ("Oven cleared", "Finish all your due cards for the day."), ("A clean week", "Clear the oven 7 times."), ("A spotless month", "Clear the oven 30 times."),
        ("A hundred ovens", "Clear the oven 100 times."), ("A year of discipline", "Clear the oven 365 times."),
    ]),
    "s": ("", [
        ("Heating up", "A 3-day streak."), ("Perfect week", "A 7-day streak."), ("Fortnight", "A 14-day streak."), ("Iron month", "A 30-day streak."),
        ("Unstoppable", "A 60-day streak."), ("Centenarian", "A 100-day streak."), ("A whole year", "A 365-day streak."),
    ]),
    "m": ("", [
        ("Bud", "Have 50 mature cards (interval ≥ 21 days)."), ("Sprout", "Have 100 mature cards."), ("Shrub", "Have 500 mature cards."),
        ("Oak", "Have 1,000 mature cards."), ("Grove", "Have 2,500 mature cards."), ("Forest", "Have 5,000 mature cards."),
        ("Old-growth forest", "Have 10,000 mature cards."), ("Amazonia", "Have 25,000 mature cards."),
    ]),
    "q": ("", [
        ("First mission", "Complete a daily mission."), ("Missionary", "Complete 10 daily missions."),
        ("Special agent", "Complete 50 daily missions."), ("Counter legend", "Complete 200 daily missions."),
    ]),
    "u": ("", [
        ("Tinkerer", "Own 10 upgrades."), ("Engineer", "Own 30 upgrades."), ("Inventor", "Own 60 upgrades."), ("Genius", "Own 100 upgrades."),
    ]),
    "p": ("", [
        ("Graduate", "Receive your first diploma."), ("PhD student", "Graduate 3 times."), ("Professor emeritus", "Graduate 10 times."),
    ]),
    "d": ("", [
        ("Big day", "Do 200 reviews in a single day."), ("Marathoner", "Do 500 reviews in a single day."), ("Ultra-trail", "Do 1,000 reviews in a single day."),
    ]),
}
ACH_SPECIAL_EN = {
    "h_night": ("Night owl", "Review between midnight and 4 a.m."),
    "h_dawn": ("Early bird", "Review between 5 and 7 a.m."),
    "h_big_clear": ("Spring cleaning", "Clear the oven after 300 reviews in a day."),
    "h_frenzy_combo": ("Perfect storm", "Be in a Frenzy with a combo of at least 50."),
    "h_freeze": ("Saved by the frosting", "A Protective frosting saved your streak."),
    "h_patience": ("Comeback", "Come back after at least 7 days without reviewing."),
}
BUILDING_ACH_LABELS_EN = ["First steps", "Small fleet", "Centurion", "Dynasty"]

QUESTS_EN = {
    "reviews": "Do {n} reviews",
    "combo": "Reach a combo of {n}",
    "golden": "Catch {n} golden cookie(s)",
    "clear": "Clear the oven (all due cards)",
    "buy": "Buy {n} buildings",
    "mature_reviews": "Review {n} mature cards",
}

MISC_EN = {
    "mystery": "Mystery building",
    "locked_desc": "Keep reviewing to discover it.",
    "secret_desc": "Secret achievement.",
}
MISC_FR = {
    "mystery": "Bâtiment mystère",
    "locked_desc": "Continue de réviser pour le découvrir.",
    "secret_desc": "Succès secret.",
}

# ---------------------------------------------------------------- python-side messages
MSG = {
    "fr": {
        "error": "Cookie Recall a rencontré une erreur (détails dans la console). Tes révisions ne sont pas affectées.",
        "hud_later": "Le compteur sera mis à jour à ta prochaine session de révision.",
        "toolbar": "Cookie Recall",
        "toolbar_tip": "Ouvrir la boulangerie Cookie Recall",
        "menu_open": "Cookie Recall : ouvrir la boulangerie",
        "menu_reset": "Cookie Recall : remettre à zéro…",
        "reset_q": "Remettre Cookie Recall à zéro ?\n\nTous tes cookies, bâtiments, succès, diplômes et ta série seront effacés. Tes cartes Anki ne sont pas touchées.",
        "reset_done": "Cookie Recall a été remis à zéro.",
        "jackpot_tip": "Four vidé ! +{gain} cookies · série de {streak} j",
        "lang_restart": "La langue du menu Outils changera au prochain démarrage d'Anki.",
    },
    "en": {
        "error": "Cookie Recall ran into an error (details in the console). Your reviews are not affected.",
        "hud_later": "The counter will update at your next review session.",
        "toolbar": "Cookie Recall",
        "toolbar_tip": "Open the Cookie Recall bakery",
        "menu_open": "Cookie Recall: open the bakery",
        "menu_reset": "Cookie Recall: reset…",
        "reset_q": "Reset Cookie Recall?\n\nAll your cookies, buildings, achievements, diplomas and your streak will be erased. Your Anki cards are not touched.",
        "reset_done": "Cookie Recall has been reset.",
        "jackpot_tip": "Oven cleared! +{gain} cookies · {streak}-day streak",
        "lang_restart": "The Tools menu language will change the next time Anki starts.",
    },
}


def msg(key: str, **kw) -> str:
    return MSG.get(LANG, MSG["fr"]).get(key, MSG["fr"][key]).format(**kw)


# ---------------------------------------------------------------- content lookups
def building(b: C.Building) -> tuple[str, str, str]:
    if LANG == "en" and b.id in BUILDINGS_EN:
        return BUILDINGS_EN[b.id]
    return b.name, b.plural, b.desc


def upgrade(u: C.Upgrade) -> tuple[str, str]:
    if LANG != "en":
        return u.name, u.desc
    if u.kind == "building":
        b = C.BUILDING_BY_ID[u.target]
        _n, plural, _d = building(b)
        return f"{plural} · {TIER_NAMES_EN[u.tier]}", f"{plural} are twice as efficient."
    return UPGRADES_EN.get(u.id, (u.name, u.desc))


def perk(p: C.Perk) -> tuple[str, str]:
    if LANG == "en":
        return PERKS_EN.get(p.id, (p.name, p.desc))
    return p.name, p.desc


def achievement(a: C.Achievement) -> tuple[str, str]:
    if LANG != "en":
        return a.name, a.desc
    if a.id in ACH_SPECIAL_EN:
        return ACH_SPECIAL_EN[a.id]
    if a.id.startswith("b_"):
        bid, idx = a.id[2:].rsplit("_", 1)
        b = C.BUILDING_BY_ID[bid]
        name, plural, _d = building(b)
        n = int(a.threshold)
        return f"{name} · {BUILDING_ACH_LABELS_EN[int(idx)]}", f"Own {n} {name if n == 1 else plural}."
    prefix, idx = a.id[0], a.id[1:]
    rows = _ACH_EN_ROWS.get(prefix)
    if rows and idx.isdigit() and int(idx) < len(rows[1]):
        return rows[1][int(idx)]
    return a.name, a.desc


def quest_template(kind: str) -> str | None:
    if LANG == "en":
        return QUESTS_EN.get(kind)
    t = C.QUEST_BY_KIND.get(kind)
    return t.text if t else None


def misc(key: str) -> str:
    return (MISC_EN if LANG == "en" else MISC_FR)[key]
