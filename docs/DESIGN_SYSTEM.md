# Design system — AGRO-DATA

**Source** : `maquettes/agro-data-maquette.html` (commit `10e7d3b`)
**Version** : 1.1
**Auteur de la maquette** : MEKONTSO Olivier Steve (MOD-B1 / B2)
**Implémentation** : `dashboard/css/tokens.css`
**Références** : cahier des charges §14 (interface), §13 (sécurité), plan §1.2 (MOD-B1)

Cette maquette est la **référence visuelle** du projet. Toute divergence dans le dashboard doit être justifiée ici.

---

## 1. Palette

Les jetons sont définis dans `dashboard/css/tokens.css`.

| Jeton | Valeur | Usage |
|---|---|---|
| `--brun` | `#8B4A2B` | couleur principale : boutons, titres, liens |
| `--brun-f` | `#3E2219` | brun profond : fonds, toasts |
| `--brun-m` | `#5A3020` | brun intermédiaire |
| `--or` | `#C8873A` | accent : bordures actives, barres de progression, focus |
| `--creme` | `#F0DDC0` | fonds secondaires, boutons `.btn.sec` |
| `--fond` | `#F7F1E8` | fond de page (clair) |
| `--carte` | `#FFFFFF` | fond des cartes (clair) |
| `--encre` | `#2B1A12` | texte principal |
| `--gris` | `#7A5C48` | texte secondaire, libellés |
| `--bord` | `#E2D6CC` | bordures, séparateurs |
| `--ok` | `#4F7F3A` | niveau faible, statut sain |
| `--mod` | `#C8873A` | niveau modéré, avertissement |
| `--ko` | `#A63D2F` | niveau élevé, alerte, suppression |

**Sémantique des niveaux** (RM2) : `--ok` < 30, `--mod` de 30 à 60, `--ko` > 60. Cette correspondance couleur/niveau ne doit jamais changer : c'est le seul repère de l'interface producteur « zéro-texte ».

### Mode sombre

Deux déclencheurs, dans cet ordre :

1. `@media (prefers-color-scheme: dark)` : automatique, sauf si `data-theme="light"` est posé sur `<html>` ;
2. `data-theme="dark"` : forcé par le bouton `contrast` de l'en-tête.

| Jeton | Valeur sombre |
|---|---|
| `--fond` | `#1E120D` |
| `--carte` | `#2B1A12` |
| `--encre` | `#F5E9DA` |
| `--gris` | `#C9AE98` |
| `--bord` | `#4A2E22` |
| `--creme` | `#3A2419` |

---

## 2. Typographie

| Élément | Valeur |
|---|---|
| Police principale | **Poppins** (400, 500, 600, 700), Google Fonts |
| Icônes | **Material Symbols Rounded**, classe `.ms` |
| Corps | 14 px, interligne 1,5 |
| Titres d'écran | 17 px (`header h2`) |
| Titres de carte | 14 px |
| Libellés de formulaire | 12 px, semi-gras, `--gris` |
| Valeur de KPI | 25 px, gras |
| Libellés de tableau | 11 px, majuscules, lettrage 0,8 px |

Aucune émoticône nulle part (CDC §14). Les icônes sont toujours du Material Symbols.

---

## 3. Formes et espacements

| Élément | Rayon | Ombre |
|---|---|---|
| Carte | 16 px | `0 10px 28px rgba(62,34,25,.10)` |
| Champ, bouton, icône-bouton | 12 px | — |
| Pastille (`.pill`) | 99 px | — |
| Boîte de connexion | 20 px | `0 24px 60px rgba(0,0,0,.4)` |
| Modale | 18 px | — |

Grille : `gap: 16px` ; KPI `repeat(auto-fit, minmax(210px, 1fr))` ; graphiques `minmax(340px, 1fr)` ; marge de vue `22px 24px`, largeur maximale 1200 px.

---

## 4. Composants

| Composant | Classe / structure | Remarque |
|---|---|---|
| Carte | `.card` | fond `--carte`, bordure 1 px, ombre |
| KPI | `.card.kpi` + `.ic` + `<small>` + `<b>` + `.pill` | icône dans un carré 48 px |
| Pastille de niveau | `.pill.ok` / `.mod` / `.ko` | texte blanc, jamais seule : toujours accompagnée du libellé |
| Barre de progression | `.barre > i` | largeur = indice, couleur = niveau |
| Tableau | `table` dans `.scroll` | défilement horizontal sous 560 px |
| Modale | `.fond > .modal` + `.acts` | fermeture au clic sur le fond |
| Toast | `#toast > .t` | 3,2 s, bordure gauche `--or`, icône `check_circle` |
| Bouton | `.btn`, `.btn.sec`, `.btn.ko`, `.btn.bl` | `.bl` = pleine largeur, `.ko` = suppression |
| Bouton d'action de ligne | `.mini`, `.mini.d` | modifier / supprimer |
| Champ mot de passe | `.champ > input + button` | icône `visibility` / `visibility_off` (CDC §13) |
| Zone de dépôt | `.drop` | bordure pointillée `--or`, clic ou glisser-déposer |
| Feu tricolore producteur | `.feu` | 190 px, icône 96 px, couleur = niveau |
| Gros boutons producteur | `.gros > button` | 2 × 2, icône 52 px + libellé |

---

## 5. Écrans

| # | Écran | Rôle | Routes appelées | Issue |
|---|---|---|---|---|
| 1 | Connexion | e-mail, mot de passe, œil, erreur inline | `POST /api/v1/auth/login` | #8 |
| 2 | Tableau de bord | 4 KPI, humidité 7 j, prix 7 j, parcelles à surveiller | `GET /api/v1/kpis`, `GET /api/v1/prices/forecast` | #15 |
| 3 | Parcelles | recherche, tableau CRUD, modales, suppression confirmée | `GET/POST/PUT/DELETE /api/v1/plots` | #16 |
| 4 | Diagnostic IA | dépôt d'image, drapeau, score, recommandation | `POST /api/v1/diagnostic` | #14 |
| 5 | Vue producteur | feu tricolore, humidité, température, écouter, appeler | `GET /api/v1/kpis` | #15 |
| 6 | API REST | clé d'API, tableau des routes | — | #16 |

Navigation : 5 entrées maximum, dont 4 visibles en permanence (CDC ENF-U9). L'entrée active porte une barre `--or` à gauche.

**État d'implémentation** : les écrans 2 et 5 sont codés dans `dashboard/app.html` (issues #15 et #21), avec `dashboard/css/app.css` et `dashboard/js/kpis.js`. L'écran 2 consomme `GET /api/v1/kpis` et `GET /api/v1/prices/forecast` ; chaque appel bascule indépendamment sur un jeu de démonstration conforme au contrat si l'API n'est pas joignable. La courbe de prix est rendue en SVG natif (pas de dépendance externe) avec mention « Courbe de démonstration » tant que `is_demo` vaut `true`. Les écrans 1, 3, 4 et 6 restent à intégrer (#8, #14, #16, #22).

---

## 6. Responsive

Point de rupture principal : **820 px** ; ajustement téléphone à **520 px**.

- `> 820 px` : barre latérale fixe de 236 px, contenu décalé (`margin-left`), en-tête collant.
- `<= 820 px` : la barre latérale devient une barre horizontale défilante en haut, le logo texte et le bloc utilisateur sont masqués, la marge gauche du contenu passe à 0, les tableaux défilent horizontalement.
- `<= 520 px` : grilles KPI et graphiques sur une colonne, en-tête autorisé à passer à la ligne, feu producteur réduit à 160 px.

Les zones tactiles respectent `env(safe-area-inset-*)` en haut et en bas (encoches).

---

## 7. Conformité au cahier des charges

| Exigence | Statut |
|---|---|
| Design moderne et responsive (§14) | ✅ |
| Aucune émoticône, icônes Material, Google Fonts (§14) | ✅ |
| Tableaux dynamiques aux couleurs soignées (§14) | ✅ (maquette : `<table>` ; cible : jQWidgets) |
| CRUD en modales (§14) | ✅ |
| Toast de confirmation après chaque action (§14) | ✅ |
| Interface producteur zéro-texte, vert/orange/rouge (§14) | ✅ |
| Champ mot de passe avec œil (§13) | ✅ |
| Focus clavier visible | ✅ depuis `dashboard/css/app.css` (`:focus-visible`, lien d'évitement) |
| `prefers-reduced-motion` | ✅ depuis `dashboard/css/app.css` |
| Contraste AA | ✅ vérifié : `--gris` sur `--fond` = 5,4:1 ; texte blanc sur `--or` corrigé en encre sur `--mod` = 5,5:1 ; blanc sur `--ok` = 4,7:1 ; blanc sur `--ko` = 6,3:1 |

Les trois points d'accessibilité sont traités dans `dashboard/css/app.css` (issue #15) : la maquette reste la référence visuelle, mais le code ajoute le focus visible, le respect de `prefers-reduced-motion` et le correctif de contraste de la pastille « modéré ». La page KPIs ajoute aussi une alternative textuelle aux graphiques (`<details>` avec le tableau des valeurs) et des noms accessibles aux boutons de la vue producteur.

---

## 8. Écarts entre la maquette et le backend actuel

À trancher avant d'intégrer le dashboard :

| Écart | Maquette | Backend (PR #25) | Décision proposée |
|---|---|---|---|
| Identifiants de démo | `acheteur@ebolowa.cm` / `demo1234` | alignés (commit `d524467`) | ✅ résolu : `acheteur@ebolowa.cm` (admin) et `lecteur@ebolowa.cm` (acheteur), mot de passe `demo1234` |
| Champs de parcelle | `nom`, `village`, `ha` | `code`, `name`, `location_label` | ajouter `village` et `surface_ha` au modèle `Plot` (#18) |
| Heures > 85 % | saisies dans le formulaire | non stockées | calculées à partir des mesures, en lecture seule (#13) |
| Taux de détection IA | saisi dans le formulaire | non stocké | calculé à partir des mesures, en lecture seule (#13) |
| Graphiques | SVG écrits à la main | — | remplacer par Chart.js (#16) |
| Tableaux | `<table>` statique | — | remplacer par jQWidgets (#16) |
| Température sur la vue producteur | `27 °C` en gros bouton | `climate.temperature_c` est ingéré, mais `/kpis` n'expose pas de moyenne de température | **décision #15** : afficher les **alertes actives** à la place, sans changer le contrat ; si le besoin est confirmé, ajouter `avg_air_temperature_c` à `/kpis` (évolution mineure, contrat §7) |
| CORS | — | absent (revue #25) | ✅ résolu : `CORSMiddleware` activé, origines locales (`localhost`/`127.0.0.1` ports 8000/5500/5173) et `null` pour l'ouverture en `file://` |

---

## 9. Historique

| Version | Date | Auteur | Changement |
|---|---|---|---|
| 1.0 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Extraction des jetons, composants et écrans depuis la maquette `agro-data-maquette.html` |
| 1.1 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Écrans 2 et 5 implémentés (`dashboard/app.html`), accessibilité traitée, écart température documenté (#15) |
| 1.2 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | CORS activé, `geo_enc` en `Text` et chiffré dans la zone brute, `device_id` contraint (revue #25) |
| 1.3 | 10/11/2026 | MEKONTSO Olivier Steve (SM) | Courbe de prix SVG branchée sur `/prices/forecast`, responsive 520 px, mention démonstration (#15, #21) |
