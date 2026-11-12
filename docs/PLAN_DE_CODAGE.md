# Plan de codage - AGRO-DATA

| | |
|---|---|
| Version | 1.0 - 24 octobre 2026 |
| Scrum Master | MEKONTSO Olivier Steve |
| Product Owner | MESSANGA MESSANGA Mike |
| Référence | `CAHIER_DES_CHARGES.md` et `PRODUCT_BACKLOG.md` |

Les choix techniques sont des **propositions à valider par consensus** en équipe (méthode du TD Séance 4). Toute évolution est tracée dans ce fichier.

---

## 1. Architecture du projet

### 1.1 Vue d'ensemble

```
 BLOC C - Terrain                BLOC A - Serveur / PC                   BLOC B - Restitution
+---------------------+       +--------------------------------+      +----------------------+
| Boîtier ESP32-CAM   |       | API d'ingestion (FastAPI)      |      | Dashboard web        |
|  - DHT22 / sol      | HTTPS | -> validation (Pydantic)       | REST |  - login, KPIs       |
|  - caméra           |------>| -> pipeline de nettoyage       |<-----|  - graphiques        |
|  - MicroSD (tampon) |  JSON | -> Data Lake (brut + traité)   |      |  - tableau jQWidgets |
|  OU simulateur      |       | -> indice + prix prédictif     |      |  - CRUD en modals    |
+---------------------+       | -> module IA (diagnostic)      |      +----------------------+
                              | -> API REST pour acheteurs     |
                              +--------------------------------+
```

### 1.2 Arborescence du dépôt

```
agro-data/
├── README.md
├── docs/
│   ├── CAHIER_DES_CHARGES.md
│   ├── PLAN_DE_CODAGE.md
│   ├── PRODUCT_BACKLOG.md
│   └── livrables/                  # versions v2, v3, v4-partiel du dossier
├── simulator/                      # Bloc C (simulation) - Mounpain
│   ├── generator.py                # génération des mesures JSON
│   ├── scenarios.py                # sain, humidité critique, coupure réseau
│   └── store_forward.py            # tampon local type MicroSD
├── firmware/                       # Bloc C (matériel, optionnel) - Mounpain
│   └── agro_node/agro_node.ino
├── backend/                        # Bloc A - Mourad et Olivier
│   ├── app/
│   │   ├── main.py                 # point d'entrée FastAPI
│   │   ├── config.py               # paramètres, variables d'environnement
│   │   ├── database.py             # connexion et session
│   │   ├── models/                 # tables SQLAlchemy
│   │   ├── schemas/                # schémas Pydantic (contrat JSON)
│   │   ├── routers/                # auth.py, measurements.py, plots.py, kpis.py, diagnostic.py
│   │   ├── services/
│   │   │   ├── pipeline.py         # nettoyage des flux
│   │   │   ├── infestation.py      # indice d'infestation
│   │   │   ├── pricing.py          # courbe de prix prédictive
│   │   │   └── crypto.py           # AES-256-GCM
│   │   └── security/               # hachage, JWT, limitation de débit
│   ├── tests/
│   └── requirements.txt
├── ai/                             # Bloc A - Olivier (avec Mike pour les données)
│   ├── dataset/                    # images (non versionnées si volumineuses)
│   ├── train.py                    # entraînement (transfert d'apprentissage)
│   ├── infer.py                    # inférence utilisée par le backend
│   └── model/
├── dashboard/                      # Bloc B - Angue et Patrick
│   ├── index.html                  # page de connexion
│   ├── app.html                    # application (KPIs, graphiques, tableaux)
│   ├── css/                        # design system
│   ├── js/                         # api.js, auth.js, charts.js, grids.js, modals.js, toast.js
│   └── assets/
└── .github/workflows/ci.yml        # tests automatiques à chaque push
```

## 2. Pile technique

| Couche | Technologie | Raison |
|---|---|---|
| Boîtier (optionnel) | ESP32-CAM, C++ (Arduino) | Caméra, MicroSD et Wi-Fi sur une seule carte |
| Simulation | Python 3.11 ou plus | Même format JSON que le boîtier |
| API | FastAPI, Uvicorn | Documentation OpenAPI automatique, validation intégrée |
| Validation | Pydantic | Rejet des entrées invalides |
| Base de données | SQLite (prototype), PostgreSQL (production) via SQLAlchemy | Requêtes paramétrées, anti injection SQL |
| Data Lake | Zone brute (fichiers JSON) et zone traitée (tables) | Simple, vérifiable, évolutif |
| Sécurité | Argon2 ou bcrypt, JWT, `cryptography` (AES-256-GCM) | Conformité Loi n° 2010/012 |
| IA | TensorFlow/Keras, MobileNetV2 (transfert d'apprentissage) | Peu de données nécessaires, export TFLite possible |
| Frontend | HTML, CSS, JavaScript, jQWidgets, Chart.js | Tableaux dynamiques animés, graphiques |
| Interface | Icônes Material, polices Google Fonts, aucune émoticône | Rendu professionnel |
| Qualité | pytest, GitHub Actions | Tests automatiques |
| Gestion | GitHub Issues et Projects (Kanban) | Visibilité pour l'enseignant |

Références officielles à consulter avant d'implémenter : documentation FastAPI, SQLAlchemy, Pydantic, `cryptography`, TensorFlow/Keras, jQWidgets, Chart.js, MDN Web Docs, OWASP Top 10.

## 3. Règles de codage communes

- **Commentaires** : chaque fichier commence par un en-tête (rôle, auteur). Chaque fonction a une docstring ou un commentaire explicite.
- **Structure** : un module = une responsabilité. Pas de code dupliqué entre modules.
- **Sécurité** : toute entrée est validée côté serveur (types, longueurs, plages) ; aucune requête SQL construite par concaténation ; sorties HTML échappées ; secrets dans des variables d'environnement, jamais dans Git ; champ mot de passe avec icône pour afficher ou masquer.
- **Interface** : responsive, icônes Material, polices Google Fonts, aucune émoticône, notification (toast) après chaque action de création, modification ou suppression validée.
- **Données** : le contrat JSON de la section 12 du cahier des charges est **figé en Sprint 2**. Tout changement passe par le Product Owner.
- **Tests** : chaque module du backend a au moins un test automatisé (cas normal et cas invalide).

### Workflow Git
- Branche principale : `main` (toujours fonctionnelle).
- Une branche par module : `feature/<module>-<prénom>` (exemple : `feature/api-ingestion-mourad`).
- Un commit après chaque fonctionnalité terminée, message au format `type(portée): description` (types : `feat`, `fix`, `docs`, `test`, `refactor`).
- Fusion dans `main` par Pull Request, relue par un autre membre, validée par le Scrum Master.
- Tags de version : `v2` (28 octobre), `v3` (4 novembre), `v4-partiel` (11 novembre).

### Définition de « terminé » (DoD)
Un ticket est terminé quand : le code est commenté, les tests passent, la revue est faite, la fusion dans `main` est effectuée, et le Product Owner a validé le critère d'acceptation.

## 4. Répartition des modules par membre

| Code | Module | Responsable | Bloc | Backlog |
|---|---|---|---|---|
| MOD-C1 | Simulateur de capteurs et scénarios | NTEINTIE Mounpain | C | PB-01, PB-02 |
| MOD-C2 | Tampon Store-and-Forward (type MicroSD) | NTEINTIE Mounpain | C | PB-03 |
| MOD-C3 | Firmware ESP32-CAM (si matériel disponible) | NTEINTIE Mounpain | C | PB-01, PB-04 |
| MOD-A1 | API d'ingestion, modèles et schémas | NKWANE Mourad | A | PB-07 |
| MOD-A2 | Pipeline de nettoyage des flux | NKWANE Mourad | A | PB-07 |
| MOD-A3 | Chiffrement AES-256-GCM et sécurité (JWT, hachage) | NKWANE Mourad | A | PB-05 |
| MOD-A4 | Indice d'Infestation et courbes de prix | MEKONTSO Olivier Steve | A | PB-08, PB-09 |
| MOD-A5 | Prototype IA (entraînement et inférence) | MEKONTSO Olivier Steve | A | PB-06, PB-10 |
| MOD-A6 | CRUD parcelles, appareils, abonnés (API) | NKWANE Mourad | A/B | PB-12, PB-13 |
| MOD-B1 | Design system et maquettes (login, dashboard) | NTYAM Angue | B | PB-11, PB-15 |
| MOD-B2 | Pages KPIs et interface producteur « zéro-texte » | NTYAM Angue | B | PB-11, PB-15 |
| MOD-B3 | Graphiques, tableau jQWidgets, modals CRUD, toasts | NEGOUE Patrick | B | PB-11 |
| MOD-B4 | Connexion, abonnement, appels à l'API | NEGOUE Patrick | B | PB-12, PB-13 |
| MOD-Q1 | Critères d'acceptation, données de test, jeu d'images, validation | MESSANGA MESSANGA Mike (PO) | Transverse | PB-06, PB-14 |
| MOD-G1 | Dépôt Git, CI, intégration, revues, documentation | MEKONTSO Olivier Steve (SM) | Transverse | - |

Le Product Owner ne code pas dans l'équipe de développement, mais il prépare les données de test et le jeu d'images, rédige les critères d'acceptation et valide chaque incrément.

## 5. Plan de codage par sprint

### Sprint 2 - Fondations (jusqu'au 28 octobre 2026)
Objectif : une chaîne minimale « simulateur vers API vers base » et les maquettes du dashboard.

| Membre | Tâches | Livrable vérifiable |
|---|---|---|
| Olivier | Structure du dépôt, `README`, CI de base, tickets GitHub assignés, figer le contrat JSON avec le PO | Dépôt structuré, Project Kanban visible |
| Mourad | Squelette FastAPI, modèles et schémas Pydantic, `POST /api/v1/measurements` (validation seule) | Route qui accepte un JSON valide et refuse un JSON invalide |
| Mounpain | `generator.py` et trois scénarios (sain, humidité critique, coupure réseau) | Le simulateur envoie des messages conformes |
| Angue | Design system (couleurs, typographie, composants), maquettes login et dashboard | Maquettes validées par le PO |
| Patrick | Page de connexion (icône afficher/masquer le mot de passe), squelette de navigation responsive | Page de connexion fonctionnelle (sans back-end réel) |
| Mike (PO) | Critères d'acceptation, 3 jeux de données de test, début de collecte d'images (licences vérifiées) | Fichier de tests et dossier d'images |

### Sprint 3 - Traitement (jusqu'au 4 novembre 2026)
Objectif : les données entrantes sont nettoyées, protégées, évaluées par l'indice et par l'IA.

| Membre | Tâches | Livrable vérifiable |
|---|---|---|
| Mourad | Pipeline de nettoyage (anomalies, doublons), chiffrement AES-256-GCM, authentification JWT, hachage des mots de passe | Mesures invalides rejetées, champ `geo_enc` chiffré en base |
| Mounpain | Tampon Store-and-Forward : écriture locale, reprise de l'envoi au retour du réseau | Scénario « coupure réseau » sans perte de message |
| Olivier | Indice d'Infestation (règle des 85 % pendant 48 h), prix prédictif v1, entraînement du modèle IA v1 et route `POST /api/v1/diagnostic` | Indice calculé sur les scénarios, diagnostic avec score de confiance |
| Angue | Page KPIs (cartes, indicateurs couleur), interface producteur « zéro-texte » | Écrans responsive validés |
| Patrick | Intégration du login avec l'API, structure du tableau jQWidgets et des graphiques avec données d'essai | Connexion réelle et premier graphique alimenté |
| Mike (PO) | Validation des calculs de l'indice sur les jeux de test, étiquetage des images | Rapport de validation |

### Sprint 4 - Restitution et intégration (jusqu'au 11 novembre 2026)
Objectif : démonstration complète de bout en bout.

| Membre | Tâches | Livrable vérifiable |
|---|---|---|
| Mourad | Routes de gestion (parcelles, appareils, abonnés), API REST de consultation, limitation de débit, documentation OpenAPI | Documentation interactive accessible, tests passés |
| Mounpain | Intégration finale simulateur ou boîtier, options de configuration, documentation du câblage | Démonstration d'acquisition réelle ou simulée |
| Olivier | Intégration de bout en bout, bascule du diagnostic IA vers le serveur, prix prédictif v2, tag `v4-partiel`, dossier final | Scénario de démonstration reproductible |
| Angue | Finition visuelle, accessibilité, cohérence sur téléphone, tablette et ordinateur | Revue de design validée |
| Patrick | Tableau jQWidgets animé, graphiques complets, modals CRUD, notifications toast sur chaque action validée | Fonctionnalités de gestion opérationnelles |
| Mike (PO) | Recette finale selon les critères d'acceptation (section 17 du cahier des charges), préparation de la démonstration | Procès-verbal de recette |

## 6. Interface de l'API (contrat de départ)

| Méthode | Route | Rôle | Responsable |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Connexion, retourne un jeton | Mourad |
| POST | `/api/v1/measurements` | Ingestion d'une mesure (clé d'API appareil) | Mourad |
| GET | `/api/v1/measurements` | Liste filtrable des mesures | Mourad |
| POST | `/api/v1/diagnostic` | Diagnostic IA d'une image | Olivier |
| GET | `/api/v1/kpis` | Indicateurs (indice, humidité, alertes) | Olivier |
| GET | `/api/v1/prices/forecast` | Courbe de prix prédictive | Olivier |
| GET, POST, PUT, DELETE | `/api/v1/plots` | Gestion des parcelles | Mourad |
| GET, POST, PUT, DELETE | `/api/v1/devices` | Gestion des appareils | Mourad |
| GET, POST, PUT, DELETE | `/api/v1/subscribers` | Gestion des abonnés | Mourad |

## 7. Suivi et visibilité pour l'enseignant

- Un **GitHub Project** (colonnes À faire, En cours, Terminé) alimenté par les tickets assignés à chaque membre.
- Un historique de **commits** par membre et par branche.
- Une **Sprint Review** à la fin de chaque sprint, avec démonstration au Product Owner et compte-rendu dans `docs/livrables/`.
- Une **Rétrospective** hebdomadaire consignée dans le dossier.
- Les trois **tags** `v2`, `v3`, `v4-partiel`.

## 8. Risques techniques et plan B

| Risque | Plan B |
|---|---|
| Matériel indisponible | Le simulateur remplace le boîtier, le reste de la chaîne ne change pas |
| Modèle IA peu précis | Présenter le prototype comme preuve de concept, avec la précision mesurée et honnêtement indiquée |
| Retard sur le dashboard | Livrer d'abord KPIs et tableau (Must), puis graphiques avancés (Should) |
| Conflits Git | Branches courtes, fusions fréquentes, revue obligatoire |
| Hébergement indisponible | Démonstration en local, documentée dans le `README` |
