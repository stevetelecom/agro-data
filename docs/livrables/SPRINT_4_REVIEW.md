# Sprint 4 Review — Restitution et intégration

| | |
|---|---|
| **Sprint** | Sprint 4 — Restitution et intégration |
| **Échéance prévue** | 11/11/2026 (cahier des charges §16) |
| **Revue prévue le** | 11/11/2026 |
| **Tag** | `v-final` — annoté, partiel (voir §10) |
| **Participants** | MEKONTSO Olivier Steve (SM) |
| **PO** | MESSANGA MESSANGA Mike — **validations en attente au 10/11** |
| **Rédigé le** | 10/11/2026, à partir de l'état de `main` (commit `fe5f8a7`, CI verte) |

> **Note de méthode.** Ce compte-rendu est rédigé la veille de la revue, à
> partir de l'état réel du dépôt et du Kanban, et non des intentions du Sprint
> Backlog. Il est à valider et à compléter pendant la séance du 11/11 : les
> lignes marquées « à valider » dépendent du PO.

---

## 1. Objectif du sprint

Une démonstration de bout en bout : un message part du simulateur, traverse
l'API, est nettoyé et chiffré, alimente l'indice et la courbe de prix, et
s'affiche dans le dashboard ; l'acheteur retrouve les mêmes données par l'API
REST.

**Objectif atteint partiellement** : la chaîne backend est complète et prouvée
par les tests, mais elle est alimentée par `curl` / `tests/test_e2e.py`, pas par
le simulateur, et le dashboard ne couvre que les écrans KPIs et producteur.

## 2. Ce qui était planifié

| Issue | Tâche | Assigné | Statut en fin de sprint |
|---|---|---|---|
| #18 | CRUD parcelles/appareils/abonnés, API REST, rate limiting | Mourad | 🟡 Livré et fusionné ; champs `village` / `surface_ha` manquants |
| #19 | Intégration finale simulateur/boîtier, câblage | Mounpain | ❌ Non commencé |
| #20 | Intégration E2E, bascule IA, prix v2, tag `v-final` | Olivier (SM) | 🟡 Intégration E2E partielle, prix v2 et tag non faits |
| #21 | Finition visuelle, accessibilité, responsive | Olivier (SM) | 🟡 Technique fait, revue de design non validée |
| #22 | Tableau animé, graphiques, modals CRUD, toasts | Patrick | ❌ Non commencé |
| #23 | Recette finale, PV, préparation de la démo | Mike (PO) | ❌ PV de recette absent |
| #24 | Rituels Scrum, livrables, comptes-rendus | Olivier (SM) | 🟡 Reviews 2 et 3 + rétros livrées ; review 4 et rétro finale en cours |

Tickets du Sprint 4 : **0 terminé**, **4 partiels**, **3 non commencés** sur 7.

## 3. Ce qui a été livré

### 3.1 Backend complet — PR #25 fusionnée le 10/11 à 13:16

- `POST /api/v1/auth/login` (JWT), rôles `admin` / `acheteur`, Argon2.
- `POST` et `GET /api/v1/measurements` : clé `X-API-Key`, pipeline de rejet
  (plages physiques, horodatage futur > 5 min, > 30 jours, doublons),
  `geo_enc` chiffré AES-256-GCM dans la zone brute.
- CRUD `/plots`, `/devices`, `/subscribers`, limitation de débit 120/min.
- `GET /api/v1/kpis` et `GET /api/v1/prices/forecast` (RM2, RM3 v1, audit RM5),
  protégés par JWT.
- `POST /api/v1/diagnostic` : validation JPEG/PNG ≤ 5 Mo, drapeau + score.
- **79 tests verts** en CI (`pytest -q`), dont `test_contract.py` (document ↔
  schémas Pydantic) et `test_e2e.py` (scénario de démonstration).

### 3.2 Restitution

- `dashboard/app.html` + `dashboard/js/kpis.js` : 4 cartes KPI, courbe
  d'humidité et de prix en SVG natif, vue producteur « zéro-texte »,
  repli sur données de démonstration si l'API est injoignable.
- `docs/DESIGN_SYSTEM.md` v1.3 et `dashboard/css/tokens.css`.

### 3.3 Documentation et pilotage

- `docs/CONTRAT_JSON.md` v1.2 (gelé), `docs/CRITERES_ACCEPTATION.md`,
  `docs/RITUELS_SCRUM.md`, `docs/RETROSPECTIVES.md`, reviews 2 et 3.
- Kanban remis à jour le 10/11 : 5 issues terminées fermées avec preuves
  (#5, #10, #11, #13, #15), cases cochées sur #4, #7, #18, #24.

## 4. Ce qui n'a pas été livré

| Ticket | Raison | Conséquence sur la démo |
|---|---|---|
| #6 simulateur | Non commencé (`generator.py` et `scenarios.py` réduits à un TODO) | étape 1 remplacée par `curl` / `test_e2e.py` |
| #12 store-and-forward | Non commencé (`store_forward.py` = TODO) | critère §17.2 non démontrable |
| #19 boîtier | Non commencé (`agro_node.ino` = squelette commenté) | pas de démonstration matérielle |
| #8 login | Non commencé (`dashboard/index.html` = squelette) | étape 5 remplacée par un accès direct à `app.html` |
| #16 / #22 dashboard | `api.js`, `auth.js`, `charts.js`, `grids.js`, `modals.js`, `toast.js` = TODO | tableau CRUD, modales et toasts absents |
| #20 prix v2 | Non spécifié, non implémenté | seul `formula_version = v1` est exposé |
| #23 PV de recette | PO indisponible | recette non signée |

## 5. Recette des 8 critères du CDC §17

| # | Critère | Statut | Preuve / limite |
|---|---|---|---|
| 1 | Un message JSON conforme arrive dans le Data Lake | ✅ | `tests/test_e2e.py`, `data_lake/raw/*.json` ; **producteur = test, pas simulateur** |
| 2 | Une coupure réseau ne perd aucune mesure | ❌ | #12 non commencé, aucun test |
| 3 | Plus de 48 h au-dessus de 85 % déclenche une alerte | ✅ | `test_infestation.py`, `test_kpis.py`, routes `/kpis` |
| 4 | Le prototype IA renvoie un drapeau et un score | 🟡 | route livrée, `is_demo: true`, modèle non entraîné, `ai/dataset` vide |
| 5 | L'acheteur voit les KPIs et retrouve les mêmes données par l'API | 🟡 | écran KPIs branché ; tableau CRUD absent (#16/#22) |
| 6 | Les entrées invalides ou malveillantes sont rejetées | ✅ | `test_measurements.py`, `test_security.py`, `device_id` contraint |
| 7 | Chaque action de gestion affiche un toast | ❌ | #22 non commencé, `toast.js` = TODO |
| 8 | L'historique Git montre le travail de chaque membre | 🟡 | voir §9 : 33 des 35 commits sont du SM, sans PR |

Bilan : **3 validés**, **2 partiels**, **2 non couverts**, **1 partiel côté
traçabilité** (critère 8).

## 6. Démonstration

| Étape du scénario | Faisable le 11/11 | Support |
|---|---|---|
| 1. Simulateur → `POST /measurements` (201) | ❌ | remplacé par `curl` / `test_e2e.py` |
| 2. Coupure réseau puis reprise | ❌ | non implémenté (#12) |
| 3. `GET /kpis` : indice > 60, alerte active | ✅ | API + `tests/test_kpis.py` |
| 4. `GET /prices/forecast` | ✅ | v1, `is_demo: true` |
| 5. Connexion dashboard | ❌ | page de connexion non implémentée (#8) |
| 6. Créer/supprimer une parcelle avec toast | ❌ | #16/#22 |
| 7. Diagnostic IA sur image | ✅ | stub déterministe annoncé comme tel |
| 8. Vue producteur zéro-texte | ✅ | `kpis.js` |
| 9. Mêmes données par `curl` avec jeton | ✅ | JWT sur `/kpis` et `/prices/forecast` |
| 10. Mesure invalide → 422 | ✅ | `test_measurements.py` |

**6 étapes sur 10.** Les étapes 1, 2, 5 et 6 doivent être annoncées comme non
livrées, ou remplacées par le plan de secours (§5 de
`SPRINT_4_PREPARATION.md`).

## 7. Décisions

| Décision | Qui | Suite |
|---|---|---|
| La PR #25 est fusionnée sans les champs `village` / `surface_ha` | SM + Mourad | correctif #18 à livrer par PR, non bloquant pour la démo |
| Le diagnostic IA reste un stub déterministe assumé | SM | `is_demo: true` dans la réponse et dans la doc ; aucun chiffre de précision annoncé |
| Les critères §17.2 et §17.7 sont déclarés non couverts | SM | consignés ici et dans `CRITERES_ACCEPTATION.md` |
| Le prix v2 est abandonné pour ce livrable | SM, à valider PO | la v1 reste exposée avec `formula_version = v1` |
| Le tag `v-final` est différé | SM | à créer après la séance, sur l'état réellement démontré |
| Validation du contrat v1.2, du design system et des critères §17 | PO | **à valider pendant la revue** |

## 8. Indicateurs

| Indicateur | Valeur |
|---|---|
| Issues du dépôt (total / fermées) | 24 / 8 |
| Issues du Sprint 4 terminées | 0 sur 7 |
| Tests automatisés sur `main` | 79 |
| Commits sur `main` | 35 |
| Commits du SM / des autres membres | 33 / 2 |
| Pull requests fusionnées | 1 (#25) |
| Critères §17 validés | 3 sur 8 |

## 9. Écarts de processus

1. **Travail direct sur `main`** : 33 des 35 commits sont allés directement sur
   `main`, sans PR ni revue. C'est un **choix assumé du SM** (seul développeur
   sur le backend, itérations courtes), qui s'écarte de la DoD et de l'action
   R2-4 ; seule la PR #25 est passée par une branche et une revue. L'historique
   Git demandé par le critère §17.8 ne montre donc pas le travail de chaque
   membre : l'écart porte sur la traçabilité, pas sur l'existence du code.
   Arbitrage à faire trancher par le PO : soit la pratique est entérinée dans
   la DoD, soit elle est abandonnée au profit de branches courtes.
2. **Kanban décorrélé du code** : au 10/11, 21 issues étaient ouvertes dont
   plusieurs terminées depuis le Sprint 3 ; les cases n'étaient pas cochées.
   Corrigé le 10/11 (5 issues fermées, cases mises à jour).
3. **Modules orphelins** : les blocs B (dashboard) et C (simulateur/boîtier)
   n'ont produit aucun code exécutable, faute de relance des assignés.
4. **PO indisponible** : aucune validation formelle depuis le Sprint 2, ce qui
   bloque #4, #7, #17, #21 et #23.

## 10. Tag `v-final`

Créé le 10/11 sur l'état destiné à la démonstration du 11/11, en tag **annoté**.
Son message liste explicitement le livré et le non-livré, sans quoi il laisserait
croire à un incrément complet.

- `v2` et `v3` : incréments des Sprints 2 et 3, tous deux partiels.
- `v-final` : état démontré du Sprint 4 — backend complet et 79 tests verts,
  mais sans simulateur, sans store-and-forward, sans dashboard CRUD, sans prix
  v2 et sans IA entraînée.
- Le tag est **en local uniquement** tant que le `push` n'est pas fait
  (`git push origin v-final`).

Si le PO valide des critères supplémentaires pendant la séance du 11/11, le tag
reste valable : il décrit l'état du code, pas le statut de la recette.
