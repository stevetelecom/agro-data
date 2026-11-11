# Simulateur du boîtier AGRO-DATA (bloc C)

Remplace le matériel quand il n'est pas disponible : produit des mesures
conformes au [contrat JSON](../docs/CONTRAT_JSON.md) §3, les envoie à l'API, et
conserve les mesures hors ligne pour les renvoyer au retour du réseau
(Store-and-Forward, critère §17.2).

| Fichier | Contenu | Issue |
|---|---|---|
| `generator.py` | message d'ingestion, série horaire, envoi HTTP `X-API-Key` | #6 |
| `scenarios.py` | `sain`, `humidite_critique` (RM1), `coupure_reseau` | #6 |
| `store_forward.py` | tampon JSON Lines persistant, reprise, anti-doublon | #12 |
| `__main__.py` | point d'entrée `python -m simulator` | — |
| `../firmware/agro_node/agro_node.ino` | croquis ESP32-CAM équivalent (non compilé) | #19 |

Aucune dépendance supplémentaire : uniquement la bibliothèque standard.

## Parcours testable au navigateur

### 1. Démarrer le backend (terminal 1)

```bash
cd backend
source .venv/bin/activate          # Windows : .venv\Scripts\activate
uvicorn app.main:app --reload      # http://127.0.0.1:8000
```

La base SQLite, l'appareil `AMB-P001` et les comptes de démonstration sont créés
au premier démarrage.

### 2. Servir le tableau de bord (terminal 2)

```bash
python -m http.server 8080         # depuis la racine du dépôt
```

Ouvrir <http://127.0.0.1:8080/dashboard/>, se connecter avec
`acheteur@ebolowa.cm` / `demo1234`, puis ouvrir l'onglet **Lecture terrain**.

### 3. Injecter un scénario (terminal 3)

```bash
# Parcelle saine : 72 h, aucune alerte
python -m simulator --scenario sain --hours 72

# Humidité critique : 60 h au-dessus de 85 %, alerte RM1 attendue
python -m simulator --scenario humidite_critique --hours 60

# Coupure réseau : 24 h hors ligne puis reprise
python -m simulator --scenario coupure_reseau --hours 48 --buffer /tmp/buffer.jsonl --wait 10
```

Recharger l'onglet **Lecture terrain** : le feu passe au rouge, la dernière
mesure affiche plus de 85 % d'humidité, et le bandeau d'alerte signale la
pourriture brune. Le journal de l'application enregistre les mesures ingérées.

Options utiles :

| Option | Effet |
|---|---|
| `--dry-run` | affiche le JSON sans appeler l'API |
| `--hours N` | nombre d'heures produites |
| `--device-id ID` | appareil émetteur (défaut `AMB-P001`) |
| `--api-base URL` | backend cible (défaut `http://127.0.0.1:8000`) |
| `--api-key KEY` | clé `X-API-Key` (défaut `agro-device-demo-key`) |
| `--buffer CHEMIN` | fichier du tampon local |
| `--wait SECONDES` | durée de la coupure simulée avant reprise |
| `--send-now` | reprise immédiate, sans attendre |

## Vérifier la reprise sans navigateur

```bash
# Backend arrêté : les mesures restent dans le tampon
python -m simulator --scenario coupure_reseau --buffer /tmp/buffer.jsonl --wait 0
cat /tmp/buffer.jsonl | wc -l      # 24 lignes en attente

# Backend redémarré, puis nouvelle exécution : le tampon se vide
python -m simulator --scenario coupure_reseau --buffer /tmp/buffer.jsonl --wait 0
```

Un refus `422` (mesure déjà persistée) retire la ligne du tampon : rejouer une
reprise ne crée jamais de doublon.

## Limites connues

- Le diagnostic IA est **simulé** : le firmware estime un taux de pixels sombres,
  il n'exécute aucun modèle entraîné.
- Le scénario `humidite_critique` produit 60 mesures d'affilée ; la limite de
  débit de l'API est de 120 requêtes par minute, ne pas enchaîner deux
  scénarios en parallèle.
- Le croquis `firmware/agro_node/agro_node.ino` n'a été ni compilé ni flashé
  faute de matériel : à valider sur le boîtier avant toute annonce.
