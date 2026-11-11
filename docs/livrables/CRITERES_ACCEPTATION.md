# Critères d'acceptation du prototype (CDC §17)

| | |
|---|---|
| **Référence** | `docs/CAHIER_DES_CHARGES.md` §17 |
| **Date** | 11/11/2026 |
| **Auteur** | MEKONTSO Olivier Steve (SM), issue #20 |
| **Portée** | Vérification honnête des 8 critères avant la revue de sprint du 11/11 |

Ce document relie chaque critère du cahier des charges à une **preuve
exécutable** : un test automatisé, une route, un commit. Un critère n'est coché
que si la preuve existe dans `main`. Les critères partiels sont marqués 🟡 et
leur reste-à-faire est explicite : aucune promesse au-delà de ce qui tourne.

## Synthèse

| # | Critère | Statut | Preuve principale |
|---|---|---|---|
| 1 | Un message JSON conforme arrive dans le Data Lake | ✅ | `test_e2e.py::test_scenario_complet_de_demonstration` |
| 2 | Une coupure réseau ne perd aucune mesure | ✅ | `test_simulator.py::test_reprise_apres_coupure_envoie_tout_une_seule_fois` + démonstration CLI réelle (24 h hors ligne, 24 renvoyées, 0 doublon) |
| 3 | Plus de 48 h > 85 % déclenche une alerte | ✅ | `test_kpis.py` (alerte à 48 h, pas avant 47 h) |
| 4 | Le prototype IA retourne un drapeau et un score | 🟡 | `test_diagnostic.py`, `ai/infer.py` (stub, `is_demo: true`) |
| 5 | L'acheteur voit les KPIs et retrouve les mêmes données par l'API | ✅ | Dashboard branché sur `/api/v1/kpis` et `/prices/forecast`, 17 tests JS, `test_kpis.py` |
| 6 | Les entrées invalides ou malveillantes sont rejetées | ✅ | `test_measurements.py`, `test_security.py` |
| 7 | Chaque action de gestion affiche un toast | ✅ | `dashboard/js/toast.js` + appels `showToast` après chaque CRUD (`app.js`) |
| 8 | L'historique Git montre le travail de chaque membre | 🟡 | 2 PR (#25, fusion du dashboard) ; 40 des 45 commits de `main` sont du SM ; Mounpain : 2 commits sur `sahoda`, non fusionnés |

Légende : ✅ couvert et testé · 🟡 partiel, reste-à-faire documenté · ❌ non couvert.

---

## Détail par critère

### 1. Un message JSON conforme arrive dans le Data Lake — ✅

- Route `POST /api/v1/measurements` (clé `X-API-Key`), validation Pydantic du
  contrat §3, écriture du message brut dans `data_lake/raw/`.
- Le test de bout en bout ingère 48 mesures horaires et vérifie qu'il existe
  **48 fichiers bruts**, que le contenu est exploitable et qu'aucune
  coordonnée `geo_enc` n'apparaît en clair (chiffrement AES-256-GCM).
- Preuve : `backend/tests/test_e2e.py`, commit `54c7e79` (README) et `689c038`
  (chiffrement de la zone brute).
- Complément : le simulateur (issue #6, `simulator/generator.py`) produit les
  mêmes messages par la commande `python -m simulator --scenario sain`. Le test
  E2E n'est donc plus la seule source de messages conformes.

### 2. Une coupure réseau ne fait perdre aucune mesure — ✅

- Tampon local `simulator/store_forward.py` (issue #12) : une mesure par ligne
  en JSON Lines, réécriture atomique, mesure retirée uniquement après acceptation
  par l'API, anti-doublon sur `(device_id, timestamp)`.
- La reprise s'arrête au premier échec temporaire (réseau, 5xx, 429) pour
  conserver l'ordre chronologique ; un refus définitif `422` (mesure invalide ou
  déjà persistée) retire la ligne sans bloquer la file.
- Preuves : `backend/tests/test_simulator.py` (5 tests sur le tampon, dont un
  rejeu réel contre l'API qui vérifie l'absence de doublon), et une exécution
  manuelle : 24 mesures écrites hors ligne puis `24 renvoyées, 0 refusées,
  0 en attente`, tampon vide.
- Le firmware `firmware/agro_node/agro_node.ino` applique la même logique sur
  MicroSD, mais n'a pas été compilé ni flashé (voir plus bas).

### 3. Plus de 48 h au-dessus de 85 % déclenche une alerte — ✅

- Indice RM2 : `60 × min(1, heures>85 / 48) + 40 × taux IA`, borné 0-100.
- Alertes calculées par parcelle sur une fenêtre glissante de 48 h.
- Tests : `test_alerte_apres_48h_au_dessus_de_85` (indice 60, alerte active) et
  `test_pas_d_alerte_avant_48h` (47 h, pas d'alerte). La route `GET /api/v1/kpis`
  expose le résultat, et le test E2E confirme `active_alerts == 1` et
  `global_infestation_index >= 60`.
- Preuve : `backend/tests/test_kpis.py`, commit `821b1a3`.

### 4. Le prototype IA retourne un drapeau et un score — 🟡

- Route `POST /api/v1/diagnostic` : image JPEG/PNG (5 Mo max), réponse
  `phytophthora_detected` (0/1), `confidence`, `label`, `recommendation`.
- Le modèle n'est **pas entraîné** : `ai/infer.py` produit un score déterministe
  (SHA-256) et `is_demo` reste `true`. Le script `ai/train.py` (MobileNetV2) est
  fourni mais n'a pas tourné, faute de jeu d'images validé et licencié par le PO.
- Preuve : `backend/tests/test_diagnostic.py` (image valide, invalide, trop
  lourde, sans jeton, seuil configurable), commit `f5188cf`.
- Reste : jeu d'images validé, exécution de `ai/train.py`, report de
  `val_accuracy` dans `ai/model/metrics.json` et dans le dossier final.

### 5. L'acheteur voit les KPIs et obtient les mêmes données par l'API — ✅

- Le dashboard fusionné le 11/11 (`dashboard/index.html` → `app.html`, modules
  `api.js`, `app.js`, `grids.js`, `charts.js`, `metrics.js`) affiche les cartes
  d'indicateurs, les graphiques Chart.js et les grilles jQWidgets des mesures,
  parcelles, appareils, abonnés et journal.
- **Les indicateurs viennent du serveur** : connecté à l'API, `loadIndicators()`
  appelle `GET /api/v1/kpis` (indice, niveau, alertes, humidité, volume sain en kg)
  et `GET /api/v1/prices/forecast` (courbe de prix, formule v1). Le filtre par
  parcelle recharge les KPIs avec `plot_id`. En mode démonstration seulement, le
  dashboard recalcule localement — avec les mêmes constantes (1050 FCFA/kg,
  k = 0,15) et la même formule RM2/RM3 que le backend.
- Les mêmes données restent accessibles par l'API avec le jeton de l'acheteur :
  `GET /api/v1/kpis`, `/prices/forecast`, `/measurements`, `/plots`, `/devices`,
  `/subscribers`.
- Preuves : **17 tests JS** (`node --test js/*.test.js`), dont l'égalité de la
  formule de prix et l'adaptation de la courbe §4.5 ; `backend/tests/test_kpis.py`
  (dont `estimated_healthy_volume_kg`) ; vérification par appels API sur une base
  neuve (8 mesures et une parcelle créées au démarrage, connexion
  `acheteur@ebolowa.cm` → HTTP 200).
- Limite assumée : le parcours navigateur complet n'a pas été rejoué le 11/11 ;
  la validation visuelle reste à faire pendant la démonstration.

### 6. Les entrées invalides ou malveillantes sont rejetées — ✅

- Pipeline : plages physiques, horodatage futur (> 5 min), mesures de plus de
  30 jours, doublons `(device_id, timestamp)`.
- Sécurité : `device_id` contraint à `^[A-Za-z0-9._-]{1,64}$` (anti path
  traversal), `geo_enc` chiffré avant écriture, noms de fichiers nettoyés,
  rate limiting, JWT et rôles.
- Tests : `test_measurements.py` (plages, futur, doublon),
  `test_security.py` (geo chiffré, `device_id` dangereux, CORS) et le second
  test E2E (rejet de `../etc/passwd` puis ingestion normale).
- Preuve : commits `689c038` et `821b1a3`.

### 7. Chaque action de gestion affiche un toast — ✅

- `dashboard/js/toast.js` implémente `showToast(message, variant)` : nœud
  `#toast-root` (présent dans `index.html` et `app.html`), icône, `role="status"`
  pour les lecteurs d'écran, disparition après 4,2 s.
- Branché sur les actions de gestion dans `app.js` : création et modification
  d'une parcelle, d'un appareil et d'un abonné, et suppression (« Parcelle
  supprimée. », « Appareil supprimé. », « Abonné supprimé. »).
- Preuves : lecture du câblage `app.js` → `toast.js`, tests JS de validation des
  formulaires CRUD (14 verts). Aucun test automatisé ne couvre le rendu visuel
  du toast : à confirmer à l'écran pendant la démonstration.

### 8. L'historique Git montre le travail de chaque membre — 🟡

- 24 issues réparties par module (A1-A6, B1-B2, C1-C2, G1), milestones Sprint 2
  à 4, Kanban public : la répartition du **travail prévu** est tracée.
- Trois apports extérieurs sont visibles dans l'historique : la PR #25 (backend
  de Mourad, 2 commits), la fusion du dashboard de NTPbreak le 11/11
  (3 commits, `6d6e337`) et la branche `sahoda` de Mounpain (73EGA), poussée le
  11/11 avec 2 commits sur `simulator/` (générateur, scénarios, Store-and-Forward).
- Conséquence : l'historique ne montre pas le travail de chaque membre. Il est
  correct pour Mourad et Patrick (branches dédiées), partiel pour le bloc C :
  `sahoda` couvre #6 et #12 mais n'a ni test, ni firmware (#19), et n'est pas
  fusionnée (base de 29 commits en retard, 3 fichiers en conflit).
  L'écart sur le travail direct du SM est assumé (voir `SPRINT_4_REVIEW.md`
  §9.1) et laisse le critère **partiel**.
- Preuve : `git log --format='%an' | sort | uniq -c`,
  [PR #25](https://github.com/stevetelecom/agro-data/pull/25),
  `docs/livrables/SPRINT_4_REVIEW.md`.

---

## Comment rejouer les preuves

```bash
cd backend && pytest -q                 # 95 tests, dont test_e2e.py et test_simulator.py
python scripts/demo_e2e.py              # backend démarré : parcours complet
cd dashboard && node --test js/*.test.js  # 17 tests des modules du dashboard
```

---

## Ce que la démonstration du 11/11 peut affirmer

1. La chaîne ingestion → Data Lake → KPIs → courbe de prix fonctionne de bout en
   bout et est reproductible par un test automatisé et un script.
2. L'alerte RM1 et l'indice d'infestation sont conformes à la formule du CDC.
3. Le diagnostic IA répond et rejette proprement les images invalides, en mode
   démonstration explicitement signalé.
4. Les entrées malveillantes sont rejetées.
5. L'acheteur se connecte au dashboard, consulte les indicateurs et les grilles,
   et gère parcelles, appareils et abonnés avec un toast de confirmation
   (critères 5 et 7), sur les mêmes données que l'API.
6. Un boîtier simulé alimente cette chaîne et survit à une coupure réseau sans
   perdre de mesure (critères 1, 2 et 3), avec trois scénarios rejouables par
   `python -m simulator` (voir `simulator/README.md`).

## Ce qu'elle ne peut pas affirmer

1. Une précision de détection IA mesurée : le modèle n'est pas entraîné.
2. Un fonctionnement sur le matériel réel : le croquis ESP32-CAM
   (`firmware/agro_node/agro_node.ino`) n'a été ni compilé ni flashé faute de
   boîtier. Seul le simulateur, qui suit le même contrat et la même logique de
   tampon, a été exécuté.
3. Un prix de référence calibré : 1050 FCFA/kg et k = 0,15 restent des
   hypothèses de démonstration (formule v1), à confronter aux séries ICCO/CICC.
