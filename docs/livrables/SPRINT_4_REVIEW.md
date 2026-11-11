# Sprint 4 Review — Restitution et intégration

| | |
|---|---|
| **Sprint** | Sprint 4 — Restitution et intégration |
| **Échéance prévue** | 11/11/2026 (cahier des charges §16) |
| **Revue prévue le** | 11/11/2026 |
| **Tag** | `v-final` — annoté, partiel (voir §10) |
| **Participants** | MEKONTSO Olivier Steve (SM) |
| **PO** | MESSANGA MESSANGA Mike — **validations en attente** |
| **Rédigé le** | 11/11/2026, sur l'état de `main` après fusion du dashboard (CI verte, 79 tests backend + 14 tests JS) |

> **Note de méthode.** Ce compte-rendu décrit l'état réel du dépôt et du Kanban,
> au soir de l'échéance, et non les intentions du Sprint Backlog. La version du
> 10/11 annonçait un dashboard et des toasts absents : ils ont été récupérés sur
> la branche de NTPbreak et fusionnés le 11/11 (commit `6d6e337`), ce qui change
> les critères 5 et 7. Les lignes « à valider » dépendent toujours du PO.

---

## 1. Objectif du sprint

Une démonstration de bout en bout : un message part du simulateur, traverse
l'API, est nettoyé et chiffré, alimente l'indice et la courbe de prix, et
s'affiche dans le dashboard ; l'acheteur retrouve les mêmes données par l'API
REST.

**Objectif atteint à 7 étapes sur 10** : la chaîne backend est complète et
prouvée par les tests, le dashboard permet désormais de se connecter, de
consulter les indicateurs et de gérer les données. Le point d'entrée manquant
reste le **simulateur** : la mesure initiale est injectée par `curl` /
`tests/test_e2e.py`, pas par un générateur.

## 2. Ce qui était planifié

| Issue | Tâche | Assigné | Statut en fin de sprint |
|---|---|---|---|
| #18 | CRUD parcelles/appareils/abonnés, API REST, rate limiting | Mourad | 🟡 Livré et fusionné ; champs `village` / `surface_ha` manquants |
| #19 | Intégration finale simulateur/boîtier, câblage | Mounpain | ❌ Non commencé, 0 commit |
| #20 | Intégration E2E, bascule IA, prix v2, tag `v-final` | Olivier (SM) | 🟡 E2E partielle, tag créé, prix v2 non fait |
| #21 | Finition visuelle, accessibilité, responsive | Olivier (SM) | 🟡 Technique fait, revue de design non validée par le PO |
| #22 | Tableau animé, graphiques, modals CRUD, toasts | Patrick | ✅ Livré le 11/11 (branche fusionnée) |
| #23 | Recette finale, PV, préparation de la démo | Mike (PO) | ❌ PV de recette absent |
| #24 | Rituels Scrum, livrables, comptes-rendus | Olivier (SM) | ✅ Reviews 2 à 4, rétrospectives, critères et tag |

Tickets du Sprint 4 : **2 terminés**, **3 partiels**, **2 non commencés** sur 7.

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

### 3.2 Dashboard — branche de NTPbreak fusionnée le 11/11

Le travail du bloc B existait sur `feature/IntegrationApiLoginJQwidegtsEtGraphique`
mais n'avait **jamais été proposé en PR** : il était donc absent de la livraison.
Il est désormais dans `main` (commit de fusion `6d6e337`) :

- `dashboard/index.html` : écran de connexion (validation, affichage/masquage du
  mot de passe, jeton en session, bascule de démonstration **seulement** si l'API
  est injoignable — jamais sur des identifiants refusés).
- `dashboard/app.html` + `app.js` : tableau de bord complet — indicateurs,
  mesures, parcelles, appareils, abonnés, vue terrain, journal.
- `grids.js` (jQWidgets), `charts.js` (Chart.js), `modals.js` (formulaires CRUD),
  `toast.js` (confirmation après chaque action), `metrics.js` (calculs d'indices).
- **14 tests JS** verts (`node --test js/*.test.js`), vendorisation locale de
  jQuery/jQWidgets/Chart.js (démo hors ligne).
- Corrections apportées à la fusion : `allow_origins=["*"]` en doublon supprimé
  (le port 8080 rejoint les origines autorisées), `.env` retiré du versionnement,
  README débarrassé de comptes de démonstration inexistants.

### 3.3 Documentation et pilotage

- `docs/CONTRAT_JSON.md` v1.2 (gelé), `docs/CRITERES_ACCEPTATION.md`,
  `docs/RITUELS_SCRUM.md`, `docs/RETROSPECTIVES.md`, reviews 2 à 4.
- Kanban remis à jour le 10/11 puis le 11/11 : 11 issues fermées avec preuves,
  cases cochées sur #4, #7, #18, #24.

## 4. Ce qui n'a pas été livré

| Ticket | Raison | Conséquence sur la démo |
|---|---|---|
| #6 simulateur | Non commencé (`generator.py` et `scenarios.py` = TODO) | étape 1 remplacée par `curl` / `test_e2e.py` |
| #12 store-and-forward | Non commencé (`store_forward.py` = TODO) | critère §17.2 non démontrable |
| #19 boîtier | Non commencé (`agro_node.ino` = squelette commenté) | pas de démonstration matérielle |
| #18 correctif | Branche de Mourad repoussée à l'identique de `main` (0 commit devant) | `village` / `surface_ha` absents du CRUD |
| #20 prix v2 | Non spécifié, non implémenté | seul `formula_version = v1` est exposé |
| #23 PV de recette | PO indisponible | recette non signée |
| Vue producteur zéro-texte | `kpis.js` n'est plus chargé par aucune page après la fusion | l'ancienne page `app.html` a été remplacée ; la vue subsiste en code seulement |

## 5. Recette des 8 critères du CDC §17

| # | Critère | Statut | Preuve / limite |
|---|---|---|---|
| 1 | Un message JSON conforme arrive dans le Data Lake | ✅ | `tests/test_e2e.py`, `data_lake/raw/*.json` ; **producteur = test, pas simulateur** |
| 2 | Une coupure réseau ne perd aucune mesure | ❌ | #12 non commencé, aucun test |
| 3 | Plus de 48 h au-dessus de 85 % déclenche une alerte | ✅ | `test_infestation.py`, `test_kpis.py`, routes `/kpis` |
| 4 | Le prototype IA renvoie un drapeau et un score | 🟡 | route livrée, `is_demo: true`, modèle non entraîné, `ai/dataset` vide |
| 5 | L'acheteur voit les KPIs et retrouve les mêmes données par l'API | ✅ | dashboard fusionné + 14 tests JS + `test_kpis.py` |
| 6 | Les entrées invalides ou malveillantes sont rejetées | ✅ | `test_measurements.py`, `test_security.py`, `device_id` contraint |
| 7 | Chaque action de gestion affiche un toast | ✅ | `toast.js` branché sur chaque CRUD (`app.js`) |
| 8 | L'historique Git montre le travail de chaque membre | 🟡 | voir §9 : 2 apports extérieurs, 37 des 42 commits du SM, Mounpain 0 |

Bilan : **5 validés**, **2 partiels**, **1 non couvert**. Les critères 5 et 7,
annoncés non couverts le 10/11, sont couverts depuis la fusion du dashboard.

## 6. Démonstration

| Étape du scénario | Faisable le 11/11 | Support |
|---|---|---|
| 1. Simulateur → `POST /measurements` (201) | ❌ | remplacé par `curl` / `test_e2e.py` |
| 2. Coupure réseau puis reprise | ❌ | non implémenté (#12) |
| 3. `GET /kpis` : indice > 60, alerte active | ✅ | API + `tests/test_kpis.py` |
| 4. `GET /prices/forecast` | ✅ | v1, `is_demo: true` |
| 5. Connexion dashboard | ✅ | `index.html` + `auth.js` |
| 6. Créer/supprimer une parcelle avec toast | ✅ | `modals.js` + `toast.js` |
| 7. Diagnostic IA sur image | ✅ | stub déterministe annoncé comme tel |
| 8. Vue producteur zéro-texte | 🟡 | plus accessible depuis le nouveau dashboard |
| 9. Mêmes données par `curl` avec jeton | ✅ | JWT sur `/kpis` et `/prices/forecast` |
| 10. Mesure invalide → 422 | ✅ | `test_measurements.py` |

**7 étapes sur 10.** Les étapes 1 et 2 doivent être annoncées comme non livrées ;
l'étape 8 se présente comme un reste-à-faire, pas comme un acquis.

## 7. Décisions

| Décision | Qui | Suite |
|---|---|---|
| La PR #25 est fusionnée sans les champs `village` / `surface_ha` | SM + Mourad | correctif #18 non poussé par Mourad ; non bloquant pour la démo |
| La branche du dashboard est fusionnée le jour de l'échéance, sans PR | SM | conflits résolus à la main, 79 + 14 tests rejoués après fusion |
| Le diagnostic IA reste un stub déterministe assumé | SM | `is_demo: true` dans la réponse et dans la doc ; aucune précision annoncée |
| Le critère §17.2 n'est pas couvert | SM | consigné ici et dans `CRITERES_ACCEPTATION.md` |
| Le prix v2 est abandonné pour ce livrable | SM, à valider PO | la v1 reste exposée avec `formula_version = v1` |
| Validation du contrat v1.2, du design system et des critères §17 | PO | **à valider pendant la revue** |

## 8. Indicateurs

| Indicateur | Valeur |
|---|---|
| Issues du dépôt (total / fermées) | 24 / 11 |
| Issues du Sprint 4 terminées | 2 sur 7 |
| Tests automatisés sur `main` | 79 backend + 14 JS |
| Commits sur `main` | 42 |
| Commits du SM / de NTPbreak / de Mourad | 37 / 3 / 2 |
| Pull requests fusionnées | 1 (#25) ; 1 branche fusionnée sans PR |
| Critères §17 validés | 5 sur 8 |

## 9. Écarts de processus

1. **Travail direct sur `main`** : 37 des 42 commits sont allés directement sur
   `main`, sans PR ni revue. C'est un **choix assumé du SM** (seul développeur
   sur le backend, itérations courtes), qui s'écarte de la DoD et de l'action
   R2-4 ; seule la PR #25 est passée par une branche et une revue. L'historique
   Git demandé par le critère §17.8 reste donc partiel : l'écart porte sur la
   traçabilité, pas sur l'existence du code. Arbitrage à trancher par le PO :
   soit la pratique est entérinée dans la DoD, soit elle est abandonnée.
2. **Livraison invisible** : le dashboard du bloc B était complet et testé sur
   une branche distante mais **aucune PR n'avait été ouverte**. Sans la
   vérification du 11/11, il aurait été déclaré « non commencé » alors qu'il
   représentait 3 200 lignes de code. Leçon : une branche poussée n'est pas une
   livraison, et « terminé » se vérifie dans `main`, pas dans une déclaration.
3. **Kanban décorrélé du code** : au 10/11, 21 issues étaient ouvertes dont
   plusieurs terminées depuis le Sprint 3 ; les cases n'étaient pas cochées.
   Corrigé les 10 et 11/11.
4. **Bloc C à l'arrêt** : Mounpain (73EGA) n'a produit **aucun commit** sur
   aucune branche ; le simulateur, le store-and-forward et le firmware sont
   restés des squelettes. C'est la cause unique du critère §17.2 manquant.
5. **PO indisponible** : aucune validation formelle depuis le Sprint 2, ce qui
   bloque #4, #7, #17, #21 et #23.

## 10. Tag `v-final`

Tag **annoté** sur l'état livré, recréé après la fusion du dashboard. Son message
liste explicitement le livré et le non-livré, sans quoi il laisserait croire à un
incrément complet.

- `v2` et `v3` : incréments des Sprints 2 et 3, tous deux partiels.
- `v-final` : état démontré du Sprint 4 — backend complet (79 tests), dashboard
  connexion + CRUD + graphiques + toasts (14 tests), mais sans simulateur, sans
  store-and-forward, sans firmware, sans prix v2 et sans IA entraînée.
- Le tag est **en local uniquement** tant que le `push` n'est pas fait
  (`git push origin main --follow-tags`).

Si le PO valide des critères supplémentaires pendant la séance, le tag reste
valable : il décrit l'état du code, pas le statut de la recette.
