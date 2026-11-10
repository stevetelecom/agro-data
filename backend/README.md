# Backend AGRO-DATA (Mourad)

Modules **MOD-A1 / A2 / A3 / A6** : ingestion FastAPI, pipeline de nettoyage, AES-256-GCM + JWT, CRUD API.

## Prérequis

- Python 3.11+

## Installation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Lancer l'API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentation OpenAPI : http://127.0.0.1:8000/docs
- Santé : `GET /health`

### Authentification

- Appareil (ingestion) : header `X-API-Key` (valeur `DEVICE_API_KEY` du `.env`)
- Acheteur : `POST /api/v1/auth/login` avec l'utilisateur démo du `.env`, puis `Authorization: Bearer <token>`

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Routes (périmètre Mourad)

| Méthode | Route | Auth |
|---|---|---|
| POST | `/api/v1/auth/login` | — |
| POST | `/api/v1/measurements` | `X-API-Key` |
| GET | `/api/v1/measurements` | JWT |
| CRUD | `/api/v1/plots` | JWT |
| CRUD | `/api/v1/devices` | JWT |
| CRUD | `/api/v1/subscribers` | JWT |
