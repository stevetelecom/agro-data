# AGRO-DATA

[![CI](https://github.com/stevetelecom/agro-data/actions/workflows/ci.yml/badge.svg)](https://github.com/stevetelecom/agro-data/actions/workflows/ci.yml)

Service Data-as-a-Service de prédiction du risque de pourriture brune du cacao (Ambam, Cameroun).
Projet du cours GSA 712 / GSI 712 - Construire une Équipe Projet.
Scrum Master : MEKONTSO Olivier Steve - Product Owner : MESSANGA MESSANGA Mike

## Suivi du projet

- [Product Backlog](docs/PRODUCT_BACKLOG.md)
- [Cahier des charges](docs/CAHIER_DES_CHARGES.md)
- [Plan de codage](docs/PLAN_DE_CODAGE.md)
- [Contrat d'échange JSON](docs/CONTRAT_JSON.md) : format des mesures et des lectures, version 1.2
- [Design system](docs/DESIGN_SYSTEM.md) : palette, composants, écrans, écarts avec le backend
- [Maquette interactive](maquettes/agro-data-maquette.html) : 6 écrans, thème cacao, mode sombre
- [Rituels Scrum](docs/livrables/RITUELS_SCRUM.md) : rôles, rituels, Definition of Ready et Done
- [Comptes-rendus de sprint](docs/livrables/) : revues, rétrospectives et plan de démonstration
- [Issues](https://github.com/stevetelecom/agro-data/issues) : une issue par tâche, assignée et priorisée
- [Kanban](https://github.com/users/stevetelecom/projects/2) : colonnes À faire / En cours / Terminé
- [Milestones](https://github.com/stevetelecom/agro-data/milestones) : Sprint 2, Sprint 3, Sprint 4

## Démarrage local

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://127.0.0.1:8000
```

La documentation interactive est disponible sur `http://127.0.0.1:8000/docs`.
La base SQLite et les comptes de démonstration sont créés au premier démarrage.

### Tableau de bord

Servir le dossier `dashboard/` avec un serveur statique (les modules ES sont sous
`dashboard/js/`) :

```bash
python -m http.server 8080 --directory dashboard   # http://127.0.0.1:8080/
```

Servir `dashboard/` seul évite d'exposer `backend/` et le fichier `.env` sur le
port 8080 pendant la démonstration.

Le port 8080 est déjà autorisé par le CORS du backend. L'écran de connexion
(`dashboard/index.html`) ouvre le tableau de bord complet (`app.html`) :
indicateurs, mesures, parcelles, appareils, abonnés, vue terrain et journal.

L'adresse de l'API est `http://127.0.0.1:8000` par défaut, réglable dans
`dashboard/config.js` (versionné, clé `window.AGRO_CONFIG.apiBaseUrl`), puis par
`window.AGRO_API_BASE`, puis par la variable `API_BASE_URL` d'un fichier `.env`
à la racine (local, non versionné).
Connecté à l'API, le tableau de bord affiche les indicateurs et la courbe de prix
de `GET /api/v1/kpis` et `GET /api/v1/prices/forecast` ; les mêmes formules sont
recalculées localement en mode démonstration.

Si l'API est injoignable (réseau, timeout), l'écran de connexion bascule sur une
session de démonstration et l'indique clairement. Un refus du serveur (401, 403,
422, 429, 5xx) ne bascule jamais en démonstration : le message distingue des
identifiants refusés d'un service indisponible.

### Comptes de démonstration

| Rôle | E-mail | Mot de passe |
|---|---|---|
| `admin` | `acheteur@ebolowa.cm` | `demo1234` |
| `acheteur` (lecture seule) | `lecteur@ebolowa.cm` | `demo1234` |

Ces comptes sont réservés à la démonstration. Les secrets par défaut de
`backend/app/config.py` (`JWT_SECRET`, `AGRO_AES_KEY`, `DEVICE_API_KEY`) doivent
être surchargés par des variables d'environnement avant toute mise en ligne.

### Tests

```bash
cd backend
pytest -q
```

Les modules du tableau de bord ont leurs propres tests (Node ≥ 20) :

```bash
cd dashboard
node --test js/*.test.js
```

### Scénario de démonstration

Avec le backend démarré, le parcours de bout en bout se rejoue en une commande
(ingestion 48 h, rejet d'une mesure malveillante, diagnostic IA, KPIs, prix) :

```bash
python scripts/demo_e2e.py
```

### Simulateur du boîtier

Le boîtier est simulé sans dépendance supplémentaire : mesures conformes au
contrat, scénarios `sain`, `humidite_critique` et `coupure_reseau`, tampon local
Store-and-Forward.

```bash
python -m simulator --scenario sain --hours 72 --dry-run
python -m simulator --scenario humidite_critique --hours 60   # alerte RM1
python -m simulator --scenario coupure_reseau --buffer /tmp/buffer.jsonl --wait 10
```

Le parcours complet, du simulateur à l'onglet « Lecture terrain » du navigateur,
est décrit dans [simulator/README.md](simulator/README.md).

## API principale

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Jeton JWT |
| `POST` | `/api/v1/measurements` | Ingestion d'une mesure (clé `X-API-Key`) |
| `GET` | `/api/v1/measurements` | Consultation des mesures (JWT) |
| `GET` | `/api/v1/kpis` | Indicateurs du tableau de bord (§4.4) |
| `GET` | `/api/v1/prices/forecast` | Courbe de prix prédictive (§4.5) |
| `POST` | `/api/v1/diagnostic` | Diagnostic IA d'une image (§4.7) |
| `GET/POST/PUT/DELETE` | `/api/v1/plots` | CRUD parcelles |
| `GET/POST/PUT/DELETE` | `/api/v1/devices` | CRUD appareils |
| `GET/POST/PUT/DELETE` | `/api/v1/subscribers` | CRUD abonnés |

Les modèles de lecture détaillés sont dans [docs/CONTRAT_JSON.md](docs/CONTRAT_JSON.md).
