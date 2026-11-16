# Rapport de présentation — AGRO-DATA

| | |
|---|---|
| **Projet** | AGRO-DATA — service numérique de surveillance de la pourriture brune du cacaoyer |
| **Cours** | GSA 712 / GSI 712 — organisation d'équipe et gestion de projet Scrum |
| **Équipe** | 6 membres : MEKONTSO Olivier Steve (SM), MESSANGA MESSANGA Mike (PO), NKWANE Mourad, NTYAM Angue, NEGOUE Patrick, NTEINTIE Mounpain |
| **Livraison** | Sprint 4 — tag annoté `v4-partiel`, commit `fbe7a20` |
| **Présentation** | 16/11/2026, 10 h 30 |
| **Rédacteur** | MEKONTSO Olivier Steve (Scrum Master) |
| **Dépôt** | <https://github.com/stevetelecom/agro-data> |
| **Kanban public** | <https://github.com/users/stevetelecom/projects/2> |

> **Les cinq messages à retenir pour l'oral**
>
> 1. **Un problème réel** : la pourriture brune détruit jusqu'à 80 % d'une
>    récolte à Ambam, et les acheteurs urbains décident sans visibilité.
> 2. **Une réponse DaaS** : des mesures microclimatiques transformées en indice
>    de risque, en alertes et en courbe de prix, vendues sous abonnement.
> 3. **Une organisation Scrum complète** : rôles, backlog priorisé, 24 issues,
>    3 milestones, Kanban public, rituels, DoR/DoD, CI à 4 jobs.
> 4. **Un calendrier tenu dans ses jalons, pas dans sa répartition** : les dates
>    du cahier des charges n'ont pas été décalées, mais l'essentiel de l'effort
>    a été produit du 10 au 12/11. Ce point est assumé et documenté.
> 5. **Une livraison partielle et honnête** : `v4-partiel` annonce dans son
>    message ce qui est livré et ce qui ne l'est pas ; aucune promesse au-delà
>    de ce qui tourne.

## Sommaire

1. [Description du projet](#1-description-du-projet)
2. [Ce que fait réellement le prototype](#2-ce-que-fait-réellement-le-prototype)
3. [Le lien avec le cours GSA 712 / GSI 712](#3-le-lien-avec-le-cours-gsa-712--gsi-712)
4. [Comment les tâches ont été organisées](#4-comment-les-tâches-ont-été-organisées)
5. [Comment les délais ont été respectés](#5-comment-les-délais-ont-été-respectés)
6. [Résultats chiffrés](#6-résultats-chiffrés)
7. [Limites et réserves](#7-limites-et-réserves)
8. [Bilan pédagogique](#8-bilan-pédagogique)
9. [Annexes](#annexes)

---

## 1. Description du projet

### 1.1 Le problème

Ambam, dans la région du Sud du Cameroun, est le deuxième bassin de production
cacaoyère du pays. La pourriture brune, causée par *Phytophthora megakarya*,
prospère dès que l'humidité relative dépasse **85 %** : une plantation peut
passer de saine à fortement infestée en moins de sept jours, et une cabosse
touchée est perdue à 100 %.

Trois conséquences se cumulent :

- le producteur ne voit pas venir le risque et traite trop tard, ou traite
  toute la parcelle au lieu des seules zones à risque ;
- l'acheteur urbain (Ebolowa, Yaoundé) envoie ses camions sans savoir quel
  volume sain est réellement disponible ;
- personne ne dispose d'un prix objectivé par l'état sanitaire de la zone.

C'est une **asymétrie d'information** entre la production rurale et le marché
urbain.

### 1.2 La réponse : un service Data-as-a-Service

AGRO-DATA mesure en continu les conditions microclimatiques sous la canopée,
en déduit un **indice d'infestation**, déclenche des **alertes** au-delà de
48 h d'humidité critique, et publie une **courbe de prix prévisionnelle**
ajustée par le risque. L'acheteur y accède par un dashboard web et par une API
REST, sous abonnement sécurisé.

| Question du client | Réponse du service |
|---|---|
| Le cacao est-il encore sain ? | Indice d'infestation 0-100, niveau et alertes par parcelle |
| Quel volume puis-je acheter ? | Volume sain estimé en kg et part du volume de référence |
| À quel prix ? | Prix indicatif ajusté à partir de 1 050 FCFA/kg (formule v1) |
| Puis-je intégrer ces données ? | API REST documentée (OpenAPI) et export des mesures |

### 1.3 Utilisateurs

| Utilisateur | Besoin | Interface |
|---|---|---|
| Producteur d'Ambam | Savoir quand et où pulvériser | Vue « Lecture terrain » sans texte, feux d'alerte, gros boutons |
| Acheteur / exportateur | Décider d'un déplacement et d'un prix | Dashboard KPIs, graphiques, journal des prix |
| Coopérative | Protéger et suivre les boîtiers | Gestion des appareils et des parcelles |
| Intégrateur | Brancher ses propres outils | API REST + JWT |

### 1.4 Périmètre du prototype

**Dans le périmètre** : acquisition simulée ou réelle, tampon local
Store-and-Forward, API d'ingestion, pipeline de nettoyage, Data Lake, indice
d'infestation, prix v1, diagnostic IA de démonstration, dashboard sécurisé avec
CRUD, API REST documentée.

**Hors périmètre** : déploiement massif de boîtiers, entraînement de l'IA sur
des milliers d'images terrain, paiement en ligne, application mobile native.

### 1.5 Trois blocs, trois incréments

```
[ BLOC C ] ──── message JSON ────► [ BLOC A ] ──── KPIs / prix ────► [ BLOC B ]
Acquisition                         Traitement                         Restitution
DHT22, caméra, MicroSD              nettoyage, IA, indice, prix        dashboard, API acheteurs
simulateur, firmware                Data Lake, SQLite                  login, CRUD, toasts
```

| Bloc | Rôle | Modules | Issues |
|---|---|---|---|
| **C** | Capturer et ne rien perdre | simulateur, tampon, firmware ESP32-CAM | #6, #12, #19 |
| **A** | Nettoyer, sécuriser, calculer | ingestion, pipeline, chiffrement, indice, prix, IA, CRUD | #5, #10, #11, #13, #14, #18 |
| **B** | Restituer aux acheteurs | design system, login, KPIs, grilles, graphiques, toasts | #7, #8, #15, #16, #21, #22 |
| **Transverse** | Piloter et prouver | dépôt, CI, contrat, Kanban, recette, rituels | #1, #2, #3, #4, #9, #17, #20, #23, #24 |

Le plan de codage applique une **tranche verticale** : le Sprint 2 pose les
fondations des trois blocs, le Sprint 3 approfondit le bloc A, le Sprint 4
termine le bloc B et intègre le bloc C. Ce découpage évite de livrer trois
morceaux qui ne se parlent pas.

---

## 2. Ce que fait réellement le prototype

### 2.1 Le parcours de démonstration, en 10 étapes

| # | Étape | État | Preuve |
|---|---|---|---|
| 1 | Un message JSON part du simulateur et arrive dans le Data Lake | ✅ | `test_e2e.py`, 48 fichiers bruts |
| 2 | Une coupure réseau ne perd aucune mesure | ✅ | 24 h hors ligne, 24 renvoyées, 0 doublon |
| 3 | 48 h au-dessus de 85 % déclenchent une alerte | ✅ | `test_kpis.py`, indice 69-70 |
| 4 | La courbe de prix répond | ✅ | `GET /api/v1/prices/forecast`, v1, `is_demo` |
| 5 | L'acheteur se connecte au dashboard | ✅ | `index.html` + `auth.js` |
| 6 | Créer/supprimer une parcelle affiche un toast | ✅ | `modals.js` + `toast.js` |
| 7 | Le diagnostic IA retourne un drapeau et un score | 🟡 | stub déterministe, `is_demo: true` |
| 8 | La vue producteur « zéro-texte » est utilisable | ✅ | onglet « Lecture terrain » |
| 9 | Les mêmes données sortent par `curl` avec un jeton | ✅ | JWT sur `/kpis` et `/prices/forecast` |
| 10 | Une mesure invalide est rejetée | ✅ | `422` sur `device_id` malveillant |

**10 étapes sur 10** sont rejouées par `scripts/demo_e2e.py` ; la seule réserve
est matérielle (firmware non flashé) et la seule réserve fonctionnelle est l'IA
non entraînée.

### 2.2 Architecture technique

```
┌──────────────────┐   HTTPS/JSON   ┌──────────────────────────────┐   REST/JWT   ┌──────────────────┐
│ Boîtier ESP32-CAM│ ─────────────► │ API FastAPI + Uvicorn        │ ◄─────────── │ Dashboard web    │
│ ou simulateur    │                │  Pydantic : validation       │              │  HTML/CSS/JS     │
│ DHT22, caméra,   │                │  pipeline : nettoyage        │              │  Chart.js        │
│ MicroSD (tampon) │                │  AES-256-GCM, JWT, rôles     │              │  jQWidgets       │
└──────────────────┘                │  SQLite (SQLAlchemy)         │              │  toasts, modals  │
                                    │  Data Lake : brut + traité   │              └──────────────────┘
                                    │  indice, prix v1, IA démo    │
                                    └──────────────────────────────┘
```

| Couche | Technologie | Justification |
|---|---|---|
| API | FastAPI + Uvicorn | validation intégrée, OpenAPI automatique |
| Validation | Pydantic | rejet des entrées invalides avant la base |
| Base | SQLite via SQLAlchemy | prototype simple, requêtes paramétrées |
| Data Lake | fichiers JSON bruts + tables traitées | vérifiable à l'œil, sans infrastructure |
| Sécurité | Argon2/bcrypt, JWT, AES-256-GCM | conformité Loi n° 2010/012 |
| Frontend | HTML/CSS/JS, Chart.js, jQWidgets | tableaux et graphiques sans framework lourd |
| Tests | pytest, `node:test`, `pip-audit` | 106 tests backend + 18 tests JS |
| CI | GitHub Actions, 4 jobs | backend, dashboard, démo E2E, audit des dépendances |

### 2.3 Le contrat d'échange avant le code

Le contrat JSON (`docs/CONTRAT_JSON.md`) est écrit dès le Sprint 2 (version
1.0 provisoire, faute de validation du PO), puis versionné jusqu'à la **1.3**.
Il sert de frontière entre les trois blocs. Il définit les mesures
entrantes, les modèles de lecture du dashboard (§4.4 à §4.8), les règles métier
(seuil « 48 h ou plus », `humidity_delta_7d` sur 7 jours, volume sain incluant
les parcelles sans mesure) et les comptes hors ligne.

Un test vérifie que le document de contrat reste aligné sur le schéma Pydantic :
les trois blocs ne peuvent plus diverger silencieusement.

### 2.4 Lancer la démonstration

```bash
# 1. API
cd backend && ../.venv/bin/python -m uvicorn app.main:app --port 8000

# 2. Dashboard
.venv/bin/python -m http.server 8080 --directory dashboard

# 3. Scénario complet (10 vérifications)
.venv/bin/python scripts/demo_e2e.py
```

Comptes : `acheteur@ebolowa.cm` / `demo1234` (admin) et
`lecteur@ebolowa.cm` / `demo1234` (lecture seule).

---

## 3. Le lien avec le cours GSA 712 / GSI 712

### 3.1 L'objectif pédagogique du cahier des charges

Le cahier des charges (§3.3) formule ainsi l'objectif pédagogique :

> « Montrer la construction et le fonctionnement d'une équipe Scrum : rôles,
> répartition des tâches, gouvernance, communication, outils collaboratifs,
> progression visible sprint après sprint. »

Le projet n'est donc pas seulement jugé sur le code : il est jugé sur la
**capacité de l'équipe à se doter d'un cadre de travail vérifiable**. C'est
pourquoi chaque affirmation de ce rapport renvoie à un artefact consultable.

### 3.2 Grille de lecture : exigence du cours → application → preuve

| Exigence du cours | Application sur AGRO-DATA | Preuve |
|---|---|---|
| **Rôles explicites** | PO, SM, 4 développeurs ; enseignant spectateur | `RITUELS_SCRUM.md` §1, CDC §15 |
| **Répartition des tâches** | 24 issues, un assigné par issue, labels `bloc-*`, `MOD-*`, `must/should/could` | GitHub Issues, `PRODUCT_BACKLOG.md` |
| **Gouvernance** | le PO arbitre les priorités, le SM fusionne après revue, le contrat se change à deux | `RITUELS_SCRUM.md` §5 |
| **Communication** | daily asynchrone, revues, rétrospectives, comptes-rendus écrits | `SPRINT_*_REVIEW.md`, `RETROSPECTIVES.md` |
| **Outils collaboratifs** | GitHub Issues, Projects, Actions, Pull Requests, Git | dépôt public, Kanban public, CI |
| **Progression visible** | 3 milestones, 3 tags, Kanban à 3 colonnes, indicateurs par sprint | Project #2, tags `v2`/`v3`/`v4-partiel` |
| **Rituels** | planning, daily, raffinement, review, rétrospective | `RITUELS_SCRUM.md` §3 |
| **Amélioration continue** | actions R2-x, R3-x, R4-x décidées puis suivies | `RETROSPECTIVES.md` §Suivi |

### 3.3 L'équipe et ses rôles

| Membre | Rôle Scrum | Responsabilité principale |
|---|---|---|
| MESSANGA MESSANGA Mike (`@oppoytron-eng`) | Product Owner | valeur, ordre du backlog, validation des critères |
| MEKONTSO Olivier Steve (`@stevetelecom`) | Scrum Master + développeur | dépôt, CI, Kanban, rituels, backend, intégration |
| NKWANE Mourad (`@mourad055`) | Développeur | ingestion, pipeline, sécurité, CRUD |
| NTYAM Angue | Développeur | design system, maquettes, accessibilité |
| NEGOUE Patrick (`@NTPbreak`) | Développeur | login, grilles, graphiques, modals, toasts |
| NTEINTIE Mounpain (`@73EGA`) | Développeur | simulateur, tampon, firmware |

Deux choix sont assumés et documentés :

- **le SM est aussi développeur** : avec six personnes dont deux profils design
  et un profil intermédiaire, le cumul était nécessaire pour livrer le backend ;
- **l'enseignant est spectateur** : accès `write`, aucune issue assignée, aucune
  intervention dans le backlog ou les revues.

---

## 4. Comment les tâches ont été organisées

### 4.1 Du besoin au ticket : le Product Backlog

Le Product Backlog contient **15 user stories** (PB-01 à PB-15), dérivées des
besoins fonctionnels du cahier des charges. Chacune porte un bloc, une priorité
MoSCoW et une estimation S/M/L.

| Priorité | Nombre | Exemples |
|---|---|---|
| **Must** | 8 | mesure horaire, stockage local, chiffrement, IA, indice, dashboard |
| **Should** | 5 | boîtier IP66, prix prédictif, API REST, abonnement |
| **Could** | 2 | alertes de pulvérisation ciblée, parcours en moins de 60 s |

Le PO ordonne le backlog ; le SM le découpe en issues exécutables. Une issue
n'entre dans un sprint que si elle respecte la **Definition of Ready** : titre
`[MOD-Xn]`, critère d'acceptation vérifiable, estimation, assigné unique,
milestone, dépendances identifiées, section de contrat écrite si nécessaire.

### 4.2 Le découpage réel : 24 issues, 3 milestones

| Milestone | Issues | Terminées | Partielles | Non commencées |
|---|---|---|---|---|
| Sprint 2 — Fondations (28/10) | 9 | 3 | 4 | 2 |
| Sprint 3 — Traitement (04/11) | 8 | 0 | 3 | 5 |
| Sprint 4 — Restitution (11/11) | 7 | 4 | 3 | 0 |
| **Total** | **24** | **21 fermées** | — | — |

Chaque issue porte :

- un **titre préfixé** par le module (`[MOD-A1]`, `[MOD-B2]`…) ;
- des **labels** de bloc (`bloc-a/b/c`), de priorité (`must/should/could`),
  de sprint (`sprint-2/3/4`) et de type (`bug`, `documentation`, `enhancement`) ;
- **un seul assigné** et une estimation ;
- un **critère d'acceptation** et, en commentaire de clôture, une **preuve**
  (commit, test, capture).

### 4.3 Le cycle de vie d'une tâche

```
Besoin CDC
   │
   ▼
User story (PB-xx) ──► Issue GitHub (MOD-xn) ──► Definition of Ready
   │                                              │
   │                                              ▼
   │                                   Branche feature/<module>-<prénom>
   │                                              │
   │                                              ▼
   │                                   Code + tests (cas normal + invalide)
   │                                              │
   │                                              ▼
   │                                   CI verte sur la branche
   │                                              │
   │                                              ▼
   │                                   Pull Request relue par un autre membre
   │                                              │
   │                                              ▼
   │                                   Fusion dans main ──► tag de sprint
   │                                              │
   │                                              ▼
   │                                   Issue commentée avec preuve + fermée
   │                                              │
   │                                              ▼
   │                                   Carte Kanban en « Terminé »
   │                                              │
   │                                              ▼
   └──────────────────────────────► Definition of Done (8 points)
```

La **Definition of Done** exige : code commenté, tests verts en local et en CI,
cas normal et cas invalide couverts, PR relue, fusion dans `main`, issue
commentée avec preuve, carte Kanban à jour, et validation du PO pour toute
fonctionnalité visible.

### 4.4 Les rituels

| Rituel | Quand | Durée | Sortie |
|---|---|---|---|
| Sprint Planning | lundi de la 1re semaine | 45 min | objectif, Sprint Backlog, cartes estimées |
| Daily Scrum | chaque jour, asynchrone | 10 min | fait / à faire / blocage |
| Raffinement | milieu de sprint | 30 min | critères d'acceptation clarifiés |
| Sprint Review | jour de livraison | 30 min | démonstration, acceptation ou refus |
| Rétrospective | après la Review | 30 min | 2 actions maximum, suivies au sprint suivant |

Les comptes-rendus sont écrits et versionnés : `SPRINT_2_REVIEW.md`,
`SPRINT_3_REVIEW.md`, `SPRINT_4_REVIEW.md`, `RETROSPECTIVES.md`. Ils listent
aussi ce qui n'a **pas** été fait — c'est une règle explicite du document de
rituels.

### 4.5 Les outils et la gouvernance

| Besoin | Outil | Convention |
|---|---|---|
| Tickets | GitHub Issues | titre `[MOD-Xn]`, labels, un assigné |
| Planning | GitHub Milestones | un milestone par sprint |
| Suivi visuel | GitHub Projects | 3 colonnes : À faire, En cours, Terminé |
| Code | Git + GitHub | une branche par module, une PR par lot |
| CI | GitHub Actions | 4 jobs sur chaque branche poussée |
| Documentation | `docs/` | Markdown, une section par sujet |

Règles de décision : le PO arbitre les priorités, le SM arbitre les conflits de
capacité et fusionne après revue, un choix technique interne appartient au
développeur du module, un changement de contrat se fait à deux (PO + SM) dans
le même commit que le schéma.

### 4.6 Git et intégration continue

- Branche `main` toujours fonctionnelle ; branches `feature/<module>-<prénom>`.
- Messages au format `type(portée): description` (`feat`, `fix`, `docs`, `test`,
  `refactor`, `chore`, `ci`).
- `Closes #N` ferme l'issue et déplace la carte ; `Refs #N` relie sans fermer.
- La CI vérifie **quatre choses** à chaque push : les 106 tests backend, les
  18 tests JS, la démonstration de bout en bout sur une base neuve, et l'absence
  de vulnérabilité connue dans les dépendances épinglées (`pip-audit`).

Dernier run vert : `43826585768` sur `fbe7a20`, 4 jobs sur 4.

---

## 5. Comment les délais ont été respectés

### 5.1 Le calendrier de référence (CDC §16)

| Sprint | Échéance | Objectif | Livrable attendu |
|---|---|---|---|
| 2 | **28/10/2026** | Fondations : dépôt, contrat JSON, simulateur, squelette API, maquettes | version 2 du dossier + premier code |
| 3 | **04/11/2026** | Traitement : pipeline, indice, prototype IA, authentification | version 3 du dossier + backend fonctionnel |
| 4 | **11/11/2026** | Restitution : dashboard, API REST, démonstration | livrable final + prototype complet |

### 5.2 Prévu contre réel

| Sprint | Échéance CDC | Revue tenue | Tag | Commit | Bilan | Verdict |
|---|---|---|---|---|---|---|
| 2 | 28/10 | **10/11** | `v2` | `901f4ab` | 3 terminés, 4 partiels, 2 non commencés | Partiel, revue tardive |
| 3 | 04/11 | **10/11** | `v3` | `add13d4` | 0 terminé, 3 partiels, 5 non commencés | Partiel, revue tardive, PR #25 bloquante |
| 4 | 11/11 | **11/11** | `v4-partiel` | `fbe7a20` | 4 terminés, 3 partiels, 0 non commencé | Livré avec réserves, dans les délais |

### 5.3 Ce qui est tenu, ce qui ne l'est pas

**Ce qui est tenu :**

- la **date de livraison finale** du cahier des charges (11/11) : la revue du
  Sprint 4 s'est tenue ce jour-là, avec une démonstration de bout en bout ;
- les **trois jalons** existent et sont **étiquetés** (`v2`, `v3`, `v4-partiel`) ;
- **aucune date n'a été repoussée** : un incrément incomplet est présenté tel
  quel, avec la liste de ce qui manque, plutôt que reporté en silence ;
- le **périmètre Must** est couvert et testé, à l'exception de l'IA entraînée,
  assumée comme réserve ;
- la **démonstration est reproductible** en trois commandes, sur une base neuve,
  et rejouée automatiquement par la CI.

**Ce qui n'est pas tenu :**

- les Sprints 2 et 3 n'ont pas été **revus à leur date** : les deux revues ont
  été tenues le 10/11, et les tags `v2`/`v3` ont été posés sur des commits
  datés du 10/11 ;
- l'effort est **concentré sur la fin** : 56 des 59 commits de `main` sont
  datés du 10, 11 ou 12/11 (39 le 10/11, 14 le 11/11, 3 le 12/11), contre
  3 commits en octobre ;
- **52 des 59 commits** sont du SM, dont une partie du bloc C reprise faute de
  livraison : le critère §17.8 (historique montrant le travail de chacun) est
  partiel ;
- le **PO n'a validé aucun artefact** depuis le Sprint 2 : #14, #17 et #20
  restent ouvertes.

### 5.4 Les leviers qui ont évité le report

1. **Le contrat JSON figé avant le code.** Les trois blocs ont pu avancer en
   parallèle sans se découvrir au moment de l'intégration.
2. **La priorisation MoSCoW.** En cas de retard, on sacrifie un `Could`, jamais
   un `Must`. Le prix v2 (non spécifié) et l'IA entraînée (données absentes)
   ont été explicitement sortis du périmètre plutôt que bâclés.
3. **Un ticket = une preuve.** Chaque issue fermée renvoie à un test ou à un
   commit. On ne coche pas une case sans preuve exécutable (action R4-3).
4. **La CI sur toutes les branches.** Elle a servi de filet lors des fusions
   tardives du dashboard et de la PR #25.
5. **Des tags partiels plutôt qu'un faux `v-final`.** Le nom `v-final` a été
   refusé et supprimé ; `v4-partiel` décrit exactement l'état livré.
6. **Un plan B préparé.** Démonstration locale, simulateur, maquette de secours :
   rien n'a été improvisé le jour de la revue.
7. **Le Kanban remis à jour la veille.** 21 issues fermées avec preuves, pour
   que le tableau reflète le code et non l'inverse.

### 5.5 Ce que l'équipe ferait différemment

Les rétrospectives ont produit des actions datées, dont plusieurs sont déjà
appliquées :

| Action | Origine | Statut |
|---|---|---|
| R2-1 : taguer chaque sprint | S2 | ✅ fait, en retard |
| R3-1 : trancher la PR #25 | S3 | ✅ fusionnée le 10/11 à 13 h 16 |
| R4-1 : tag `v4-partiel` annoté | S4 | ✅ recréé le 12/11 après audit |
| R4-3 : aucune case cochée sans preuve | S4 | ✅ appliqué |
| R4-6 : vérifier les branches distantes avant revue | S4 | ✅ appliqué (dashboard récupéré) |
| R4-5 : tickets de 2 jours maximum | S4 | ⏳ prochaine itération |
| R4-7 : PR ouverte 48 h avant l'échéance | S4 | ⏳ prochaine itération |
| R4-8 : point hebdomadaire écrit, escalade si silence | S5 | ⏳ prochaine itération |

La leçon centrale est simple : **le calendrier a été tenu dans ses jalons, pas
dans sa répartition**. La prochaine itération doit lisser l'effort, imposer des
PR ouvertes 48 h avant l'échéance et escalader plus tôt les blocs silencieux.

---

## 6. Résultats chiffrés

| Indicateur | Valeur |
|---|---|
| Issues créées / fermées | 24 / 21 |
| Sprints étiquetés | 3 (`v2`, `v3`, `v4-partiel`) |
| Commits sur `main` | 59 |
| Auteurs de commits | 4 (SM 52, NTPbreak 3, Mourad 2, 73EGA 2) |
| Pull requests fusionnées | 1 (#25) + 1 branche fusionnée sans PR |
| Fichiers versionnés | 141 |
| Code | ≈ 8 400 lignes (backend 4 006, dashboard 2 823, simulateur 912, IA 262, firmware 243, scripts 172) |
| Documentation | ≈ 3 500 lignes (dont ce rapport) |
| Routes API | 21 |
| Tests backend | 106 |
| Tests JavaScript | 18 |
| Jobs CI | 4, tous verts sur `fbe7a20` |
| Démonstration E2E | 10 étapes sur 10 |
| Critères §17 | 6 ✅ / 2 🟡 |
| Vues du dashboard | 7 (tableau de bord + 6 écrans) |
| Cartes d'indicateurs | 7 |

---

## 7. Limites et réserves

| Réserve | Réalité | Conséquence |
|---|---|---|
| **IA non entraînée** | `ai/dataset` vide, `ai/infer.py` est un stub SHA-256 déterministe, `is_demo: true` | critère §17.4 partiel : drapeau et score retournés, mais non appris |
| **Firmware non compilé ni flashé** | `firmware/agro_node/agro_node.ino` écrit (243 lignes), aucune recette matérielle | critère §17.1 couvert par le simulateur, pas par le boîtier |
| **Prix v2 absent** | formule v1 seule (`adjusted = reference × (1 + 0,15 × indice/100)`), `is_demo: true` | fonctionnalité non spécifiée par le PO, sortie du périmètre |
| **Validation PO absente** | PV signé par le SM mandaté le 11/11 ; #14, #17, #20 ouvertes | livraison « acceptée avec réserves », pas validée formellement |
| **Historique Git partiel** | 52/59 commits du SM, bloc C repris | critère §17.8 partiel, assumé et documenté |
| **Branche `main` non protégée** | pas de protection de branche, pas de `LICENSE` | risque de gouvernance, sans impact sur la démo |

Ces réserves ne sont pas cachées : elles figurent dans le message du tag
`v4-partiel`, dans le PV de recette (§6 et §8), dans `SPRINT_4_REVIEW.md` §9 et
dans `AUDIT.md` §10.

---

## 8. Bilan pédagogique

### 8.1 Ce que l'équipe a appris sur Scrum

- **Un backlog vivant ne suffit pas** : il faut que le Kanban dise la vérité.
  Le tableau a menti jusqu'au 10/11, avec des issues terminées encore ouvertes.
  Le pilotage s'est fait sur le code, pas sur le board — c'est une erreur.
- **La Definition of Done protège** : quand elle n'est pas appliquée (travail
  direct sur `main`), l'historique ne raconte plus le travail réel.
- **Le PO est un rôle, pas un titre** : son absence a bloqué le contrat, les
  critères et les données. L'équipe a appris à consigner formellement cette
  absence plutôt qu'à l'ignorer.
- **Un incrément partiel assumé vaut mieux qu'un report silencieux** : les tags
  `v2`, `v3`, `v4-partiel` racontent une progression honnête.
- **L'intégration se prépare** : la PR #25 a bloqué quatre tickets pendant deux
  sprints ; une branche poussée sans PR n'est pas une livraison.

### 8.2 Ce que le cours peut retenir

AGRO-DATA montre qu'une équipe de six personnes, sans compétence IA/IoT
préalable, peut livrer un prototype DaaS fonctionnel en trois semaines **si**
elle :

1. fige un contrat d'échange tôt ;
2. découpe en tranches verticales livrables ;
3. automatise les tests et la CI ;
4. priorise sans pitié ;
5. documente ses écarts au lieu de les masquer.

Le projet montre aussi les **limites** de l'exercice : un PO indisponible, un
membre qui ne pousse pas, et une fin de projet comprimée ne se corrigent pas
par la bonne volonté du SM. Ils se corrigent par des règles : PR obligatoire,
point hebdomadaire écrit, escalade au PO, tickets de deux jours maximum.

### 8.3 Conclusion

AGRO-DATA est un **prototype fonctionnel de bout en bout et honnêtement
partiel**.
La chaîne acquisition → Data Lake → IA → KPIs → prix → dashboard fonctionne de
bout en bout, elle est testée (106 + 18 tests), rejouée par la CI et
démontrable en trois commandes.

Ce qui manque est nommé : IA entraînée, firmware flashé, prix v2, validation
formelle du PO. Ce qui est livré est prouvé. C'est cette distinction — entre
**ce qu'on affirme** et **ce qu'on exécute** — que le projet cherche à
démontrer, au-delà du code.

---

## Annexes

### A. Preuves vérifiables

| Preuve | Où |
|---|---|
| Dépôt et historique | <https://github.com/stevetelecom/agro-data> |
| Kanban public | <https://github.com/users/stevetelecom/projects/2> |
| CI verte | run `43826585768` sur `fbe7a20` |
| Tag de livraison | `git show v4-partiel` |
| Démonstration | `.venv/bin/python scripts/demo_e2e.py` |
| Tests backend | `cd backend && ../.venv/bin/python -m pytest -q` |
| Tests JS | `node --test dashboard/js/*.test.js` |

### B. Documents de référence

| Document | Contenu |
|---|---|
| `docs/CAHIER_DES_CHARGES.md` | contexte, besoins, planning, critères §17, risques |
| `docs/PLAN_DE_CODAGE.md` | architecture, pile technique, workflow Git, plan par sprint |
| `docs/PRODUCT_BACKLOG.md` | PB-01 à PB-15, priorités, estimations |
| `docs/CONTRAT_JSON.md` | contrat d'échange v1.3 |
| `docs/livrables/RITUELS_SCRUM.md` | rôles, artefacts, rituels, DoR/DoD |
| `docs/livrables/SPRINT_2_REVIEW.md` | bilan du Sprint 2 |
| `docs/livrables/SPRINT_3_REVIEW.md` | bilan du Sprint 3 |
| `docs/livrables/SPRINT_4_REVIEW.md` | bilan du Sprint 4 |
| `docs/livrables/RETROSPECTIVES.md` | rétrospectives et suivi des actions |
| `docs/livrables/CRITERES_ACCEPTATION.md` | preuves des 8 critères §17 |
| `docs/livrables/PV_RECETTE.md` | procès-verbal de recette |
| `docs/livrables/AUDIT.md` | audit A1-A22 et correctifs §10 |

### C. Historique du document

| Version | Date | Auteur | Changement |
|---|---|---|---|
| 1.0 | 16/11/2026 | MEKONTSO Olivier Steve (SM) | Rédaction pour la présentation du 16/11/2026 |
