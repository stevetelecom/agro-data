# Sprint 4 Review — Restitution et intégration

| | |
|---|---|
| **Sprint** | Sprint 4 — Restitution et intégration |
| **Échéance prévue** | 11/11/2026 (cahier des charges §16) |
| **Revue prévue le** | 11/11/2026 |
| **Tag** | `v-final` — annoté, partiel (voir §10) |
| **Participants** | MEKONTSO Olivier Steve (SM) |
| **PO** | MESSANGA MESSANGA Mike — **validations en attente** |
| **Rédigé le** | 11/11/2026, sur l'état de `main` après livraison du bloc C (CI verte, 92 tests backend + 14 tests JS) |

> **Note de méthode.** Ce compte-rendu décrit l'état réel du dépôt et du Kanban,
> au soir de l'échéance, et non les intentions du Sprint Backlog. La version du
> 10/11 annonçait un dashboard et des toasts absents : ils ont été récupérés sur
> la branche de NTPbreak et fusionnés le 11/11 (commit `6d6e337`), ce qui change
> les critères 5 et 7. Le bloc C, non livré par son titulaire, a été repris par
> le SM le 11/11 (simulateur, store-and-forward, firmware), ce qui change le
> critère 2 et débloque les étapes 1, 2 et 8 de la démonstration. Les lignes
> « à valider » dépendent toujours du PO.

---

## 1. Objectif du sprint

Une démonstration de bout en bout : un message part du simulateur, traverse
l'API, est nettoyé et chiffré, alimente l'indice et la courbe de prix, et
s'affiche dans le dashboard ; l'acheteur retrouve les mêmes données par l'API
REST.

**Objectif atteint à 10 étapes sur 10** : la chaîne est complète et prouvée par
les tests, le dashboard permet de se connecter, de consulter les indicateurs et
de gérer les données, et le **simulateur** fournit le point d'entrée manquant —
y compris la reprise après coupure réseau. Le firmware reste écrit mais non
flashé, faute de boîtier : c'est la seule réserve matérielle de la démo.

## 2. Ce qui était planifié

| Issue | Tâche | Assigné | Statut en fin de sprint |
|---|---|---|---|
| #18 | CRUD parcelles/appareils/abonnés, API REST, rate limiting | Mourad | ✅ Livré et fusionné ; `village`, `surface_ha` et `reference_volume_kg` ajoutés le 11/11 |
| #19 | Intégration finale simulateur/boîtier, câblage | Mounpain | 🟡 Non livré par son titulaire, repris par le SM le 11/11 : simulateur, tampon et firmware écrits ; firmware non flashé |
| #20 | Intégration E2E, bascule IA, prix v2, tag `v-final` | Olivier (SM) | 🟡 E2E complète avec le simulateur, tag créé, prix v2 non fait |
| #21 | Finition visuelle, accessibilité, responsive | Olivier (SM) | 🟡 Technique fait, revue de design non validée par le PO |
| #22 | Tableau animé, graphiques, modals CRUD, toasts | Patrick | ✅ Livré le 11/11 (branche fusionnée) |
| #23 | Recette finale, PV, préparation de la démo | Mike (PO) | ❌ PV de recette absent |
| #24 | Rituels Scrum, livrables, comptes-rendus | Olivier (SM) | ✅ Reviews 2 à 4, rétrospectives, critères et tag |

Tickets du Sprint 4 : **2 terminés**, **4 partiels**, **1 non commencé** sur 7.

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
- **92 tests verts** en CI (`pytest -q`), dont `test_contract.py` (document ↔
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

### 3.3 Bloc C — simulateur, Store-and-Forward, firmware (repris par le SM)

Rien de Mounpain (73EGA) n'étant arrivé dans `main` à la revue, le SM a écrit le
bloc entier le 11/11 pour que la démonstration ait un producteur de messages et
une preuve de reprise après coupure. Deux commits de son auteure ont été poussés
sur `sahoda` après la revue (voir §9.4) ; ils ne sont pas fusionnés :

- `simulator/generator.py` : message conforme au contrat §3 (horodatage Unix en
  secondes, `climate` / `diagnostic_ia` imbriqués, `geo_enc`), série horaire,
  envoi `POST /api/v1/measurements` avec `X-API-Key`, distinction échec
  temporaire / définitif.
- `simulator/scenarios.py` : `sain`, `humidite_critique` (> 85 % pendant plus de
  48 h, détection associée) et `coupure_reseau` (24 h hors ligne puis reprise).
  Les séries se terminent à l'heure courante, pour rester dans la fenêtre
  d'horodatage acceptée par l'API.
- `simulator/store_forward.py` : tampon JSON Lines persistant, réécriture
  atomique, anti-doublon `(device_id, timestamp)`, arrêt au premier échec
  temporaire pour conserver l'ordre, abandon des refus définitifs `422`.
- `python -m simulator` : point d'entrée CLI (`--scenario`, `--hours`,
  `--device-id`, `--dry-run`, `--buffer`, `--wait`).
- `firmware/agro_node/agro_node.ino` : croquis ESP32-CAM équivalent (DHT22,
  capteur de sol, photo, tampon MicroSD, reprise), **écrit mais non compilé ni
  flashé** faute de matériel.
- 13 nouveaux tests (`backend/tests/test_simulator.py`), dont un rejeu réel
  contre l'API qui prouve l'absence de doublon après reprise.
- Procédure de test navigateur : `simulator/README.md`.

Exécution réelle vérifiée le 11/11 sur un backend local : 12 mesures « sain »,
60 « humidité critique », 48 « coupure » (24 hors ligne) — 120 mesures
persistées, tampon vidé, aucun doublon.

### 3.4 Documentation et pilotage

- `docs/CONTRAT_JSON.md` v1.2 (gelé), `docs/CRITERES_ACCEPTATION.md`,
  `docs/RITUELS_SCRUM.md`, `docs/RETROSPECTIVES.md`, reviews 2 à 4.
- Kanban remis à jour le 10/11 puis le 11/11 : 11 issues fermées avec preuves,
  cases cochées sur #4, #7, #18, #24.

## 4. Ce qui n'a pas été livré

| Ticket | Raison | Conséquence sur la démo |
|---|---|---|
| #6 simulateur | Livré par le SM le 11/11 ; les 2 commits de `sahoda` sont fusionnés le 11/11 (`06e5d66`) sans reprendre leur implémentation, défaillante | étape 1 de la démo assurée par `python -m simulator` |
| #12 store-and-forward | Livré par le SM le 11/11, testé contre l'API | critère §17.2 désormais couvert |
| #19 boîtier | Écrit par le SM, **non compilé ni flashé** | pas de démonstration matérielle, seulement le simulateur |
| #18 correctif | Branche de Mourad repoussée à l'identique de `main` (0 commit devant), correctif fait par le SM | `village` / `surface_ha` / `reference_volume_kg` désormais exposés par `/api/v1/plots` |
| #20 prix v2 | Non spécifié, non implémenté | seul `formula_version = v1` est exposé |
| #23 PV de recette | PO indisponible | `PV_RECETTE.md` rédigé et validé par le SM mandaté (accepté avec réserves) |
| Code mort du dashboard | `kpis.js` (521 lignes) n'était chargé par aucune page après la fusion | supprimé le 11/11 ; la vue producteur zéro-texte vit dans l'onglet « Lecture terrain » d'`app.js` |

## 5. Recette des 8 critères du CDC §17

| # | Critère | Statut | Preuve / limite |
|---|---|---|---|
| 1 | Un message JSON conforme arrive dans le Data Lake | ✅ | `tests/test_e2e.py`, `data_lake/raw/*.json`, et producteur réel `python -m simulator` |
| 2 | Une coupure réseau ne perd aucune mesure | ✅ | `test_simulator.py` (5 tests du tampon + rejeu API) ; 24 h hors ligne renvoyées sans doublon |
| 3 | Plus de 48 h au-dessus de 85 % déclenche une alerte | ✅ | `test_infestation.py`, `test_kpis.py`, routes `/kpis` |
| 4 | Le prototype IA renvoie un drapeau et un score | 🟡 | route livrée, `is_demo: true`, modèle non entraîné, `ai/dataset` vide |
| 5 | L'acheteur voit les KPIs et retrouve les mêmes données par l'API | ✅ | dashboard branché sur `/kpis` et `/prices/forecast` + 17 tests JS + `test_kpis.py` |
| 6 | Les entrées invalides ou malveillantes sont rejetées | ✅ | `test_measurements.py`, `test_security.py`, `device_id` contraint |
| 7 | Chaque action de gestion affiche un toast | ✅ | `toast.js` branché sur chaque CRUD (`app.js`) |
| 8 | L'historique Git montre le travail de chaque membre | 🟡 | voir §9 : 3 apports extérieurs, 40 des 45 commits de `main` du SM, Mounpain 2 commits sur `sahoda` |

Bilan : **6 validés**, **2 partiels**, **0 non couvert**. Les critères 5 et 7,
annoncés non couverts le 10/11, sont couverts depuis la fusion du dashboard ; le
critère 2 l'est depuis la livraison du bloc C. Restent partiels le prototype IA
(non entraîné) et l'historique Git (travail direct sur `main`).

## 6. Démonstration

| Étape du scénario | Faisable le 11/11 | Support |
|---|---|---|
| 1. Simulateur → `POST /measurements` (201) | ✅ | `python -m simulator --scenario sain` |
| 2. Coupure réseau puis reprise | ✅ | `python -m simulator --scenario coupure_reseau --buffer /tmp/buffer.jsonl` |
| 3. `GET /kpis` : indice > 60, alerte active | ✅ | API + `tests/test_kpis.py` |
| 4. `GET /prices/forecast` | ✅ | v1, `is_demo: true` |
| 5. Connexion dashboard | ✅ | `index.html` + `auth.js` |
| 6. Créer/supprimer une parcelle avec toast | ✅ | `modals.js` + `toast.js` |
| 7. Diagnostic IA sur image | ✅ | stub déterministe annoncé comme tel |
| 8. Vue producteur zéro-texte | ✅ | onglet « Lecture terrain » de `app.html` (feu d'alerte, gros boutons muets) |
| 9. Mêmes données par `curl` avec jeton | ✅ | JWT sur `/kpis` et `/prices/forecast` |
| 10. Mesure invalide → 422 | ✅ | `test_measurements.py` |

**10 étapes sur 10.** La seule réserve est matérielle : le croquis ESP32-CAM
n'a pas été compilé, la démonstration s'appuie sur le simulateur.

## 7. Décisions

| Décision | Qui | Suite |
|---|---|---|
| La PR #25 est fusionnée sans les champs `village` / `surface_ha` | SM + Mourad | correctif #18 appliqué par le SM le 11/11 (modèle, schémas, migration, formulaire) |
| La branche du dashboard est fusionnée le jour de l'échéance, sans PR | SM | conflits résolus à la main, tests backend et JS rejoués après fusion |
| Le diagnostic IA reste un stub déterministe assumé | SM | `is_demo: true` dans la réponse et dans la doc ; aucune précision annoncée |
| Le bloc C est réécrit par le SM faute de livraison | SM | simulateur, tampon et firmware livrés le 11/11 ; écart de traçabilité consigné en §9.4 |
| Le prix v2 est abandonné pour ce livrable | SM, à valider PO | la v1 reste exposée avec `formula_version = v1` |
| Validation du contrat v1.2, du design system et des critères §17 | PO | **à valider pendant la revue** |

## 8. Indicateurs

| Indicateur | Valeur |
|---|---|
| Issues du dépôt (total / fermées) | 24 / 14 |
| Issues du Sprint 4 terminées | 5 sur 7, dont 3 reprises par le SM (#6, #12, #19) |
| Tests automatisés sur `main` | 92 backend + 14 JS |
| Commits sur `main` | 45 |
| Commits du SM / de NTPbreak / de Mourad | 40 / 3 / 2 |
| Pull requests fusionnées | 1 (#25) ; 1 branche fusionnée sans PR |
| Critères §17 validés | 6 sur 8 |

## 9. Écarts de processus

1. **Travail direct sur `main`** : 40 des 45 commits sont allés directement sur
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
4. **Bloc C livré hors délai, puis repris** : Mounpain (73EGA) n'a poussé que
   **2 commits** sur `sahoda`, le 10/11 à 17 h et le 11/11 à 4 h, sans test ni
   firmware ; le simulateur, le store-and-forward et le firmware sont restés des
   squelettes dans `main` jusqu'au 11/11. Le SM les a écrits lui-même pour ne pas
   livrer un critère manquant. Conséquence : le code existe et est testé, mais
   l'historique n'attribue pas ce travail à son titulaire. Action de
   rétrospective : exiger un commit par semaine et une PR bloquante avant la
   revue, plutôt qu'un livrable annoncé à l'oral.
5. **PO indisponible** : aucune validation formelle depuis le Sprint 2, ce qui
   bloque #4, #7, #17, #21 et #23.

## 10. Tag `v-final`

Tag **annoté** sur l'état livré, recréé après la fusion du dashboard. Son message
liste explicitement le livré et le non-livré, sans quoi il laisserait croire à un
incrément complet.

- `v2` et `v3` : incréments des Sprints 2 et 3, tous deux partiels.
- `v-final` : état démontré du Sprint 4 — backend complet (95 tests), dashboard
  connexion + CRUD + graphiques + toasts + vue terrain (17 tests), simulateur et
  store-and-forward testés, démonstration de bout en bout verte, firmware écrit
  mais non flashé ; sans prix v2 et sans IA entraînée.
- Le tag est poussé avec `main` (`git push origin main --follow-tags`), recréé
  sur le commit de livraison du bloc C.

Si le PO valide des critères supplémentaires pendant la séance, le tag reste
valable : il décrit l'état du code, pas le statut de la recette.
