# Sprint 2 Review — Fondations

| | |
|---|---|
| **Sprint** | Sprint 2 — Fondations |
| **Échéance prévue** | 28/10/2026 (cahier des charges §16) |
| **Revue tenue le** | 10/11/2026 |
| **Tag** | `v2` |
| **Participants** | MEKONTSO Olivier Steve (SM), NKWANE Mourad, NTEINTIE Mounpain, NEGOUE Patrick |
| **PO** | MESSANGA MESSANGA Mike — **absent**, aucun critère d'acceptation validé |
| **Spectateur** | `@Metili` (enseignant), accès `write`, aucune issue assignée |

> **Note de calendrier.** Les commits de cet incrément portent la date du
> 10/11/2026 : l'historique a été consolidé tardivement, après l'échéance du
> 28/10. Les dates du cahier des charges ne sont pas décalées pour autant.
> L'écart est traité en rétrospective (action R2-1).

---

## 1. Objectif du sprint

Une chaîne minimale « simulateur → API → base » et les maquettes du dashboard.

## 2. Ce qui était planifié

| Issue | Tâche | Assigné | Statut en fin de sprint |
|---|---|---|---|
| #1 | Structure du dépôt, README, arborescence | Olivier | ✅ Terminé |
| #2 | CI GitHub Actions de base | Olivier | ✅ Terminé |
| #3 | Issues, labels, milestones, Kanban | Olivier | ✅ Terminé |
| #4 | Figer le contrat JSON avec le PO | Olivier + Mike | 🟡 Livré, non validé par le PO |
| #5 | Squelette FastAPI, modèles, schémas, `POST /measurements` | Mourad | 🟡 Livré dans la PR #25, non fusionné |
| #6 | Simulateur `generator.py` et 3 scénarios | Mounpain | ❌ Non commencé |
| #7 | Design system et maquettes login/dashboard | Olivier (reprise de MOD-B1) | 🟡 Maquette livrée, validation PO en attente |
| #8 | Page de connexion et navigation responsive | Patrick | ❌ Non commencé |
| #9 | Critères d'acceptation, jeux de données, images | Mike (PO) | ❌ Non commencé — PO indisponible |

Bilan : **3 terminés**, **4 partiels**, **2 non commencés** sur 9 tickets.

## 3. Ce qui a été livré

### 3.1 Dépôt et outillage (#1, #2, #3)

- Arborescence complète conforme au plan §1.2 : `ai/`, `backend/`, `dashboard/`, `docs/`, `firmware/`, `maquettes/`, `simulator/`.
- `README.md` avec badge CI, liens vers le backlog, le cahier des charges, le contrat, le Kanban et les milestones (commits `55e15da`, `8aeb18f`, `1328eb4`).
- CI GitHub Actions (`.github/workflows/ci.yml`) : tests sur `main` **et sur chaque branche poussée** (commit `1ea90e7`).
- 24 issues, labels `module:*` / `priorite:*` / `type:*`, 3 milestones (Sprint 2, 3, 4) et un Kanban public à trois colonnes.

### 3.2 Contrat d'échange JSON (#4)

- `docs/CONTRAT_JSON.md` v1.0 : transport, message d'ingestion, réponse `201`, erreurs `400`/`401`/`422`/`429`, lecture `GET /measurements` (commit `07697e8`).
- Passé en **v1.1** puis **v1.2** au Sprint 3 pour couvrir les écrans de la maquette (§4.4 à §4.8).
- `backend/tests/test_contract.py` vérifie que le document et le schéma Pydantic restent alignés.
- **Non validé par le PO**, qui était indisponible : le contrat est figé « en attente de confirmation » (règle de décision, `RITUELS_SCRUM.md` §5).

### 3.3 Design system et maquettes (#7)

- `maquettes/agro-data-maquette.html` (commit `10e7d3b`) : 6 écrans interactifs (connexion, tableau de bord, parcelles, diagnostic IA, vue producteur, API REST), thème cacao, mode sombre automatique et manuel, responsive à 820 px.
- `docs/DESIGN_SYSTEM.md` (commit `901f4ab`) : palette, typographie, formes, composants, écrans et routes, conformité CDC §14, écarts avec le backend.
- `dashboard/css/tokens.css` : jetons réutilisables, clair et sombre.
- Une première maquette d'un **autre projet** (TailleurPro) avait été poussée par erreur ; elle a été retirée (commit `6a6d9bd`).

### 3.4 Backend (#5)

- PR **#25** `feature/backend-mourad` : application FastAPI, modèles SQLAlchemy, schémas Pydantic, `POST /api/v1/measurements`, `GET /api/v1/measurements`, authentification JWT, chiffrement AES-256-GCM, pipeline de nettoyage, CRUD.
- **26 tests verts**, CI verte, PR `MERGEABLE` / `CLEAN`.
- Revue de code faite par le Scrum Master : 5 points relevés (secrets par défaut, `geo_enc` en clair dans la zone brute, `device_id` non contraint, CORS absent, `geo_enc String(1024)` trop court).
- **Laissée en brouillon** : Mourad exige une validation PO avant fusion.

## 4. Ce qui n'a pas été livré

| Ticket | Raison |
|---|---|
| #6 simulateur | Non commencé par le développeur assigné ; aucune dépendance technique, seul un manque de disponibilité |
| #8 page de connexion | Non commencée ; dépendait du design system livré en fin de sprint |
| #9 jeux de données et images | PO indisponible depuis le début du sprint |

## 5. Démonstration

1. Ouverture du dépôt : arborescence, README, badge CI vert.
2. Kanban : 24 cartes réparties dans les trois colonnes.
3. `docs/CONTRAT_JSON.md` : message d'ingestion et réponses d'erreur.
4. Maquette : parcours des 6 écrans, bascule clair/sombre, passage en largeur téléphone.
5. PR #25 : `GET /docs` (Swagger), `POST /api/v1/measurements` accepté puis rejeté sur humidité hors plage.

## 6. Décisions

| Décision | Qui | Suite |
|---|---|---|
| Le contrat JSON est figé en version provisoire, en attente du PO | SM | documenté §8 du contrat, révisé en v1.1 et v1.2 |
| La maquette `agro-data-maquette.html` devient la référence visuelle | SM | `docs/DESIGN_SYSTEM.md` |
| La PR #25 reste en brouillon jusqu'à validation PO | SM + Mourad | bloque #13 (routes), #15, #16 et la démo |
| Les dates de sprint ne sont pas décalées | SM | les incréments incomplets sont présentés tels quels |

## 7. Indicateurs

| Indicateur | Valeur |
|---|---|
| Tickets planifiés / terminés | 9 / 3 |
| Tickets partiellement livrés | 4 |
| Tickets non commencés | 2 |
| Tests automatisés sur `main` | 0 (le backend est dans la PR #25) |
| Tests automatisés dans la PR #25 | 26 |

## 8. Tag `v2`

Le tag annoté `v2` pointe sur l'état de l'incrément à la fin du Sprint 2. Son
message précise qu'il est **partiel** et renvoie à ce compte-rendu : le
squelette backend n'était pas encore fusionné.
