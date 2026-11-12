# Procès-verbal de recette — AGRO-DATA, livraison finale

| Champ | Valeur |
|---|---|
| Projet | AGRO-DATA — surveillance de la pourriture brune du cacaoyer |
| Livraison | Sprint 4, tag `v4-partiel` |
| Date de recette | 11/11/2026 |
| Environnement | Python 3.10, FastAPI + Uvicorn, SQLite, Chrome 141, `127.0.0.1` |
| Rédacteur | MEKONTSO Olivier Steve (SM) |
| Validation | SM mandaté par le PO le 11/11/2026 ; PO indisponible pour signature |
| Verdict | **Accepté avec réserves** (réserves §6) |

## 1. Objet

Vérifier que le prototype livré satisfait les huit critères d'acceptation du
cahier des charges §17, que la chaîne complète fonctionne sur une base neuve et
que la démonstration de soutenance est reproductible en trois commandes.

## 2. Périmètre rejoué

| Élément | Version testée |
|---|---|
| Backend | commit de livraison `v4-partiel` (après correctifs de l'audit), base SQLite recréée à zéro |
| Dashboard | même commit, servi par `http.server` sur le port 8080 |
| Simulateur | `python -m simulator` (sain, humidité critique, coupure réseau) |
| IA | route `POST /api/v1/diagnostic`, mode `is_demo: true` |
| Firmware | écrit, **non compilé ni flashé** : hors recette matérielle |

## 3. Preuves automatisées

| Commande | Résultat |
|---|---|
| `cd backend && python -m pytest -q` | **106 passed** |
| `node --test dashboard/js/*.test.js` | **18 pass, 0 fail** |
| `python scripts/demo_e2e.py` | **10 contrôles OK, exit 0** |

Dernier passage de la démonstration de bout en bout :

```
OK  le backend répond sur /health
OK  connexion JWT de l'acheteur
OK  48 mesures acceptées et écrites dans le Data Lake
OK  device_id malveillant rejeté (422)
OK  diagnostic IA : drapeau=1 confiance=0.61 (is_demo=True)
OK  GET /api/v1/kpis répond
OK  au moins une alerte active après 48 h > 85 %
OK  indice d'infestation=69 (niveau eleve)
OK  GET /api/v1/prices/forecast répond
OK  prix ajusté 1158.67 > référence 1050.0 (FCFA/kg, is_demo=True)
```

Ces preuves ont été rejouées après application des correctifs de l'audit de fin
de projet (`docs/livrables/AUDIT.md`) : contrôle `409` avant suppression d'une
parcelle appareillée, indicateurs calculés exposés par `GET /plots`, libellés KPI
du dashboard corrigés, comptes de démonstration alignés sur la maquette,
garde-fou de configuration en production, CI à quatre jobs, seuils et fenêtres
d'analyse documentés et testés.

## 4. Recette des huit critères (CDC §17)

| # | Critère | Statut | Preuve / limite |
|---|---|---|---|
| 1 | Message JSON conforme dans le Data Lake | ✅ | `test_e2e.py`, `scripts/demo_e2e.py` (48 fichiers bruts), `test_contract.py` |
| 2 | Coupure réseau sans perte | ✅ | `test_simulator.py` ; CLI réelle : 24 mesures hors ligne, 20 renvoyées, 4 doublons refusés, 0 en attente |
| 3 | > 48 h à plus de 85 % déclenche une alerte | ✅ | `test_infestation.py`, `test_kpis.py` (48 h oui, 47 h non), `/kpis` |
| 4 | Prototype IA : drapeau + score | 🟡 | route livrée et testée, `is_demo: true`, modèle non entraîné (jeu d'images vide) |
| 5 | L'acheteur voit les KPIs, mêmes données par l'API | ✅ | dashboard branché sur `/kpis` et `/prices/forecast`, rendu vérifié dans Chrome, 18 tests JS |
| 6 | Entrées invalides ou malveillantes rejetées | ✅ | `test_measurements.py`, `test_security.py`, `device_id` contraint, 422 vérifié |
| 7 | Chaque action de gestion affiche un toast | ✅ | `toast.js` appelé après chaque CRUD |
| 8 | L'historique Git montre le travail de chaque membre | 🟡 | 3 apports extérieurs (PR #25, dashboard, `sahoda`) ; majorité des commits du SM |

## 5. Scénarios rejoués à la main

| Scénario | Commande | Observé |
|---|---|---|
| Parcelle saine | `python -m simulator --scenario sain --hours 2 --start …` | 2 mesures envoyées, aucune alerte |
| Humidité critique 48 h | `python scripts/demo_e2e.py` | 48 h ingérées, alerte RM1, indice 69 « élevé » |
| Coupure réseau | `python -m simulator --scenario coupure_reseau --hours 48 --send-now` | 24 h en tampon puis rejouées, tampon vidé, doublons refusés sans blocage |
| Diagnostic IA | `POST /api/v1/diagnostic` (multipart PNG) | drapeau 1, confiance 0,61, `is_demo: true` |
| CRUD parcelle | dashboard, formulaire parcelle | `village`, `surface_ha`, `reference_volume_kg` enregistrés et relus |
| Affichage navigateur | `app.html` avec session API réelle | cartes alimentées par `GET /api/v1/kpis`, note de source affichée |

## 6. Réserves et écarts assumés

1. **IA non entraînée** : `ai/dataset` est vide, la route répond en mode démo.
   Aucune précision ne doit être annoncée (issues #14 et #17 ouvertes).
2. **Firmware non flashé** : le code du boîtier existe, mais la démonstration
   matérielle n'a pas été faite (#19 fermée sur le code et le câblage).
3. **Prix prédictif v2** : non spécifié par le PO, seule la formule `v1`
   (1 050 FCFA/kg, coefficient 0,15) est exposée (#20 ouvert).
4. **Validation PO** : PO indisponible ; le SM valide en son nom, à confirmer
   par écrit.

## 7. Commandes de démonstration

```bash
# 1. Dépendances (une fois, depuis backend/)
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# 2. Backend (terminal 1, depuis backend/, venv activé)
uvicorn app.main:app --reload --port 8000

# 3. Dashboard (terminal 2, depuis la racine)
python3 -m http.server 8080 --directory dashboard

# 4. Chaîne complète (terminal 3, depuis la racine, venv activé)
python scripts/demo_e2e.py

# 5. Tests
cd backend && pytest -q
cd dashboard && node --test js/*.test.js
```

Navigateur : <http://127.0.0.1:8080/index.html> — comptes de démonstration
`acheteur@ebolowa.cm` / `demo1234` (admin) et `lecteur@ebolowa.cm` / `demo1234`
(lecture seule). API documentée : <http://127.0.0.1:8000/docs>.

Ordre à respecter pour la soutenance : lancer `demo_e2e.py` **après** toute
manipulation du simulateur, sinon les mesures saines plus récentes cassent la
série de 48 h et l'indice retombe.

## 8. Décision

La livraison est **acceptée avec réserves** : les critères 1, 2, 3, 5, 6 et 7
sont couverts par des tests exécutés et par la démonstration rejouée sur une
base neuve ; les critères 4 et 8 restent partiels pour les raisons du §6.
Aucune régression connue n'est ouverte sur le périmètre démontré.

| Rôle | Nom | Décision | Date |
|---|---|---|---|
| Scrum Master (mandaté PO) | MEKONTSO Olivier Steve | Accepté avec réserves | 11/11/2026 |
| Product Owner | à confirmer | — | — |
