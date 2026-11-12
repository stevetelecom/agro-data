# Sprint 4 — Préparation et plan de démonstration

| | |
|---|---|
| **Sprint** | Sprint 4 — Restitution et intégration |
| **Début** | 05/11/2026 |
| **Livraison** | **11/11/2026** (cahier des charges §16) |
| **Revue prévue** | 11/11/2026, avec le PO |
| **Tag** | `v4-partiel` (nommé `v-final` à la planification) |
| **Auteur** | MEKONTSO Olivier Steve (SM), issue #24 |

Ce document sert de Sprint Backlog lisible et de scénario de démonstration. Il
est mis à jour au fil du sprint ; le compte-rendu final sera
`SPRINT_4_REVIEW.md`.

---

## 1. Objectif du sprint

Une démonstration **de bout en bout** : un message part du simulateur, traverse
l'API, est nettoyé et chiffré, alimente l'indice et la courbe de prix, et
s'affiche dans le dashboard ; l'acheteur retrouve les mêmes données par l'API
REST.

## 2. Sprint Backlog

| Issue | Tâche | Assigné | Dépend de | Risque |
|---|---|---|---|---|
| #18 | CRUD parcelles/appareils/abonnés, API REST, rate limiting | Mourad | PR #25 | champs `village` / `surface_ha` à ajouter au modèle `Plot` |
| #19 | Intégration finale simulateur/boîtier, câblage | Mounpain | #6 | #6 non commencé |
| #20 | Intégration E2E, bascule IA, prix v2, tag `v4-partiel` | Olivier | PR #25, #13 routes, #14 | point de convergence |
| #21 | Finition visuelle, accessibilité, responsive | Olivier | #15, #16 | accessibilité absente de la maquette |
| #22 | Tableau animé, graphiques, modals CRUD, toasts | Patrick | #16, PR #25 | jQWidgets + Chart.js à intégrer |
| #23 | Recette finale, PV, préparation de la démo | Mike (PO) | tous | PO indisponible |
| #24 | Rituels Scrum, livrables, comptes-rendus | Olivier | — | — |

### Points de vigilance

1. **La PR #25 est fusionnée depuis le 10/11 (13:16).** Le backend est donc sur
   `main`, CI verte. Les issues #18, #20, #21 et #22 ne dépendent plus que de
   leurs auteurs ; le plan de secours (§5) ne concerne plus que le frontend.
2. **Le modèle `Plot` doit exposer `village` et `surface_ha`** (contrat §4.6,
   maquette écran 3). C'est un ajout de champs, pas une rupture : il peut être
   fait dans la PR #25 avant fusion.
3. **`hours_above_85` et `ia_detection_rate` sont calculés**, jamais saisis.
   Le formulaire de la maquette les laisse saisir : c'est un raccourci de
   démonstration à ne pas reproduire dans l'API.

## 3. Scénario de démonstration

Durée visée : 10 minutes.

| Étape | Action | Preuve attendue |
|---|---|---|
| 1 | Lancer le backend et le simulateur en mode « humidité critique » | `POST /api/v1/measurements` renvoie `201` |
| 2 | Provoquer une coupure réseau simulée puis la rétablir | aucune mesure perdue (critère §17.2) |
| 3 | Consulter `GET /api/v1/kpis` | indice > 60, niveau `eleve`, alerte active |
| 4 | Consulter `GET /api/v1/prices/forecast` | deux séries, `is_demo: true`, `formula_version: v1` |
| 5 | Se connecter au dashboard avec `acheteur@ebolowa.cm` / `demo1234` | 4 cartes, graphique d'humidité, courbe de prix |
| 6 | Créer puis supprimer une parcelle en modale | toast de confirmation à chaque action |
| 7 | Envoyer une image au diagnostic IA | drapeau, score en pourcentage, recommandation |
| 8 | Ouvrir la vue producteur | feu tricolore vert/orange/rouge, zéro texte |
| 9 | Rejouer l'étape 3 avec `curl` et un jeton | mêmes données que le dashboard (critère §17.5) |
| 10 | Tenter une mesure invalide (humidité 150 %) | `422` (critère §17.6) |

## 4. Critères d'acceptation du CDC §17

| # | Critère | Ticket | Statut au 10/11 |
|---|---|---|---|
| 1 | Un message JSON conforme arrive dans le Data Lake | #5, #6 | ✅ prouvé par `tests/test_e2e.py` ; simulateur #6 remplacé par le test |
| 2 | Une coupure réseau ne perd aucune mesure | #12 | ❌ non commencé |
| 3 | Plus de 48 h au-dessus de 85 % déclenche une alerte | #13 | ✅ service + routes `/kpis` et `/prices/forecast` livrés, 79 tests |
| 4 | Le prototype IA renvoie un drapeau et un score | #14 | 🟡 route `POST /diagnostic` livrée (stub déterministe, `is_demo: true`), modèle non entraîné |
| 5 | L'acheteur voit les KPIs et obtient les mêmes données par l'API | #15, #16, #18 | 🟡 page KPIs + courbe de prix branchées, tableau CRUD à faire (#16/#22) |
| 6 | Les entrées invalides ou malveillantes sont rejetées | #5, #10 | ✅ pipeline, `device_id` contraint, zone brute chiffrée |
| 7 | Chaque action de gestion affiche un toast | #22 | ❌ non commencé |
| 8 | L'historique Git montre le travail de chaque membre | #1, #3, #24 | ✅ |

Le détail des preuves (tests, routes, commits) et les limites assumées sont
dans [`CRITERES_ACCEPTATION.md`](CRITERES_ACCEPTATION.md).

## 5. Plan de secours (action R3-4)

Si le dashboard n'est pas prêt le 11/11, la démonstration se fait **sans
réseau** sur `maquettes/agro-data-maquette.html`, qui contient les 6 écrans et
des données simulées. Dans ce cas :

- la démonstration annonce clairement ce qui est simulé et ce qui est réel ;
- la partie backend est présentée sur Swagger (`/docs`) et par l'API réelle
  (CI verte, 79 tests) ;
- l'écart est consigné dans le compte-rendu de Review, sans le masquer.

## 6. Livrables attendus le 11/11

| Livrable | Support | Responsable |
|---|---|---|
| Dossier final (versions 2, 3, final) | `docs/livrables/` | SM |
| Compte-rendu de Sprint Review | `SPRINT_4_REVIEW.md` | SM |
| Rétrospective finale | `RETROSPECTIVES.md` § Sprint 4 | SM |
| Procès-verbal de recette | `docs/livrables/PV_RECETTE.md` | PO |
| Preuves des 8 critères CDC §17 | `docs/livrables/CRITERES_ACCEPTATION.md` | SM (#20) |
| Tag `v4-partiel` | Git | SM (#20) |
| Documentation OpenAPI | `GET /docs` | Mourad (#18) |

## 7. Décisions attendues

| Sujet | Décideur | Échéance |
|---|---|---|
| Fusion de la PR #25 | PO | ✅ fusionnée le 10/11 à 13:16 |
| Validation du contrat v1.2 | PO | avant le 11/11 |
| Validation des critères §17.1 à §17.8 | PO | 11/11 |
| Sort de #12 et #14 si non livrés | PO | 11/11, consigné en Review |
