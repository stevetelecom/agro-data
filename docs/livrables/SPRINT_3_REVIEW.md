# Sprint 3 Review — Traitement

| | |
|---|---|
| **Sprint** | Sprint 3 — Traitement |
| **Échéance prévue** | 04/11/2026 (cahier des charges §16) |
| **Revue tenue le** | 10/11/2026 |
| **Tag** | `v3` |
| **Participants** | MEKONTSO Olivier Steve (SM), NKWANE Mourad |
| **PO** | MESSANGA MESSANGA Mike — **absent**, aucun critère d'acceptation validé |
| **Spectateur** | `@Metili` (enseignant) |

> **Note de calendrier.** Même remarque qu'au Sprint 2 : les commits portent la
> date du 10/11/2026, l'échéance du cahier des charges reste le 04/11.

---

## 1. Objectif du sprint

Les données entrantes sont nettoyées, protégées, évaluées par l'indice
d'infestation et par l'IA.

## 2. Ce qui était planifié

| Issue | Tâche | Assigné | Statut en fin de sprint |
|---|---|---|---|
| #10 | Pipeline de nettoyage des flux | Mourad | 🟡 Livré dans la PR #25, non fusionné |
| #11 | Chiffrement AES-256-GCM, JWT, hachage | Mourad | 🟡 Livré dans la PR #25, non fusionné |
| #12 | Tampon Store-and-Forward | Mounpain | ❌ Non commencé |
| #13 | Indice d'infestation et prix prédictif v1 | Olivier | 🟡 Couche métier terminée, routes bloquées |
| #14 | Prototype IA v1 et `POST /diagnostic` | Olivier | ❌ Non commencé |
| #15 | Page KPIs et interface producteur zéro-texte | Olivier (reprise de MOD-B2) | ❌ Non commencé |
| #16 | Intégration login API, tableau jQWidgets, graphiques | Patrick | ❌ Non commencé |
| #17 | Validation de l'indice et étiquetage des images | Mike (PO) | ❌ Non commencé — PO indisponible |

Bilan : **0 terminé**, **3 partiels**, **5 non commencés** sur 8 tickets.

## 3. Ce qui a été livré

### 3.1 Pipeline, chiffrement et authentification (#10, #11) — PR #25

- `backend/app/services/pipeline.py` : validation, détection d'anomalies, doublons, écriture dans le Data Lake.
- `backend/app/security/` : chiffrement AES-256-GCM, JWT, hachage Argon2.
- `backend/app/routers/measurements.py` : `POST` et `GET /api/v1/measurements`.
- `backend/tests/` : **26 tests verts**, dont un test de contrat document ↔ schéma Pydantic.
- CI verte, PR `MERGEABLE` / `CLEAN`, revue de code postée.

### 3.2 Indice d'infestation et prix prédictif (#13) — `main`, commit `add13d4`

- `backend/app/services/infestation.py` :
  - RM2 : `indice = 60 × min(1, heures > 85 % / 48) + 40 × taux IA`, borné à 0-100 ;
  - seuils `faible` < 30, `modere` 30-60, `eleve` > 60 (identiques à la maquette) ;
  - alerte RM1 à partir de 48 h consécutives au-dessus de 85 % ;
  - agrégation par moyenne, volume sain estimé `max(20, 100 − 0,7 × indice)` ;
  - arrondi au supérieur sur les demis, pour reproduire la maquette (82,5 → 83).
- `backend/app/services/pricing.py` :
  - RM3 v1 : `prix ajusté = prix de référence × (1 + 0,15 × indice / 100)` ;
  - journalisation d'audit RM5 avec `formula_version = v1` ;
  - payload conforme au contrat §4.5.
- `backend/tests/test_infestation.py` et `test_pricing.py` : **21 tests**, dont un qui compare le payload de prix au bloc JSON du contrat.
- Modules purs (ni FastAPI ni SQLAlchemy), réutilisables par le simulateur.

### 3.3 Contrat et design system

- `docs/CONTRAT_JSON.md` **v1.1** : ajout des modèles de lecture déduits des 6 écrans de la maquette — `/kpis` (§4.4), `/prices/forecast` (§4.5), `/plots` (§4.6), `/diagnostic` (§4.7).
- `docs/CONTRAT_JSON.md` **v1.2** : comptes de démonstration (§4.8).
- Comptes de démonstration alignés sur la maquette, côté backend (commit `d524467` sur la branche PR) : `acheteur@ebolowa.cm` (admin) et `lecteur@ebolowa.cm` (acheteur), mot de passe `demo1234`.
- `docs/DESIGN_SYSTEM.md` et `dashboard/css/tokens.css` : prêts pour l'intégration (#16).

## 4. Ce qui n'a pas été livré

| Ticket | Raison |
|---|---|
| #12 store-and-forward | Non commencé ; aucun compte-rendu du développeur assigné |
| #14 prototype IA | Non commencé ; le jeu d'images (#9) et les critères d'acceptation (#17) ne sont pas fournis par le PO, et la route dépend de la PR #25 |
| #15 page KPIs | Non commencée ; dépend de `/kpis`, lui-même bloqué par la PR #25 |
| #16 intégration dashboard | Non commencée ; dépend de la PR #25 (CORS, JWT) et des pages de #15 |
| #17 validation de l'indice | PO indisponible |

## 5. Démonstration

1. `pytest -q` sur `main` : **22 tests verts** (21 tests MOD-A4 + le test de fumée).
2. `pytest -q` sur la branche `feature/backend-mourad` : **26 tests verts**.
3. Calcul de l'indice sur les données de la maquette : parcelle Nkoulou (62 h, 55 %) → **82**, niveau **élevé**.
4. Courbe de prix : 1085 FCFA/kg à l'indice 62 → **1185,91**, cohérent avec le dernier point de la maquette (1185).
5. Swagger de la PR #25 : `POST /api/v1/auth/login` avec le compte de démonstration.

## 6. Décisions

| Décision | Qui | Suite |
|---|---|---|
| La couche métier de #13 est fusionnée dans `main` **sans** ses routes | SM | modules purs, testés ; les routes arrivent après le merge de #25 |
| Les comptes de démo sont alignés sur la maquette | SM | commit `d524467`, documenté au §4.8 du contrat |
| La PR #25 reste bloquée | SM + Mourad | point de convergence de #13, #15, #16, #20 |
| #14 est reporté au Sprint 4 | SM, faute de PO | le prototype peut tourner sur données simulées |

## 7. Indicateurs

| Indicateur | Valeur |
|---|---|
| Tickets planifiés / terminés | 8 / 0 |
| Tickets partiellement livrés | 3 |
| Tickets non commencés | 5 |
| Tests automatisés sur `main` | 22 |
| Tests automatisés dans la PR #25 | 26 |
| Points de revue ouverts sur la PR #25 | 5 |

## 8. Risque principal identifié

**Tout converge sur la PR #25.** Quatre tickets de deux personnes différentes
(#13, #15, #16, #20) ne peuvent pas avancer tant qu'elle n'est pas fusionnée.
Le PO est le seul à pouvoir lever le blocage, et il est indisponible. Ce point
est repris en rétrospective (action R3-1) et en préparation du Sprint 4.

## 9. Tag `v3`

Le tag annoté `v3` pointe sur l'état de l'incrément à la fin du Sprint 3. Son
message précise qu'il est **partiel** : les routes de #13 et l'intégration du
dashboard manquent.
