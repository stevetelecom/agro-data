# AGRO-DATA
Service Data-as-a-Service de prédiction du risque de pourriture brune du cacao (Ambam, Cameroun).
Projet du cours GSA 712 / GSI 712 - Construire une Équipe Projet.
Scrum Master : MEKONTSO Olivier Steve - Product Owner : MESSANGA MESSANGA Mike

## Bloc B — dashboard

Depuis la racine du dépôt :

```bash
python3 -m http.server 8080
```

Puis ouvrir `http://127.0.0.1:8080/dashboard/`.

Comptes de test de l'API :

- `lecteur@agro-data.local` / `ChangeMe123!` (acheteur)
- `acheteur@agro-data.local` / `ChangeMe123!` (administration)

Si l'API ne répond pas :

- `acheteur@agrodata.local` / `Acheteur2026!`
- `admin@agrodata.local` / `Admin2026!`

L'adresse de l'API est `API_BASE_URL` dans le fichier `.env` à la racine du dépôt.
