# Contrat d'échange JSON — AGRO-DATA

**Version** : 1.0
**Date** : 10 novembre 2026
**Statut** : figée par le Scrum Master, **en attente de confirmation du Product Owner**
**Référence** : cahier des charges §12.1, §12.2, §17.1 et §17.6
**Implémentation** : `backend/app/schemas/measurement.py` (schémas Pydantic)
**Tests** : `backend/tests/test_contract.py`

Ce document est la référence unique pour tout ce qui échange des mesures : simulateur (#6), firmware (#19), backend (#5), IA (#14) et dashboard (#16). Toute modification doit être faite ici **et** dans le schéma Pydantic, dans le même commit.

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
| `device_id` | chaîne | oui | 1 à 64 caractères | Identifiant de l'appareil. Il rattache implicitement la mesure à une parcelle. |
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
| Format de `device_id` | restreindre à `^[A-Za-z0-9._-]{1,64}$` (sécurité : évite un path traversal dans les noms de fichiers du Data Lake) | revue PR #25, point 1 |
| `geo_enc` en clair dans la zone brute | exclure le champ du dump brut, ou chiffrer avant écriture | revue PR #25, point 2, BNF3 |
| `confidence` obligatoire ou non | garder obligatoire ; le simulateur fournit toujours une valeur | #6 |
| Unité de `timestamp` | secondes Unix UTC confirmé ; le simulateur doit convertir depuis `datetime` | #6 |

---

## 9. Historique

| Version | Date | Auteur | Changement |
|---|---|---|---|
| 1.0 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Première version figée à partir du CDC §12.1 et du schéma Pydantic de la PR #25 |
