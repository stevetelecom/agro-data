# Critères d'acceptation du prototype (CDC §17)

| | |
|---|---|
| **Référence** | `docs/CAHIER_DES_CHARGES.md` §17 |
| **Date** | 10/11/2026 |
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
| 2 | Une coupure réseau ne perd aucune mesure | ❌ | dépend de #12 (Store-and-Forward), non implémenté |
| 3 | Plus de 48 h > 85 % déclenche une alerte | ✅ | `test_kpis.py` (alerte à 48 h, pas avant 47 h) |
| 4 | Le prototype IA retourne un drapeau et un score | 🟡 | `test_diagnostic.py`, `ai/infer.py` (stub, `is_demo: true`) |
| 5 | L'acheteur voit les KPIs et retrouve les mêmes données par l'API | 🟡 | `dashboard/app.html`, `test_kpis.py` ; tableau CRUD (#16/#22) à venir |
| 6 | Les entrées invalides ou malveillantes sont rejetées | ✅ | `test_measurements.py`, `test_security.py` |
| 7 | Chaque action de gestion affiche un toast | ❌ | `toast.js` = squelette (3 lignes) ; actions CRUD (#22) non branchées |
| 8 | L'historique Git montre le travail de chaque membre | 🟡 | 24 issues et 1 PR (#25) ; 33 des 35 commits sont du SM, travail direct sur `main` |

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
- Réserve : le simulateur dédié (#6) n'est pas livré ; le test joue son rôle en
  générant des messages conformes. La démonstration peut s'appuyer sur
  `backend/tests/test_e2e.py` ou sur un script `curl`.

### 2. Une coupure réseau ne fait perdre aucune mesure — ❌

- Le tampon Store-and-Forward est l'issue #12 (`simulator/store_forward.py`),
  encore à l'état d'ébauche. Aucun test ne peut donc prouver la reprise.
- Décision : ne pas cocher. La démonstration du 11/11 présente ce point comme
  une limite assumée du prototype, avec le plan de reprise documenté dans
  `docs/PLAN_DE_CODAGE.md`.

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

### 5. L'acheteur voit les KPIs et obtient les mêmes données par l'API — 🟡

- Le dashboard (`dashboard/app.html`) affiche les 4 cartes KPI, le graphique
  d'humidité et la courbe de prix, tous branchés sur l'API réelle avec repli de
  démonstration explicite.
- Les routes `GET /api/v1/kpis` et `GET /api/v1/prices/forecast` renvoient les
  mêmes valeurs que celles affichées (contrat §4.4/§4.5).
- Vérifié dans le navigateur avec un jeton réel : source « Données de l'API »,
  0 erreur console, aucun débordement à 985 px.
- Reste : le **tableau des parcelles** et les modales CRUD relèvent de #16/#22 ;
  sans eux, le critère n'est pas complet au sens « KPIs + graphiques + tableau ».

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

### 7. Chaque action de gestion affiche un toast — ❌

- Le fichier `dashboard/js/toast.js` n'est qu'un squelette (3 lignes de TODO) :
  aucun toast n'est implémenté dans l'application. Les actions de gestion
  (créer/modifier/supprimer une parcelle, un appareil, un abonné) dépendent de
  #22 et des pages CRUD de #16/#18.
- Décision : ne pas cocher. Le toast est visible dans la maquette et le design
  system, pas dans l'application.

### 8. L'historique Git montre le travail de chaque membre — 🟡

- 24 issues réparties par module (A1-A6, B1-B2, C1-C2, G1), milestones Sprint 2
  à 4, Kanban public : la répartition du **travail prévu** est tracée.
- Seule la PR #25 (backend de Mourad) est passée par une branche et une revue.
  Les 33 autres commits sont du SM, directement sur `main`, et les blocs
  simulateur/boîtier (Mounpain) et dashboard (Patrick) n'ont produit aucun
  commit.
- Conséquence : l'historique ne montre pas le travail de chaque membre, il
  montre celui du SM. L'écart est assumé (voir `SPRINT_4_REVIEW.md` §9.1) et
  laisse le critère **partiel**.
- Preuve : `git log --format='%an' | sort | uniq -c`,
  [PR #25](https://github.com/stevetelecom/agro-data/pull/25),
  `docs/livrables/SPRINT_4_REVIEW.md`.

---

## Comment rejouer les preuves

```bash
cd backend && pytest -q                 # 79 tests, dont test_e2e.py
python scripts/demo_e2e.py              # backend démarré : parcours complet
```

---

## Ce que la démonstration du 11/11 peut affirmer

1. La chaîne ingestion → Data Lake → KPIs → courbe de prix fonctionne de bout en
   bout et est reproductible par un test automatisé et un script.
2. L'alerte RM1 et l'indice d'infestation sont conformes à la formule du CDC.
3. Le diagnostic IA répond et rejette proprement les images invalides, en mode
   démonstration explicitement signalé.
4. Les entrées malveillantes sont rejetées.

## Ce qu'elle ne peut pas affirmer

1. La reprise après coupure réseau (critère 2) : non implémentée.
2. Une précision de détection IA mesurée : le modèle n'est pas entraîné.
3. Un tableau CRUD complet avec toasts (critères 5 et 7) : dépend de #16/#18/#22.
