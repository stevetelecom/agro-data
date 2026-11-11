/**
 * Rôle : adresse de l'API consommée par le dashboard.
 * Auteur : NEGOUE Patrick (bloc B), corrigé le 11/11 (issue #18).
 *
 * Ce fichier est chargé avant les modules ES par `index.html` et `app.html` :
 * il suffit de servir `dashboard/` (python -m http.server 8080 --directory
 * dashboard) sans exposer la racine du dépôt. Dans le navigateur, une valeur
 * posée à la main (`window.AGRO_CONFIG.apiBaseUrl = ...`) reste prioritaire,
 * et le fichier `.env` de la racine n'est lu qu'en secours.
 */
window.AGRO_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:8000",
};
