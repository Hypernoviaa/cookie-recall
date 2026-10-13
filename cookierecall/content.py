"""Static game content for Cookie Recall: buildings, upgrades, achievements, perks.

Pure data, no Anki imports, so it can be unit-tested and simulated outside Anki.
Pacing: a review is the only "tick". Each building tier multiplies the
payback (cost / cookies-per-review) by ~2.45, starting at 30 reviews, so the
game opens fast and stretches over months. Tuned with tools/simulate.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Buildings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Building:
    id: str
    name: str
    plural: str
    desc: str
    base_cost: float
    cpr: float  # cookies per review, per unit, before multipliers


BUILDINGS: list[Building] = [
    Building("mamie", "Mamie", "Mamies", "Elle fait des cookies pendant que tu révises. Elle croit en toi.", 15, 0.5),
    Building("four", "Four à bois", "Fours à bois", "Chauffé à blanc par ta concentration.", 100, 1.4),
    Building("champ", "Champ de blé", "Champs de blé", "Chaque carte apprise fait pousser un épi.", 1_100, 6.1),
    Building("moulin", "Moulin", "Moulins", "Moud la farine au rythme de tes révisions.", 12_000, 27),
    Building("usine", "Usine à biscuits", "Usines à biscuits", "Production industrielle de savoir sucré.", 130_000, 120),
    Building("banque", "Banque de sucre", "Banques de sucre", "Ton sucre rapporte des intérêts composés.", 1.4e6, 530),
    Building("temple", "Temple du chocolat", "Temples du chocolat", "On y vénère l'effet d'espacement.", 2e7, 3_100),
    Building("tour", "Tour du sorcier", "Tours du sorcier", "Invoque des cookies à partir de mnémotechniques.", 3.3e8, 21_000),
    Building("fusee", "Fusée cookie", "Fusées cookie", "Rapporte des cookies de la planète Biscuit.", 5.1e9, 130_000),
    Building("labo", "Labo d'alchimie", "Labos d'alchimie", "Transforme l'oubli en or.", 7.5e10, 790_000),
    Building("portail", "Portail", "Portails", "Ouvre une porte vers la dimension de la pâte.", 1e12, 4.3e6),
    Building("horloge", "Machine temporelle", "Machines temporelles", "Ramène les cookies que tu aurais mangés demain.", 1.4e13, 2.4e7),
    Building("biblio", "Bibliothèque infinie", "Bibliothèques infinies", "Chaque livre contient une recette qui n'existe pas encore.", 1.7e14, 1.2e8),
    Building("prisme", "Prisme cosmique", "Prismes cosmiques", "Convertit la lumière de tes neurones en cookies.", 2.1e15, 6.1e8),
]
BUILDING_BY_ID = {b.id: b for b in BUILDINGS}
COST_GROWTH = 1.15

# ---------------------------------------------------------------------------
# Upgrades
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Upgrade:
    id: str
    name: str
    desc: str
    cost: float
    kind: str  # building | global | combo | golden | milk | savoir | streak
    icon: str  # icon key (svg file stem)
    tier: int = 0  # visual frame tier 0..7
    # effect parameters
    target: str = ""
    value: float = 0.0
    # unlock condition: (metric, threshold)
    unlock: tuple[str, float] = ("none", 0)


BUILDING_TIERS = [
    # (owned threshold, cost multiplier of base cost, name)
    (1, 10, "Rodage"),
    (5, 50, "Recette de famille"),
    (25, 500, "Ingrédients bio"),
    (50, 5_000, "Cuisson parfaite"),
    (100, 50_000, "Chaîne optimisée"),
    (150, 5e6, "Savoir-faire ancestral"),
    (200, 5e8, "Excellence étoilée"),
    (250, 5e10, "Perfection absolue"),
]


def _building_upgrades() -> list[Upgrade]:
    out = []
    for b in BUILDINGS:
        for i, (owned, mult, tier_name) in enumerate(BUILDING_TIERS):
            out.append(
                Upgrade(
                    id=f"b_{b.id}_{i}",
                    name=f"{b.plural} · {tier_name}",
                    desc=f"Les {b.plural.lower()} sont deux fois plus efficaces.",
                    cost=b.base_cost * mult,
                    kind="building",
                    icon=f"b_{b.id}",
                    tier=i,
                    target=b.id,
                    value=2.0,
                    unlock=(f"own:{b.id}", owned),
                )
            )
    return out


_GLOBAL = [
    # reviews this run, cost, name, desc, bonus
    (50, 500, "Rappel actif", "Se tester vaut mieux que relire. +10 % de cookies.", 0.10),
    (250, 25_000, "Courbe de l'oubli", "Tu la connais, elle te connaît. +10 % de cookies.", 0.10),
    (750, 2.5e6, "Effet d'espacement", "Le temps entre deux révisions est ton allié. +15 % de cookies.", 0.15),
    (2_000, 2.5e8, "Interférence vaincue", "Plus de confusion entre deux cartes. +15 % de cookies.", 0.15),
    (5_000, 2.5e10, "Palais de mémoire", "Chaque pièce contient une fournée. +20 % de cookies.", 0.20),
    (10_000, 2.5e12, "Fragmentation", "Découpe le savoir en bouchées. +20 % de cookies.", 0.20),
    (20_000, 2.5e14, "Encodage profond", "Tu ne retiens plus, tu comprends. +25 % de cookies.", 0.25),
    (40_000, 2.5e16, "Mémoire éidétique", "Tu as tout vu, tout retenu. +30 % de cookies.", 0.30),
]

_COMBO = [
    # max combo, cost, name, desc, (param, value)
    (25, 5_000, "Pétrin robuste", "Le combo peut monter 25 crans plus haut.", ("cap", 25)),
    (50, 5e5, "Levain vivace", "Tu as 50 % de temps en plus avant que le combo ne retombe.", ("window", 0.5)),
    (80, 5e7, "Fournée continue", "Le combo peut monter 50 crans plus haut.", ("cap", 50)),
    (120, 5e9, "Feu sacré", "Chaque cran de combo vaut 1,5 % au lieu de 1 %.", ("step", 0.005)),
    (175, 5e11, "Four éternel", "Le combo peut monter 75 crans plus haut.", ("cap", 75)),
]

_GOLDEN = [
    (3, 7_777, "Chance du boulanger", "Les cookies dorés apparaissent 50 % plus souvent.", ("freq", 0.5)),
    (10, 777_777, "Pépites dorées", "Les Frénésies durent deux fois plus longtemps.", ("frenzy", 1.0)),
    (27, 7.77e8, "Main verte dorée", "Les cookies dorés restent deux fois plus longtemps à l'écran.", ("life", 1.0)),
    (50, 7.77e10, "Alchimie dorée", "Les gains « Chance » sont doublés.", ("lucky", 1.0)),
    (100, 7.77e13, "Ruée vers l'or", "Les cookies dorés apparaissent encore 50 % plus souvent.", ("freq", 0.5)),
]

_MILK = [
    # achievements count, cost, name, bonus per achievement added
    (10, 9e4, "Chat pâtissier", 0.0025),
    (25, 9e7, "Chat apprenti", 0.0025),
    (50, 9e10, "Chat chef", 0.005),
    (75, 9e13, "Chat étoilé", 0.005),
    (100, 9e16, "Chat légendaire", 0.01),
]

_SAVOIR = [
    # mature cards, cost, name
    (100, 1e4, "Fiches mûres", 0.25),
    (500, 1e7, "Racines profondes", 0.25),
    (1_500, 1e10, "Arbre du savoir", 0.5),
    (5_000, 1e13, "Forêt de connaissances", 0.5),
    (15_000, 1e16, "Bibliothèque vivante", 1.0),
]


def _misc_upgrades() -> list[Upgrade]:
    out: list[Upgrade] = []
    for i, (thr, cost, name, desc, bonus) in enumerate(_GLOBAL):
        out.append(Upgrade(f"g_{i}", name, desc, cost, "global", "u_brain", min(i, 7), value=bonus, unlock=("reviews_run", thr)))
    for i, (thr, cost, name, desc, (param, val)) in enumerate(_COMBO):
        out.append(Upgrade(f"c_{i}", name, desc, cost, "combo", "u_flame", min(i + 1, 7), target=param, value=val, unlock=("max_combo", thr)))
    for i, (thr, cost, name, desc, (param, val)) in enumerate(_GOLDEN):
        out.append(Upgrade(f"o_{i}", name, desc, cost, "golden", "u_golden", min(i + 2, 7), target=param, value=val, unlock=("golden_clicked", thr)))
    for i, (thr, cost, name, val) in enumerate(_MILK):
        pct = f"{val * 100:g}".replace(".", ",")
        out.append(Upgrade(f"m_{i}", name, f"Chaque succès débloqué donne +{pct} % de cookies en plus.", cost, "milk", "u_cat", min(i + 1, 7), value=val, unlock=("achievements", thr)))
    for i, (thr, cost, name, val) in enumerate(_SAVOIR):
        out.append(Upgrade(f"s_{i}", name, f"Le bonus de Savoir (cartes mûres) est multiplié par {1 + val:g}.".replace(".", ","), cost, "savoir", "u_sapling", min(i + 1, 7), value=val, unlock=("mature", thr)))
    out.append(Upgrade("k_0", "Routine", "Tu peux stocker un Glaçage protecteur de plus pour ta série.", 50_000, "streak", "u_freeze", 2, target="freeze_cap", value=1, unlock=("streak", 3)))
    out.append(Upgrade("k_1", "Rituel", "Chaque jour de série donne +4 % au lieu de +3 %.", 5e8, "streak", "u_calendar", 4, target="streak_step", value=0.01, unlock=("streak", 14)))
    return out


UPGRADES: list[Upgrade] = _building_upgrades() + _misc_upgrades()
UPGRADE_BY_ID = {u.id: u for u in UPGRADES}

# ---------------------------------------------------------------------------
# Heavenly perks (bought with Diplômes, survive graduation)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Perk:
    id: str
    name: str
    desc: str
    cost: int
    requires: str = ""


PERKS: list[Perk] = [
    Perk("souschef", "Sous-chef", "Chaque nouvelle promotion commence avec 10 Mamies et 5 Fours à bois.", 1),
    Perk("flair", "Flair doré", "Les cookies dorés apparaissent 30 % plus souvent.", 3, "souschef"),
    Perk("glacage", "Glaçage éternel", "+1 Glaçage stockable et le bonus de série est augmenté de 50 %.", 5, "souschef"),
    Perk("memoire", "Mémoire de travail", "Fenêtre de combo doublée et +25 crans de combo.", 7, "flair"),
    Perk("sucre", "Sucre lent", "Les Frénésies durent deux fois plus longtemps.", 10, "flair"),
    Perk("negoce", "Négociateur", "Tous les bâtiments coûtent 5 % de moins.", 15, "glacage"),
    Perk("erudition", "Érudition", "Le bonus de Savoir est multiplié par 1,5.", 20, "memoire"),
    Perk("pate", "Pâte mère", "Chaque nouvelle promotion commence avec 1 % des cookies cuits lors de la précédente.", 30, "negoce"),
    Perk("these", "Thèse", "+25 % de cookies, pour toujours.", 50, "erudition"),
]
PERK_BY_ID = {p.id: p for p in PERKS}

# ---------------------------------------------------------------------------
# Achievements (each one: +1 % cookies, boosted by "Chats")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    desc: str
    metric: str
    threshold: float
    icon: str
    hidden: bool = False


def _ach() -> list[Achievement]:
    a: list[Achievement] = []

    def add(prefix, metric, icon, rows, hidden=False):
        for i, (thr, name, desc) in enumerate(rows):
            a.append(Achievement(f"{prefix}{i}", name, desc, metric, thr, icon, hidden))

    add("r", "reviews_total", "a_card", [
        (1, "Première carte", "Faire ta première révision avec Cookie Recall."),
        (10, "Échauffement", "Faire 10 révisions."),
        (100, "Ça devient sérieux", "Faire 100 révisions."),
        (500, "Habitué", "Faire 500 révisions."),
        (1_000, "Mille-feuille", "Faire 1 000 révisions."),
        (2_500, "Bourreau de travail", "Faire 2 500 révisions."),
        (5_000, "Machine à réviser", "Faire 5 000 révisions."),
        (10_000, "Dix mille pas", "Faire 10 000 révisions."),
        (25_000, "Encyclopédiste", "Faire 25 000 révisions."),
        (50_000, "Mémoire d'éléphant", "Faire 50 000 révisions."),
        (100_000, "Centenaire du savoir", "Faire 100 000 révisions."),
    ])
    add("k", "baked_total", "a_cookie", [
        (1_000, "Première fournée", "Cuire 1 000 cookies au total."),
        (100_000, "Boulangerie de quartier", "Cuire 100 000 cookies."),
        (1e6, "Millionnaire en miettes", "Cuire 1 million de cookies."),
        (1e8, "Empire du biscuit", "Cuire 100 millions de cookies."),
        (1e9, "Milliardaire sucré", "Cuire 1 milliard de cookies."),
        (1e11, "Économie cookie", "Cuire 100 milliards de cookies."),
        (1e12, "Billion de miettes", "Cuire 1 billion de cookies."),
        (1e14, "Galaxie chocolatée", "Cuire 100 billions de cookies."),
        (1e15, "Billiard", "Cuire 1 billiard de cookies."),
        (1e18, "Trillion", "Cuire 1 trillion de cookies."),
        (1e21, "Trilliard", "Cuire 1 trilliard de cookies."),
        (1e24, "Au-delà du four", "Cuire 1 quadrillion de cookies."),
    ])
    for b in BUILDINGS:
        for i, (n, label) in enumerate([(1, "Premier pas"), (50, "Petite flotte"), (100, "Centurion"), (200, "Dynastie")]):
            a.append(Achievement(f"b_{b.id}_{i}", f"{b.name} · {label}", f"Posséder {n} {b.name if n == 1 else b.plural}.", f"own:{b.id}", n, f"b_{b.id}"))
    add("t", "buildings_total", "a_oven", [
        (100, "Zone artisanale", "Posséder 100 bâtiments au total."),
        (500, "Zone industrielle", "Posséder 500 bâtiments au total."),
        (1_000, "Mégalopole", "Posséder 1 000 bâtiments au total."),
        (2_000, "Planète-usine", "Posséder 2 000 bâtiments au total."),
    ])
    add("c", "max_combo", "a_flame", [
        (10, "Petite flamme", "Atteindre un combo de 10."),
        (25, "Feu de bois", "Atteindre un combo de 25."),
        (50, "Brasier", "Atteindre un combo de 50."),
        (100, "Fournaise", "Atteindre un combo de 100."),
        (150, "Cœur de forge", "Atteindre un combo de 150."),
        (250, "Supernova", "Atteindre un combo de 250."),
    ])
    add("o", "golden_clicked", "a_golden", [
        (1, "Un éclat doré", "Attraper un cookie doré."),
        (7, "Chasseur d'or", "Attraper 7 cookies dorés."),
        (27, "Ruée", "Attraper 27 cookies dorés."),
        (77, "Midas", "Attraper 77 cookies dorés."),
        (277, "Pluie d'or", "Attraper 277 cookies dorés."),
        (777, "Jackpot éternel", "Attraper 777 cookies dorés."),
    ])
    add("j", "jackpots", "a_check", [
        (1, "Four vidé", "Terminer toutes tes cartes dues de la journée."),
        (7, "Une semaine propre", "Vider le four 7 fois."),
        (30, "Un mois impeccable", "Vider le four 30 fois."),
        (100, "Cent fours", "Vider le four 100 fois."),
        (365, "Une année de discipline", "Vider le four 365 fois."),
    ])
    add("s", "streak_best", "a_calendar", [
        (3, "Ça chauffe", "Une série de 3 jours."),
        (7, "Semaine parfaite", "Une série de 7 jours."),
        (14, "Quinzaine", "Une série de 14 jours."),
        (30, "Mois de fer", "Une série de 30 jours."),
        (60, "Inarrêtable", "Une série de 60 jours."),
        (100, "Centenaire", "Une série de 100 jours."),
        (365, "Une année entière", "Une série de 365 jours."),
    ])
    add("m", "mature", "a_sapling", [
        (50, "Bourgeon", "Avoir 50 cartes mûres (intervalle ≥ 21 jours)."),
        (100, "Jeune pousse", "Avoir 100 cartes mûres."),
        (500, "Arbrisseau", "Avoir 500 cartes mûres."),
        (1_000, "Chêne", "Avoir 1 000 cartes mûres."),
        (2_500, "Bosquet", "Avoir 2 500 cartes mûres."),
        (5_000, "Forêt", "Avoir 5 000 cartes mûres."),
        (10_000, "Forêt primaire", "Avoir 10 000 cartes mûres."),
        (25_000, "Amazonie", "Avoir 25 000 cartes mûres."),
    ])
    add("q", "quests_done", "a_scroll", [
        (1, "Première mission", "Terminer une mission du jour."),
        (10, "Missionnaire", "Terminer 10 missions du jour."),
        (50, "Agent spécial", "Terminer 50 missions du jour."),
        (200, "Légende du comptoir", "Terminer 200 missions du jour."),
    ])
    add("u", "upgrades_owned", "a_star", [
        (10, "Bricoleur", "Posséder 10 améliorations."),
        (30, "Ingénieur", "Posséder 30 améliorations."),
        (60, "Inventeur", "Posséder 60 améliorations."),
        (100, "Génie", "Posséder 100 améliorations."),
    ])
    add("p", "ascensions", "a_diploma", [
        (1, "Diplômé", "Recevoir ton premier diplôme."),
        (3, "Doctorant", "Être diplômé 3 fois."),
        (10, "Professeur émérite", "Être diplômé 10 fois."),
    ])
    add("d", "day_reviews_best", "a_card", [
        (200, "Grosse journée", "Faire 200 révisions en une journée."),
        (500, "Marathonien", "Faire 500 révisions en une journée."),
        (1_000, "Ultra-trail", "Faire 1 000 révisions en une journée."),
    ])
    a += [
        Achievement("h_night", "Noctambule", "Réviser entre minuit et 4 h du matin.", "flag:night", 1, "a_moon", True),
        Achievement("h_dawn", "Lève-tôt", "Réviser entre 5 h et 7 h du matin.", "flag:dawn", 1, "a_sun", True),
        Achievement("h_big_clear", "Grand nettoyage", "Vider le four après 300 révisions dans la journée.", "flag:big_clear", 1, "a_check", True),
        Achievement("h_frenzy_combo", "Tempête parfaite", "Être en Frénésie avec un combo d'au moins 50.", "flag:storm", 1, "a_golden", True),
        Achievement("h_freeze", "Sauvé par le glaçage", "Un Glaçage protecteur a sauvé ta série.", "flag:freeze_used", 1, "a_freeze", True),
        Achievement("h_patience", "Retour en force", "Reprendre après au moins 7 jours sans réviser.", "flag:comeback", 1, "a_sun", True),
    ]
    return a


ACHIEVEMENTS: list[Achievement] = _ach()
ACHIEVEMENT_BY_ID = {a.id: a for a in ACHIEVEMENTS}

# ---------------------------------------------------------------------------
# Daily quests
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuestTemplate:
    kind: str
    targets: tuple[int, ...]
    text: str  # with {n}
    reward_reviews: tuple[int, ...]  # reward = per-review value x this, per target


QUESTS: list[QuestTemplate] = [
    QuestTemplate("reviews", (40, 80, 150), "Faire {n} révisions", (30, 60, 110)),
    QuestTemplate("combo", (20, 40, 70), "Atteindre un combo de {n}", (30, 60, 100)),
    QuestTemplate("golden", (1, 2, 3), "Attraper {n} cookie(s) doré(s)", (40, 70, 100)),
    QuestTemplate("clear", (1,), "Vider le four (toutes les cartes dues)", (90,)),
    QuestTemplate("buy", (3, 6, 10), "Acheter {n} bâtiments", (20, 35, 50)),
    QuestTemplate("mature_reviews", (10, 25, 50), "Réviser {n} cartes mûres", (30, 55, 90)),
]
QUEST_BY_KIND = {q.kind: q for q in QUESTS}
