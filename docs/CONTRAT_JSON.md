# Contrat d'échange JSON — AGRO-DATA

**Version** : 1.2
**Date** : 10 novembre 2026
**Statut** : figée par le Scrum Master, **en attente de confirmation du Product Owner**
**Référence** : cahier des charges §12.1, §12.2, §17.1 et §17.6
**Maquette de référence** : `maquettes/agro-data-maquette.html` (commit `10e7d3b`), voir `docs/DESIGN_SYSTEM.md`
**Implémentation** : `backend/app/schemas/measurement.py` (schémas Pydantic)
**Tests** : `backend/tests/test_contract.py`

Ce document est la référence unique pour tout ce qui échange des mesures : simulateur (#6), firmware (#19), backend (#5), IA (#14) et dashboard (#16). Toute modification doit être faite ici **et** dans le schéma Pydantic, dans le même commit.

La version 1.1 ajoute les **modèles de lecture** attendus par les six écrans de la maquette (§4.4 à §4.7). Le message d'ingestion (§3) est inchangé.

---

## 1. Portée

| Rôle | Acteur | Sens |
|---|---|---|
| Producteur | simulateur Python (#6), boîtier ESP32-CAM (#19) | envoie une mesure |
| Consommateur | backend FastAPI (#5) | valide, nettoie, chiffre et persiste |
| Lecteur | dashboard (#16), acheteur via API REST | relit les mesures |

Le message est identique en sortie du simulateur et du boîtier : **le simulateur doit produire exactement ce format**, sans quoi il ne sert à rien.

---

## 2. Transport

| Élément | Valeur |
|---|---|
| Méthode et route | `POST /api/v1/measurements` |
| En-tête | `Content-Type: application/json` |
| Authentification | `X-API-Key: <clé appareil>` |
| Encodage | UTF-8 |
| Sérialisation | JSON, pas de champ supplémentaire non déclaré |

En production, le transport se fait en HTTPS (cahier des charges §13). La clé d'API n'est **jamais** placée dans le corps du message.

---

## 3. Message d'ingestion

### 3.1 Exemple canonique

```json
{
  "device_id": "AMB-P001",
  "timestamp": 1792800000,
  "climate": {
    "temperature_c": 27.4,
    "air_humidity_pct": 88.2,
    "soil_humidity_pct": 61.0
  },
  "diagnostic_ia": {
    "phytophthora_detected": 0,
    "confidence": 0.93
  },
  "geo_enc": "lat:2.383,lon:11.283"
}
```

### 3.2 Champs

| Champ | Type | Obligatoire | Contrainte | Description |
|---|---|---|---|---|
| `device_id` | chaîne | oui | `^[A-Za-z0-9._-]{1,64}$` | Identifiant de l'appareil. Il rattache implicitement la mesure à une parcelle. |
| `timestamp` | entier | oui | `> 0`, secondes Unix UTC | Seconde exacte de la mesure, pas de millisecondes. |
| `climate` | objet | oui | voir 3.3 | Mesures climatiques de l'heure. |
| `diagnostic_ia` | objet | oui | voir 3.3 | Résultat du diagnostic de pourriture brune. |
| `geo_enc` | chaîne | non (défaut `""`) | 1024 caractères maximum **avant** chiffrement | Métriques géospatiales et identifiants. Transité en clair dans le corps, puis **chiffré côté serveur** en AES-256-GCM avant toute persistance. |

### 3.3 Sous-objets

| Champ | Type | Contrainte | Unité |
|---|---|---|---|
| `climate.temperature_c` | réel | −10 à 55 | °C |
| `climate.air_humidity_pct` | réel | 0 à 100 | % |
| `climate.soil_humidity_pct` | réel | 0 à 100 | % |
| `diagnostic_ia.phytophthora_detected` | entier | `0` (sain) ou `1` (détecté) | — |
| `diagnostic_ia.confidence` | réel | 0 à 1 | probabilité |

### 3.4 Règles de validation du pipeline

Appliquées dans cet ordre après la validation Pydantic (`backend/app/services/pipeline.py`) :

| Règle | Condition de rejet | Code |
|---|---|---|
| Plages physiques (RM4) | température hors −10…55 °C, humidité hors 0…100 % | `422` |
| Horodatage incohérent | `timestamp <= 0` | `422` |
| Horodatage futur | plus de 300 s après l'heure serveur | `422` |
| Horodatage trop ancien | plus de 30 jours avant l'heure serveur | `422` |
| Doublon | couple (`device_id`, `timestamp`) déjà présent | `422` |

Un rejet est journalisé dans `data_lake/rejects.log` avec le motif, et la mesure brute est conservée dans la zone brute du Data Lake.

---

## 4. Réponse

### 4.1 Succès — `201 Created`

Le corps renvoyé est la mesure **persistée** : le climat est aplati et `geo_enc` revient **chiffré** (preuve que rien de clair n'est stocké, BNF3).

```json
{
  "id": 1,
  "device_id": "AMB-P001",
  "timestamp": 1792800000,
  "temperature_c": 27.4,
  "air_humidity_pct": 88.2,
  "soil_humidity_pct": 61.0,
  "phytophthora_detected": 0,
  "confidence": 0.93,
  "geo_enc": "q83k...=="
}
```

### 4.2 Erreurs

Format uniforme (FastAPI) :

```json
{ "detail": "temperature_c hors plage [-10.0, 55.0]: 60.0" }
```

| Code | Cause | Origine |
|---|---|---|
| `401` | `X-API-Key` absente ou invalide | `require_device_api_key` |
| `403` | jeton JWT valide mais rôle insuffisant | `require_roles` |
| `422` | schéma invalide ou règle du pipeline violée | Pydantic / `run_pipeline` |
| `429` | quota de requêtes dépassé (120/min par défaut) | `rate_limit_dependency` |
| `500` | erreur interne | non attendue, à signaler |

### 4.3 Lecture — `GET /api/v1/measurements`

Même structure que 4.1, en tableau. Authentification par JWT (`Authorization: Bearer <token>`), rôles `admin` ou `acheteur`. Filtres : `device_id`, `ts_from`, `ts_to`. Limite : 500 mesures, triées du plus récent au plus ancien. Pour une lecture autorisée, `geo_enc` est **déchiffré** côté serveur.

---

### 4.4 Indicateurs du tableau de bord — `GET /api/v1/kpis`

Alimente les quatre cartes et le graphique d'humidité de l'écran 2 de la maquette. Authentification JWT (`admin`, `acheteur`). Paramètres : `days` (défaut `7`), `plot_id` (optionnel).

```json
{
  "global_infestation_index": 62,
  "level": "eleve",
  "active_alerts": 2,
  "avg_air_humidity_pct": 83.0,
  "humidity_delta_7d": 4.0,
  "estimated_healthy_volume_pct": 57,
  "estimated_healthy_volume_kg": 2415.0,
  "plots_monitored": 4,
  "generated_at": "2026-11-10T11:00:00Z",
  "humidity_series": [
    {
      "plot_id": 1,
      "plot_name": "Parcelle Nkoulou",
      "under_alert": true,
      "points": [
        { "date": "2026-11-04", "air_humidity_pct": 78.0 },
        { "date": "2026-11-05", "air_humidity_pct": 80.0 },
        { "date": "2026-11-06", "air_humidity_pct": 83.0 },
        { "date": "2026-11-07", "air_humidity_pct": 86.0 },
        { "date": "2026-11-08", "air_humidity_pct": 88.0 },
        { "date": "2026-11-09", "air_humidity_pct": 87.0 },
        { "date": "2026-11-10", "air_humidity_pct": 89.0 }
      ]
    }
  ]
}
```

| Champ | Type | Règle de calcul |
|---|---|---|
| `global_infestation_index` | entier 0 à 100 | moyenne des indices par parcelle (RM2) |
| `level` | chaîne | `faible` si l'indice < 30, `modere` de 30 à 60, `eleve` si > 60 |
| `active_alerts` | entier | nombre de parcelles avec plus de 48 h consécutives au-dessus de 85 % (RM1) |
| `avg_air_humidity_pct` | réel | humidité de l'air moyenne sur la fenêtre |
| `humidity_delta_7d` | réel | écart en points avec la moyenne des 7 jours précédents |
| `estimated_healthy_volume_pct` | entier | `max(20, 100 − 0,7 × indice)` — **hypothèse de démonstration**, à calibrer avec l'ICCO |
| `estimated_healthy_volume_kg` | réel | somme, par parcelle, de `reference_volume_kg × (1 − indice / 100)` ; 0 pour un boîtier non rattaché |
| `plots_monitored` | entier | nombre de parcelles suivies |
| `humidity_series` | tableau | une série de `days` points par parcelle suivie, `under_alert` à `true` si la parcelle est en alerte RM1 |

Les seuils de `level` sont ceux de la maquette et de RM2 : la couleur de la pastille en dépend (`--ok`, `--mod`, `--ko`).

- `days` est compris entre 1 et 30 (défaut 7) ; `plot_id` restreint le calcul à une parcelle.
- Un appareil non rattaché à une parcelle forme sa propre série : `plot_id` vaut `0` et `plot_name` reprend le `device_id`. Le simulateur reste ainsi utilisable sans créer de parcelle au préalable.
- `humidity_series` ne contient que les parcelles ayant au moins une mesure dans la fenêtre ; `plots_monitored` compte ces séries.

### 4.5 Courbe de prix prédictive — `GET /api/v1/prices/forecast`

Alimente le second graphique de l'écran 2. Authentification JWT. Paramètre : `days` (défaut `7`).

```json
{
  "unit": "FCFA/kg",
  "horizon_days": 7,
  "is_demo": true,
  "formula_version": "v1",
  "points": [
    { "date": "2026-11-04", "reference_price": 1050, "adjusted_price": 1050 },
    { "date": "2026-11-05", "reference_price": 1050, "adjusted_price": 1062.6 },
    { "date": "2026-11-06", "reference_price": 1050, "adjusted_price": 1072.05 },
    { "date": "2026-11-07", "reference_price": 1050, "adjusted_price": 1094.1 },
    { "date": "2026-11-08", "reference_price": 1050, "adjusted_price": 1116.15 },
    { "date": "2026-11-09", "reference_price": 1050, "adjusted_price": 1136.63 },
    { "date": "2026-11-10", "reference_price": 1050, "adjusted_price": 1147.65 }
  ]
}
```

- `reference_price` est le prix de référence, `adjusted_price` le prix ajusté selon l'indice (RM3).
- Formule v1 : `adjusted_price = reference_price × (1 + 0,15 × indice / 100)`. Le coefficient `0,15` est défini dans `backend/app/services/pricing.py` et reste à calibrer avec les données ICCO/CICC.
- `is_demo` reste à `true` tant que les coefficients ne sont pas calibrés : le dashboard **doit** afficher la mention « courbe de démonstration ».
- `formula_version` est journalisé avec chaque calcul (RM5, audit).
- Le prix de référence de démonstration est constant : `REFERENCE_PRICE_FCFA_PER_KG = 1050` FCFA/kg (`pricing.py`). Il sera remplacé par la série ICCO/CICC lors de la calibration.
- Chaque jour de la courbe porte l'indice d'infestation calculé sur une fenêtre glissante de 48 h se terminant à la fin de ce jour (RM2) : sans recouvrement, une journée seule ne pourrait jamais atteindre le seuil de 48 h au-dessus de 85 %.
- `days` est compris entre 1 et 30 (défaut 7).

### 4.6 Parcelles — `/api/v1/plots`

Écran 3 (tableau CRUD) et formulaire modal. Authentification JWT ; écriture réservée au rôle `admin`.

```json
{
  "id": 1,
  "name": "Parcelle Nkoulou",
  "village": "Ambam centre",
  "surface_ha": 3.2,
  "hours_above_85": 62,
  "ia_detection_rate": 0.55,
  "infestation_index": 82,
  "level": "eleve"
}
```

| Champ | Type | Écriture | Règle |
|---|---|---|---|
| `name` | chaîne | oui | 1 à 40 caractères, obligatoire |
| `village` | chaîne | oui | 1 à 40 caractères, obligatoire |
| `surface_ha` | réel | oui | > 0, pas à 0,1 près |
| `reference_volume_kg` | réel | oui | ≥ 0, défaut 0 ; base du KPI « volume sain en kg » |
| `hours_above_85` | entier | **non** | calculé sur les mesures, 0 à 168 |
| `ia_detection_rate` | réel | **non** | calculé sur les mesures, 0 à 1 |
| `infestation_index` | entier | non | RM2 |
| `level` | chaîne | non | `faible`, `modere`, `eleve` |

Le formulaire de la maquette laisse saisir `hours_above_85` et `ia_detection_rate` : c'est un raccourci de démonstration. Dans l'API réelle, ces deux valeurs sont **en lecture seule**, sinon l'indice devient falsifiable.

`DELETE /api/v1/plots/{id}` est refusé (`409`) si des appareils sont encore rattachés à la parcelle.

### 4.7 Diagnostic IA — `POST /api/v1/diagnostic`

Écran 4. Corps `multipart/form-data`, champ `image` (JPEG ou PNG, 5 Mo maximum). Authentification JWT.

```json
{
  "phytophthora_detected": 1,
  "confidence": 0.87,
  "label": "pourriture brune",
  "recommendation": "Pulvérisation ciblée sur la parcelle concernée.",
  "model": "mobilenetv2-v1",
  "is_demo": true
}
```

- `phytophthora_detected` : `0` sain, `1` détecté — même sémantique que `diagnostic_ia` du message d'ingestion.
- `confidence` : 0 à 1 ; la maquette l'affiche en pourcentage.
- `is_demo` : `true` tant que le modèle n'est pas entraîné sur un jeu d'images validé.
- Une image illisible ou d'un autre type que JPEG/PNG → `422`.
- Le seuil de décision est configurable via la variable d'environnement `IA_DETECTION_THRESHOLD` (défaut `0.5`, BF2.5). Le prototype actuel (`ai/infer.py`) valide l'image puis produit un score **déterministe** à partir de son empreinte SHA-256 : ce n'est pas un modèle entraîné, d'où `is_demo: true`.
- `ai/train.py` fournit le script de transfert d'apprentissage MobileNetV2 ; il n'est pas exécuté par la CI (TensorFlow et jeu d'images validé par le PO requis). La précision mesurée devra être reportée dans `ai/model/metrics.json` et citée sans surpromesse dans le dossier final.

### 4.8 Comptes de démonstration

Alignés sur l'écran de connexion de la maquette (commit `d524467`), créés au démarrage par `backend/app/seed.py` :

| Rôle | E-mail | Mot de passe | Usage |
|---|---|---|---|
| `admin` | `acheteur@ebolowa.cm` | `demo1234` | CRUD complet, écrans 2 à 6 |
| `acheteur` | `lecteur@ebolowa.cm` | `demo1234` | lecture seule |

`POST /api/v1/auth/login` accepte `{ "email": ..., "password": ... }` et renvoie `{ "access_token": ..., "token_type": "bearer" }`. Ces comptes sont réservés à la démonstration et doivent être supprimés ou changés avant toute mise en ligne.

---

## 5. Exemples rejetés

Humidité hors plage physique :

```json
{
  "device_id": "AMB-P001",
  "timestamp": 1792800000,
  "climate": { "temperature_c": 27.4, "air_humidity_pct": 140.0, "soil_humidity_pct": 61.0 },
  "diagnostic_ia": { "phytophthora_detected": 0, "confidence": 0.93 }
}
```

Réponse : `422`, `air_humidity_pct` doit être compris entre 0 et 100.

Doublon : renvoyer deux fois le même couple (`device_id`, `timestamp`) → `422` au second envoi. C'est cette règle qui protège la reprise d'envoi du Store-and-Forward (#12) : rejouer une mesure n'ajoute pas de ligne.

---

## 6. Exemple d'appel

```bash
curl -X POST http://127.0.0.1:8000/api/v1/measurements \
  -H "Content-Type: application/json" \
  -H "X-API-Key: agro-device-demo-key" \
  -d '{
    "device_id": "AMB-P001",
    "timestamp": 1792800000,
    "climate": {"temperature_c": 27.4, "air_humidity_pct": 88.2, "soil_humidity_pct": 61.0},
    "diagnostic_ia": {"phytophthora_detected": 0, "confidence": 0.93},
    "geo_enc": "lat:2.383,lon:11.283"
  }'
```

---

## 7. Règles de compatibilité

1. Le préfixe de route porte la version : `/api/v1`. Un changement cassant impose `/api/v2`.
2. **Ajouter** un champ optionnel est une évolution mineure (1.x) : les producteurs existants continuent de fonctionner.
3. **Renommer, supprimer ou rendre obligatoire** un champ est une rupture majeure : prévenir #6, #12, #16 et #19 avant de fusionner.
4. Les noms de champs sont en `snake_case`, les unités sont dans le nom (`_c`, `_pct`).
5. Aucune valeur `null` : un champ absent vaut sa valeur par défaut documentée.

---

## 8. Points ouverts

Ces points ne bloquent pas le développement, mais doivent être tranchés avant le livrable final :

| Point | Décision proposée | Référence |
|---|---|---|
| Format de `device_id` | ✅ restreint à `^[A-Za-z0-9._-]{1,64}$` (sécurité : évite un path traversal dans les noms de fichiers du Data Lake) | revue PR #25, point 1 |
| `geo_enc` en clair dans la zone brute | ✅ chiffré AES-256-GCM avant écriture ; le nom de fichier est aussi nettoyé | revue PR #25, point 2, BNF3 |
| `confidence` obligatoire ou non | garder obligatoire ; le simulateur fournit toujours une valeur | #6 |
| Unité de `timestamp` | secondes Unix UTC confirmé ; le simulateur doit convertir depuis `datetime` | #6 |
| Champs de `Plot` | ✅ `village`, `surface_ha` et `reference_volume_kg` ajoutés au modèle le 11/11 (`location_label` conservé comme libellé de secteur) | #18, `docs/DESIGN_SYSTEM.md` §8 |
| `humidity_series` dans `/kpis` | série agrégée par jour et par parcelle, plutôt qu'un appel `/measurements` par graphique | #13, #16 |
| Formule du volume sain | `max(20, 100 − 0,7 × indice)` est une hypothèse de démonstration, à calibrer | #13 |

---

## 9. Historique

| Version | Date | Auteur | Changement |
|---|---|---|---|
| 1.0 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Première version figée à partir du CDC §12.1 et du schéma Pydantic de la PR #25 |
| 1.1 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Ajout des modèles de lecture du dashboard (§4.4 à §4.7) alignés sur la maquette `agro-data-maquette.html` |
| 1.2 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Comptes de démonstration alignés sur l'écran de connexion (§4.8, commit `d524467`) |
