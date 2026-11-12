# Rituels Scrum — AGRO-DATA

**Version** : 1.0
**Date** : 10 novembre 2026
**Auteur** : MEKONTSO Olivier Steve (Scrum Master)
**Références** : cahier des charges §15 et §16, plan de codage §3 et §5, issue #24

Ce document décrit comment l'équipe applique Scrum sur AGRO-DATA : les rôles,
les artefacts, les rituels et leurs dates, les outils, et les deux définitions
qui engagent l'équipe (Definition of Ready, Definition of Done).

Il sert de preuve de suivi pour l'enseignant (`@Metili`, simple spectateur) :
tout ce qui est raconté ici est vérifiable dans les issues, le Kanban et
l'historique Git.

---

## 1. Rôles

| Rôle Scrum | Membre | Responsabilités sur AGRO-DATA |
|---|---|---|
| Product Owner | MESSANGA MESSANGA Mike (`@oppoytron-eng`) | porte la valeur, ordonne le Product Backlog, valide les critères d'acceptation, fournit les jeux de données et le jeu d'images |
| Scrum Master | MEKONTSO Olivier Steve (`@stevetelecom`) | dépôt, CI, Kanban, animation des rituels, levée des blocages, revues de code, documentation |
| Développeurs | NKWANE Mourad (`@mourad055`), NTYAM Angue, NEGOUE Patrick (`@NTPbreak`), NTEINTIE Mounpain (`@73EGA`), MEKONTSO Olivier Steve | réalisent les tickets, testent, relisent les PR |

L'enseignant `@Metili` est **spectateur** : il a un accès `write` au dépôt et
au Project, aucune issue ne lui est assignée, il n'intervient ni dans le
backlog ni dans les revues.

Le Scrum Master est aussi développeur (MOD-A4, MOD-A5, MOD-B2). Ce cumul est
assumé et documenté : il est la conséquence d'une équipe de six personnes dont
deux profils design et un profil développement intermédiaire.

---

## 2. Artefacts

| Artefact | Support | Règle de tenue |
|---|---|---|
| Product Backlog | `docs/PRODUCT_BACKLOG.md` (PB-01 à PB-15) | ordonné par le PO, priorité Must / Should / Could, estimation S / M / L |
| Sprint Backlog | issues GitHub + milestone du sprint | une issue = une tâche, un seul assigné, une estimation |
| Incrément | branche `main` + tags `v2`, `v3`, `v4-partiel` | `main` reste fonctionnelle à tout moment |
| Tableau Kanban | GitHub Project `stevetelecom/projects/2` | colonnes **À faire**, **En cours**, **Terminé** ; une carte par issue |
| Contrat d'échange | `docs/CONTRAT_JSON.md` | référence unique, toute évolution se fait dans le même commit que le schéma |

Le Kanban est public :
<https://github.com/users/stevetelecom/projects/2>

---

## 3. Rituels

| Rituel | Quand | Durée | Qui | Sortie attendue |
|---|---|---|---|---|
| Sprint Planning | lundi de la première semaine du sprint | 45 min | tous + PO | objectif de sprint, Sprint Backlog, cartes créées et estimées |
| Daily Scrum | chaque jour, en asynchrone sur le fil d'équipe | 10 min | développeurs | trois réponses : fait hier, fait aujourd'hui, blocage |
| Raffinement | milieu de sprint | 30 min | PO + développeurs | critères d'acceptation clarifiés, tickets prêts (voir §6) |
| Sprint Review | jour de livraison du sprint | 30 min | tous + PO + enseignant invité | démonstration, acceptation ou refus des incréments, compte-rendu |
| Rétrospective | après la Review | 30 min | équipe de développement + SM | deux actions d'amélioration maximum, suivies au sprint suivant |

### Cadence et dates

| Sprint | Début | Livraison | Objectif | Tag |
|---|---|---|---|---|
| Sprint 2 — Fondations | 22/10/2026 | **28/10/2026** | chaîne minimale simulateur → API → base, contrat JSON, maquettes | `v2` |
| Sprint 3 — Traitement | 29/10/2026 | **04/11/2026** | pipeline, chiffrement, indice, prototype IA, authentification | `v3` |
| Sprint 4 — Restitution | 05/11/2026 | **11/11/2026** | dashboard, API REST, démonstration de bout en bout | `v4-partiel` |

Les dates de livraison sont celles du cahier des charges §16. Elles **ne sont
pas décalées** : un incrément incomplet est présenté tel quel en Review, avec
la liste de ce qui manque, plutôt que reporté en silence.

### Format des comptes-rendus

Chaque Review et chaque Rétrospective produit un fichier dans
`docs/livrables/` :

- `SPRINT_<n>_REVIEW.md` : objectif, prévu, livré, non livré et raison,
  démonstration, décisions du PO, indicateurs ;
- `RETROSPECTIVES.md` : une section par sprint, avec les actions décidées et
  leur statut au sprint suivant.

Un compte-rendu est **honnête** : il liste aussi ce qui n'a pas été fait. Un
sprint n'est jamais déclaré terminé par le Scrum Master seul, c'est le PO qui
accepte l'incrément.

---

## 4. Outils

| Besoin | Outil | Convention |
|---|---|---|
| Tickets | GitHub Issues | titre `[MOD-Xn] …`, labels `module:*`, `priorite:*`, `type:*` |
| Planning | GitHub Milestones | un milestone par sprint, même nom que le sprint |
| Suivi visuel | GitHub Projects (Kanban) | 3 colonnes, une carte = une issue |
| Code | Git + GitHub | une branche par module, une PR par lot cohérent |
| Intégration continue | GitHub Actions (`.github/workflows/ci.yml`) | tests sur **toutes** les branches poussées, plus `main` |
| Documentation | `docs/` | Markdown, une section par sujet, historique en bas de chaque doc |

### Conventions Git

- Une branche par module : `feature/<module>-<prénom>`.
- Messages au format `type(portée): description` — `feat`, `fix`, `docs`,
  `test`, `refactor`, `chore`, `ci`.
- Le mot-clé `Closes #N` dans le message ferme l'issue et déplace la carte en
  **Terminé** automatiquement ; `Refs #N` relie sans fermer.
- Aucune fusion directe dans `main` sans PR relue ; le Scrum Master valide.
- Tags annotés `v2`, `v3`, `v4-partiel` sur `main`.

---

## 5. Règles de décision

| Sujet | Décideur | Recours |
|---|---|---|
| Priorité d'un ticket | Product Owner | Scrum Master arbitre le conflit de capacité |
| Choix technique interne à un module | développeur du module | revue de code |
| Changement du contrat JSON | PO **et** SM, dans le même commit que le schéma | si le PO est indisponible, le SM fige une version provisoire, signalée « en attente de confirmation » |
| Fusion d'une PR | Scrum Master après revue | le PO valide le critère d'acceptation, pas la qualité du code |
| Report d'un ticket | PO | décision consignée en Review |

---

## 6. Definition of Ready

Un ticket peut entrer dans un sprint quand :

1. il a un titre `[MOD-Xn]`, une description et un critère d'acceptation vérifiable ;
2. il est estimé (S / M / L) et assigné à une seule personne ;
3. il est rattaché à un milestone ;
4. ses dépendances sont identifiées (contrat, route, table, maquette) ;
5. s'il touche l'échange de données, la section du contrat est écrite.

## 7. Definition of Done

Un ticket est **terminé** quand :

1. le code est commenté (en-tête de fichier, docstrings) et respecte le style du module ;
2. les tests automatisés passent en local **et** en CI ;
3. le cas normal **et** au moins un cas invalide sont couverts ;
4. la PR est relue par un autre membre ;
5. la fusion dans `main` est faite ;
6. l'issue est commentée avec la preuve (commit, test, capture) et fermée ;
7. la carte Kanban est en **Terminé** ;
8. le PO a validé le critère d'acceptation quand le ticket livre une fonctionnalité visible.

Les points 1 à 7 sont vérifiables par le Scrum Master ; le point 8 ne l'est
que par le Product Owner.

---

## 8. Historique

| Version | Date | Auteur | Changement |
|---|---|---|---|
| 1.0 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Formalisation des rôles, artefacts, rituels, outils, DoR et DoD (issue #24) |
