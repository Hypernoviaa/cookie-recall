# Cookie Recall

Un Cookie Clicker pour Anki, où l'on ne peut pas cliquer sur le cookie.
Les cookies ne se gagnent qu'en révisant tes cartes, et tout le jeu reste à l'intérieur d'Anki :

- **Pendant les révisions** : un petit compteur dans un coin, avec le « +N » à chaque réponse, le combo, le cookie doré, le prochain achat et les succès.
- **Sur l'écran des paquets** : la boulangerie complète (une devanture avec un store et un tableau noir), avec la vitrine, la boutique, les missions du jour, les succès, les diplômes et les statistiques.
- **Sur l'écran d'un paquet** : un bandeau d'une ligne avec un bouton vers la boulangerie.
- **Partout ailleurs** : le *thème Cookie Recall* habille tout Anki dans le même univers (barre du haut, liste des paquets, ajout de cartes, navigateur, statistiques, options de paquet, menus), en clair comme en sombre. Il ne touche jamais au contenu de tes cartes et se désactive d'un clic.

Et aussi :
- **Réviser en un clic** : une carte « Réviser » au-dessus de tes paquets (ou la touche **S**) et un bouton ▶ Réviser sur chaque paquet t'emmènent directement aux révisions, sans passer par l'écran intermédiaire.
- **Des cartes plus belles** : les cartes au style par défaut deviennent une fiche papier posée sur un bureau, avec une police plus agréable et des boutons de réponse colorés. Les cartes qui ont leur propre style restent exactement comme elles sont.
- **5 palettes de couleurs** : Pistache, Framboise, Myrtille, Chocolat et Lavande, pour la boulangerie, le compteur, les cartes et tout le thème d'Anki (bouton 🎨 sur le store).

Disponible en **français et en anglais** : la langue suit celle d'Anki, ou se choisit dans les réglages.

Fonctionne sur Anki Desktop ≥ 23.10 (testé sur 26.9.3, en thème clair et sombre). Les add-ons ne tournent pas sur AnkiMobile ni AnkiDroid.

## Installation

1. Double-clique sur `cookierecall.ankiaddon`, ou passe par *Outils → Modules → Installer depuis un fichier…*.
2. Redémarre Anki.

La partie est enregistrée dans ta collection et se synchronise avec AnkiWeb.

## Le système de jeu

### Aucune production passive

Les bâtiments ne produisent rien tout seuls. Ils augmentent **la valeur de chaque révision**.
Sans révision, rien ne bouge, même avec 500 Mamies. C'est la différence fondamentale avec Cookie Clicker.

### Ce que rapporte une révision

```
gain = (3 + Σ bâtiments) × améliorations × succès × Savoir × série × diplômes × combo × frénésie × anti-farm
```

- **14 bâtiments** : de la Mamie (15 cookies) au Prisme cosmique (2,1 billiards). Le coût monte de 15 % par unité. Chaque palier multiplie la rentabilité par environ 2,45, si bien que le jeu démarre vite puis s'étire sur des mois.
- **Environ 130 améliorations** : ×2 par bâtiment à 1, 5, 25, 50, 100, 150, 200 et 250 unités. S'y ajoutent les techniques d'apprentissage (Rappel actif, Effet d'espacement…) et des améliorations de combo, de cookie doré, de « chats » et de Savoir.
- **Combo** : chaque révision enchaînée sans pause de plus de 2 minutes ajoute +1 % (plafonné à 50, améliorable). C'est la régularité qui compte, jamais la vitesse.
- **Cookie doré** : il apparaît environ une révision sur 40, en bord d'écran, pendant 14 s. Il donne « Chance » (gros gain), « Frénésie » (×7 pendant 7 révisions) ou « Pluie de cookies ». C'est une récompense variable, le ressort le plus puissant du genre.

### Les boucles liées au vrai apprentissage

- **Four vidé** (le jackpot du jour) : termine *toutes* tes cartes dues de la journée. Tu gagnes un jackpot qui vaut 60 révisions plus 1 par révision faite ce jour-là, et +1 jour de **série**.
- **Série** : +3 % par jour (jusqu'à 30 jours). Le **Glaçage protecteur**, acheté avec des cookies, sauve la série si tu manques un jour.
- **Savoir** : +1 % pour 25 cartes mûres (intervalle ≥ 21 jours). C'est le seul bonus qui mesure ce que tu as réellement retenu.
- **Missions du jour** : 3 tickets tirés chaque jour (vider le four, atteindre un combo, attraper un cookie doré, réviser des cartes mûres…).
- **Succès** : 135, dont des secrets. Chacun donne +1 % pour toujours, renforcé par les Chats.
- **Diplômes** (le prestige) : une fois assez de cookies cuits au total, tu peux être diplômé. Chaque diplôme donne +1 % pour toujours. Ils se dépensent dans l'arbre Héritage (9 bonus permanents). Tes cookies, bâtiments et améliorations repartent alors de zéro.

### Anti-triche (pour qu'Anki reste utile)

- **Toutes les réponses rapportent autant.** « À revoir » rapporte autant que « Facile » : mentir à l'algorithme ne paie jamais. Le moteur ne reçoit même pas la note.
- Même carte revue le même jour : 50 %, puis 20 % (ça couvre aussi l'annulation suivie d'une nouvelle réponse).
- Réponse en moins de 0,8 s : 20 %, et elle ne fait pas monter le combo.
- Au-delà de 50 nouvelles cartes par jour : 25 % pour chacune. Mode aperçu : 25 %.

Les seuils se règlent dans la config de l'add-on.

## Soutenir le projet

Cookie Recall est gratuit et le restera. Si tu l'aimes :
- ⭐ **Note-le sur AnkiWeb** (aussi possible depuis l'onglet *Statistiques* de la boulangerie).
- ☕ **[Offre-moi un café sur Ko-fi](https://ko-fi.com/ankinovia)**.
- 🐞 **[Signale un bug ou propose une idée](https://github.com/Hypernoviaa/cookie-recall/issues)**.

## Réglages

Dans la boulangerie (onglet *Statistiques*) ou via *Outils → Modules → Cookie Recall → Config* : langue, thème Cookie Recall, sons, compteur pendant les révisions, position du compteur, animations réduites, boulangerie repliée. Le menu *Outils* propose aussi « Cookie Recall : ouvrir la boulangerie » et « Cookie Recall : remettre à zéro… ».

## Structure du code

```
cookierecall/
  __init__.py      charge l'intégration seulement dans Anki
  game.py          moteur de jeu en Python pur (aucune dépendance à Anki)
  content.py       bâtiments, améliorations, succès, Héritage, missions
  integration.py   hooks Anki, sauvegarde, pont pycmd
  theme.py         thème Cookie Recall pour tout Anki (Qt + pages web + pages Svelte)
  i18n.py          traductions anglaises du contenu et des messages Python
  web/cookierecall.js   interface (HUD, boulangerie, bandeau) dans un Shadow DOM fermé
  web/strings.js   textes de l'interface, français et anglais
  web/cookierecall.css  styles, thèmes clair et sombre, mouvements réduits respectés
  web/theme.css    règles du thème Cookie Recall pour les pages d'Anki
  web/img/         37 illustrations SVG « autocollants »
  web/fonts/       Fredoka (licence OFL), embarquée pour marcher hors ligne
tools/
  simulate.py      simulation d'équilibrage (50 / 200 / 500 révisions par jour sur un an)
  make_assets.py   génère les illustrations SVG
  render.py        rend une page HTML avec QtWebEngine (le même moteur qu'Anki)
tests/test_game.py tests unitaires du moteur
```

### Bonnes pratiques suivies

- Uniquement des hooks officiels (`aqt.gui_hooks`), aucun monkey-patching d'Anki.
- Chaque hook est protégé : une erreur de l'add-on ne bloque jamais les révisions (sinon Anki retirerait le hook).
- L'état est stocké avec `col.set_config` (quelques Ko, sans casser l'historique d'annulation), donc il se synchronise.
- Les assets sont exposés via `setWebExports`, sans CDN.
- L'interface est dans un Shadow DOM **fermé** : tes modèles de cartes ne peuvent pas la casser, et elle ne peut pas toucher tes cartes.
- Python est la seule source de vérité. L'interface envoie des intentions (`pycmd`) et le moteur valide chaque achat. Le jeton d'un cookie doré ne sert qu'une fois.
- Le comptage des cartes mûres tourne en arrière-plan (`QueryOp`).
- Le thème passe par les jetons de couleur d'Anki : une seule palette alimente les fenêtres Qt (via `style_did_init`) et toutes les pages web (`webview_will_set_content`, `webview_did_inject_style_into_page`). Aucun script inline, pour respecter la politique de sécurité (CSP) de l'éditeur.

### Tests

```
python3 -m unittest tests.test_game     # 19 tests du moteur
python3 tools/simulate.py               # courbes d'équilibrage
```

L'add-on a aussi été joué dans un vrai Anki 26.9.3 lancé hors écran. Un add-on de test a révisé des cartes, acheté via le pont, cliqué un cookie doré, vidé le four et basculé en thème sombre, en prenant des captures à chaque étape.

### Équilibrage (simulation, joueur qui achète au mieux)

| Révisions/jour | 1re Usine | 1er Temple | 1er diplôme | Dernier bâtiment |
|---|---|---|---|---|
| 50 | jour 7 | jour 24 | jour ~124 | > 1 an |
| 200 | jour 3 | jour 11 | jour ~43 | jour ~364 |
| 500 | jour 2 | jour 5 | jour ~23 | jour ~136 |

## Empaquetage

```
cd cookierecall && zip -r ../cookierecall.ankiaddon . -x "__pycache__/*" "meta.json"
```
