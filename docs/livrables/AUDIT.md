# Audit de fin de projet — AGRO-DATA

| | |
|---|---|
| **Objet** | Vérification indépendante de l'état livré après la clôture du Sprint 4 |
| **Date** | 11/11/2026 |
| **Commit audité** | `886cb29` (`main`, `v-final`) — état avant correctifs, voir §10 |
| **Environnement** | Python 3.10.12, Node 24.21.0, SQLite, Chrome (navigateur intégré) |
| **Méthode** | Rejeu des tests, de la démonstration et des scénarios ; lecture du code, du contrat, des documents ; appels API réels ; rendu du dashboard dans un navigateur |
| **Portée** | Dépôt, backend, dashboard, simulateur, documentation, tags, issues, CI |

> Cet audit n'est pas une revue de code exhaustive ligne à ligne. Il vérifie
> les **affirmations** du dossier final contre ce qui s'exécute réellement.
> Chaque constat cite un fichier, une commande ou une réponse d'API.

---

## 1. Verdict

**Prototype techniquement solide, dossier final non fiable en l'état.**

- La chaîne critique fonctionne : ingestion → Data Lake → pipeline → KPIs →
  courbe de prix → dashboard. Les 95 tests backend et les 17 tests JS passent,
  la démonstration de bout en bout est verte sur une base neuve, et la reprise
  après coupure renvoie bien 24 mesures sans doublon.
- Le code est lisible, documenté, et les limites majeures (IA non entraînée,
  firmware non flashé, prix v2 non spécifié) sont annoncées honnêtement.
- En revanche, **trois engagements ne sont pas tenus** : deux écarts entre le
  contrat §4.6 et l'API réelle, et un tag `v-final` créé alors que l'incrément
  est incomplet, avec un message qui ne liste pas les manques.
- La **documentation de clôture contient des chiffres périmés et des
  contradictions** (92/14 au lieu de 95/17, 24/14 issues, 45 commits, etc.).
  Un lecteur qui vérifie les preuves tombe sur des écarts systématiques.

**Recommandation :** corriger les points P1 (§3.1) et réaligner les documents
avant de présenter le dossier comme « audité ». Le code n'a pas besoin d'être
refondu ; le dossier a besoin d'être remis à jour.

---

## 2. Preuves exécutées

| Commande | Résultat observé |
|---|---|
| `cd backend && ../.venv/bin/python -m pytest -q` | **95 passed**, 5 warnings, 58,9 s |
| `node --test dashboard/js/*.test.js` | **17 pass**, 0 fail |
| `AGRO_API_BASE=http://127.0.0.1:8011 python scripts/demo_e2e.py` | **10 contrôles OK**, base SQLite neuve |
| `python -m simulator --scenario coupure_reseau --hours 48 --send-now` | **24 renvoyées, 0 refusées, 0 en attente** |
| Connexion dashboard + `GET /api/v1/kpis?days=7` | Cartes alimentées : indice 69, humidité 89 %, 1 alerte, 372 kg |
| `gh run list` | Run `43021614544` : succès sur `886cb29` (`main` et `v-final`) |

Le dashboard a été ouvert dans le navigateur intégré : connexion
`acheteur@ebolowa.cm` / `demo1234`, arrivée sur `app.html`, appels
`/api/v1/kpis?days=7` et `/api/v1/prices/forecast?days=7` visibles dans le
réseau, aucune erreur JS (hors polices externes, §3.4).

---

## 3. Constats

### 3.1. P1 — à corriger avant de présenter

#### A1. `DELETE /api/v1/plots/{id}` ne refuse pas une parcelle encore rattachée

Le contrat §4.6 impose : « `DELETE /api/v1/plots/{id}` est refusé (`409`) si des
appareils sont encore rattachés à la parcelle. »

Le routeur supprime sans vérifier (`backend/app/routers/plots.py:83-92`).
Reproduit sur une base neuve :

```text
DELETE /api/v1/plots/1  →  HTTP 204
GET   /api/v1/devices   →  {"device_id":"AMB-P001","plot_id":null,...}
```

L'appareil n'est pas supprimé, mais il perd son rattachement. Le contrat promet
un refus, l'API fait une suppression silencieuse. Le test `test_crud.py` ne
couvre que le cas d'une parcelle sans appareil.

**Correctif :** compter les `Device` liés et lever `409` avant `db.delete`.
Ajouter un test avec un appareil rattaché.

#### A2. La réponse `GET /api/v1/plots` n'expose pas les champs du contrat §4.6

Le contrat documente quatre champs calculés dans la réponse :

| Champ | Contrat §4.6 |
|---|---|
| `hours_above_85` | entier 0 à 168, calculé sur les mesures |
| `ia_detection_rate` | réel 0 à 1, calculé sur les mesures |
| `infestation_index` | entier, RM2 |
| `level` | `faible` / `modere` / `eleve` |

La réponse réelle ne contient que
`id`, `code`, `name`, `location_label`, `village`, `surface_ha`,
`reference_volume_kg` (`backend/app/schemas/crud.py:42-51`). Le dashboard
recalcule ces quatre valeurs côté client (`dashboard/js/metrics.js`), ce qui
masque l'écart à l'écran mais pas dans l'API.

**Conséquence :** un acheteur qui consomme l'API REST — cas prévu par le
critère §17.5 — ne retrouve pas les mêmes champs que le dashboard.

**Correctif :** soit enrichir `PlotRead` avec les champs calculés, soit corriger
le contrat §4.6 pour dire qu'ils sont calculés côté client. La première option
est préférable, car elle rend l'API autonome.

#### A3. Le tag `v-final` est créé alors que l'incrément est incomplet

La consigne était explicite : « Pas de tag `v-final` tant que l'incrément n'est
pas complet ; tags `v2`/`v3` marqués “partiels”. »

Le tag existe et pointe sur `886cb29`, alors que :

- le prix v2 n'est pas spécifié ni implémenté (#20 ouvert) ;
- l'IA n'est pas entraînée (`ai/dataset` vide, #14 ouvert) ;
- le firmware n'est ni compilé ni flashé (#19).

Le message du tag est **une seule ligne** :

```text
AGRO-DATA — livrable final du Sprint 4 (11/11/2026).
```

Il ne dit ni « partiel », ni ce qui est livré, ni ce qui manque. Or
`SPRINT_4_REVIEW.md` §10 affirme : « Son message liste explicitement le livré
et le non-livré » et la rétrospective R4-1 le revendique aussi. C'est faux.

**Correctif :** soit supprimer/renommer le tag (`v4-partiel`), soit le recréer
avec un message qui liste les trois manques. Ne pas le présenter comme
« final » sans cette mention.

#### A4. Les documents de clôture ne sont plus alignés sur l'état réel

Les écarts sont nombreux et systématiques. Ils donnent l'impression que le
dossier a été rédigé avant les dernières livraisons puis partiellement corrigé.

| Document | Ligne | Affirmé | Réel |
|---|---|---|---|
| `SPRINT_4_REVIEW.md` | 11, 63 | 92 tests backend | **95** |
| `SPRINT_4_REVIEW.md` | 11, 79 | 14 tests JS | **17** |
| `SPRINT_4_REVIEW.md` | 49 | 2 terminés, 4 partiels, 1 non commencé | 3 ✅, 3 🟡, 1 ❌ dans le tableau ; **6 fermées, 1 ouverte** au Kanban |
| `SPRINT_4_REVIEW.md` | 46 | #23 « PV de recette absent » ❌ | `PV_RECETTE.md` existe et #23 est **fermée** |
| `SPRINT_4_REVIEW.md` | 146, 196 | 40 des 45 commits | **49 des 56** |
| `SPRINT_4_REVIEW.md` | 186 | 24 / 14 issues | **24 / 21** |
| `SPRINT_4_REVIEW.md` | 187 | 5 sur 7 terminées | **6 sur 7** |
| `SPRINT_4_REVIEW.md` | 188 | 92 + 14 tests | **95 + 17** |
| `SPRINT_4_REVIEW.md` | 189 | 45 commits | **56** |
| `SPRINT_4_REVIEW.md` | 190 | 40 / 3 / 2 | **49 / 3 / 2 (+2 `73EGA`)** |
| `SPRINT_4_REVIEW.md` | 118-119 | `docs/CRITERES_ACCEPTATION.md`, `docs/RITUELS_SCRUM.md`, `docs/RETROSPECTIVES.md` | chemins réels sous **`docs/livrables/`** |
| `SPRINT_4_REVIEW.md` | 120 | 11 issues fermées | **21** |
| `SPRINT_4_REVIEW.md` | 224-226 | message du tag listant livré/non-livré | message d'**une ligne** |
| `PV_RECETTE.md` | 23 | commit `29cfd01` | **`886cb29`** |
| `PV_RECETTE.md` | 57 | 24 hors ligne, **20 renvoyées, 4 doublons refusés** | **24 renvoyées, 0 refusée** (tampon neuf, rejoué) |
| `CRITERES_ACCEPTATION.md` | 20 | 24 renvoyées, 0 doublon | cohérent avec le rejeu |
| `CRITERES_ACCEPTATION.md` | 26 | 40 des 45 commits | **49 / 56** |
| `CRITERES_ACCEPTATION.md` | 26 | 2 PR (#25, fusion du dashboard) | **1 seule PR (#25)** ; le dashboard a été fusionné sans PR |
| `CRITERES_ACCEPTATION.md` | 128 | 14 tests JS | **17** |
| `RETROSPECTIVES.md` | 112 | 14 tests JS | **17** |
| `RETROSPECTIVES.md` | 129 | 40 des 45 commits | **49 / 56** |
| `RETROSPECTIVES.md` | 148, 173 | R4-1 « fait le 10/11 », « reste à pousser » | tag créé le **11/11**, **déjà poussé** |
| `RETROSPECTIVES.md` | 173 | tag « recréé sur l'état fusionné » | pointe sur `886cb29`, pas sur le commit du bloc C (`4598cd1`) |

**Correctif :** mettre à jour ces valeurs une fois, puis vérifier par une
commande (`git rev-list --count`, `git shortlog -sne`, `pytest --collect-only`,
`gh issue list`) avant de figer le dossier.

### 3.2. P2 — importants, non bloquants

#### A5. Le libellé « 24 dernières heures » contredit la fenêtre de 7 jours

`dashboard/js/app.js:157` affiche :

```text
Humidité moyenne 89,0 % — 24 dernières heures
```

Or le dashboard appelle `GET /api/v1/kpis?days=7` (vérifié dans le réseau), et
`avg_air_humidity_pct` est la moyenne sur la fenêtre demandée
(`backend/app/services/indicators.py:190`). Le libellé est donc faux dès que
`days ≠ 1`.

**Correctif :** afficher « 7 derniers jours » (ou la valeur de `days`), ou
demander `days=1` pour cette carte.

#### A6. « 52 % du volume de référence » ne correspond pas au volume affiché

Sur la base auditée, `/api/v1/kpis` renvoie :

```json
{
  "estimated_healthy_volume_kg": 372.0,
  "estimated_healthy_volume_pct": 52
}
```

La parcelle a `reference_volume_kg = 1200`. Le dashboard affiche
« 372 kg — 52 % du volume de référence ». Or `372 / 1200 = 31 %`, pas 52 %.

Les deux KPI suivent deux formules différentes dans le contrat §4.4 :
`pct = max(20, 100 − 0,7 × indice)` et
`kg = référence × (1 − indice / 100)`. Ils ne sont pas censés coïncider, mais
le libellé les présente comme liés.

**Correctif :** soit afficher le pourcentage calculé à partir du kg
(`kg / référence`), soit libeller « 52 % (estimation ICCO) » et non
« du volume de référence ». Le plus simple est de calculer le pourcentage
affiché à partir de `estimated_healthy_volume_kg`.

#### A7. Compte de démonstration hors ligne non documenté et mot de passe en clair

`dashboard/js/auth.js:13-16` contient deux comptes codés en dur :

```js
{ email: "admin@agrodata.local", password: "Admin2026!", ... },
{ email: "acheteur@agrodata.local", password: "Acheteur2026!", ... },
```

`dashboard/index.html:90` affiche le premier sur l'écran de connexion :
« Hors ligne (backend arrêté) · admin@agrodata.local · Admin2026! ».

Ce compte ne figure ni dans le contrat §4.8, ni dans le README, ni dans les
deux comptes alignés sur la maquette. Il s'agit d'un mode de secours côté
client, pas d'une authentification serveur, mais le mot de passe est public et
le compte est présenté à l'utilisateur.

**Correctif :** soit supprimer ce compte de secours, soit le documenter
explicitement comme « démonstration hors ligne, sans accès serveur » et le
retirer de l'écran de connexion. Ne pas le laisser passer pour un compte réel.

#### A8. Secrets par défaut utilisables sans garde-fou

`backend/app/config.py:17-30` définit des valeurs par défaut pour
`JWT_SECRET`, `AGRO_AES_KEY` et `DEVICE_API_KEY`, reprises dans
`backend/.env.example`. Si `.env` est absent, l'application démarre avec ces
valeurs. Le README prévient qu'il faut les surcharger, mais rien ne bloque le
démarrage.

**Risque :** un déploiement qui oublie `.env` signe des JWT avec un secret
public et chiffre `geo_enc` avec une clé publique. En démonstration locale,
c'est acceptable ; en ligne, c'est une faille.

**Correctif :** ajouter un contrôle au démarrage (refuser les valeurs par
défaut si `ENV=production`), ou au minimum un avertissement bloquant dans les
logs et un test qui vérifie que la configuration de production n'utilise pas
les valeurs de démonstration.

#### A9. La CI ne vérifie qu'une partie de ce qui est livré

`.github/workflows/ci.yml` exécute `pip install`, `compileall backend simulator ai`
et `pytest -q`. Elle ne lance pas :

- `node --test dashboard/js/*.test.js` (17 tests) ;
- `python scripts/demo_e2e.py` (10 contrôles) ;
- un linter Python ou JS ;
- `pip-audit` / `npm audit` ;
- la compilation du firmware (normal, faute d'outil Arduino, mais à documenter).

La CI est verte sur `886cb29`, mais elle ne prouve pas le dashboard ni la
démonstration. Le dossier parle pourtant de « CI verte » comme preuve globale.

**Correctif :** ajouter au minimum un job Node pour les tests JS et un job
`compileall scripts` ; documenter explicitement que le firmware et l'E2E ne
sont pas couverts par la CI.

#### A10. Dépendances non épinglées, pas de scan de vulnérabilités

`backend/requirements.txt` utilise 12 contraintes `>=` et aucun fichier de
verrouillage. Deux installations à des dates différentes peuvent produire des
environnements différents. Aucun `dependabot.yml`, aucun `pip-audit`.

**Correctif :** générer un `requirements.lock` (ou `pip-tools`) et ajouter un
job de scan.

#### A11. Seuil d'alerte : `>= 48 h` alors que le texte dit « plus de 48 h »

`backend/app/services/infestation.py:81` :

```python
return hours_above_85 >= ALERT_DURATION_HOURS
```

Le CDC §17.3 dit « pendant plus de 48 h » et le contrat §4.4 « plus de 48 h
consécutives ». Avec des mesures horaires, 48 mesures couvrent 48 h ; le
48<sup>e</sup> point déclenche l'alerte, alors qu'un strict « plus de 48 h »
demanderait 49 mesures. Le test `test_alerte_apres_48h_au_dessus_de_85` fige
le comportement actuel.

**Correctif :** trancher explicitement dans le contrat (« 48 h ou plus ») ou
passer à `> 48`. En l'état, le texte et le code ne disent pas la même chose.

#### A12. `humidity_delta_7d` dépend du paramètre `days`

`backend/app/services/indicators.py:199-213` calcule l'écart sur `days` jours
(défaut 7) mais le champ s'appelle toujours `humidity_delta_7d`. Un appel
`?days=1` renvoie un écart sur 1 jour sous un nom qui promet 7 jours.

**Correctif :** soit figer la fenêtre à 7 jours pour ce champ, soit le renommer
`humidity_delta` et documenter la fenêtre.

#### A13. Le volume sain ignore les parcelles sans mesure dans la fenêtre

`backend/app/services/indicators.py:194-197` ne parcourt que les groupes issus
des mesures. Une parcelle suivie mais sans mesure sur la fenêtre ne contribue
pas à `estimated_healthy_volume_kg` (0 kg), alors que le contrat dit « somme,
par parcelle, de `reference_volume_kg × (1 − indice / 100)` » — avec un indice
0, elle devrait contribuer à 100 % de son volume.

**Correctif :** inclure toutes les parcelles dans la somme, avec un indice 0
quand il n'y a pas de mesure, ou documenter l'exclusion.

### 3.3. P3 — mineurs et hygiène

- **A14.** `backend/app/services/pricing.py:10-12` parle encore de
  « 1085 FCFA/kg à l'indice 62 donne 1186 », alors que la référence est
  `1050`. Commentaire périmé.
- **A15.** `backend/tests/test_contract.py` ne valide que l'exemple
  d'ingestion §3.1 et l'exemple rejeté §5. Les modèles de lecture §4.4 à §4.8
  ne sont pas comparés au document : c'est précisément ce qui a laissé passer
  A2.
- **A16.** La branche `main` n'est pas protégée (`gh api .../protection` →
  `Branch not protected`). Les commits directs sont possibles, ce que le
  dossier assume par ailleurs (§9.1).
- **A17.** Pas de fichier `LICENSE`. Pour un dépôt public, c'est une ambiguïté
  juridique, même pour un projet de cours.
- **A18.** Le dashboard charge les polices depuis `fonts.gstatic.com`
  (erreurs `ERR_TUNNEL_CONNECTION_FAILED` hors ligne). Les bibliothèques JS
  sont vendorisées, mais pas les polices : la promesse « démo hors ligne » est
  partielle. Un repli local existe, donc ce n'est pas bloquant.
- **A19.** L'indice entier est affiché « 69,0 » (`formatNumber` par défaut à
  une décimale). Cosmétique.
- **A20.** Milestones encore ouverts : Sprint 2 (0 issue ouverte, à clore),
  Sprint 3 (2 ouvertes : #14, #17), Sprint 4 (1 ouverte : #20). #20 mélange
  E2E, bascule IA, prix v2 et tag : l'E2E et le tag sont faits, le prix v2 non.
  Il faudrait la scinder ou la fermer avec une réserve explicite.
- **A21.** `ensure_not_duplicate` fait un `SELECT` puis un `INSERT` ; la
  contrainte unique `(device_id, timestamp)` protège la base, mais une course
  concurrente produirait une `IntegrityError` (500) au lieu du 422 prévu. Non
  reproduit ; à traiter si l'ingestion devient concurrente.
- **A22.** Les tags `v2` et `v3` ont été créés le 10/11, après leurs échéances
  (28/10 et 04/11). La rétrospective l'assume (« en retard »), mais le message
  du tag ne porte pas la date de création réelle.

---

## 4. Écarts contrat ↔ API (synthèse)

| Élément | Contrat | Réel | Gravité |
|---|---|---|---|
| `DELETE /plots/{id}` avec appareil | `409` | `204`, appareil détaché | P1 |
| Champs de `GET /plots` | 11 champs dont 4 calculés | 7 champs, calcul côté client | P1 |
| `active_alerts` | « plus de 48 h » | `>= 48 h` | P2 |
| `humidity_delta_7d` | écart 7 jours | écart sur `days` | P2 |
| `estimated_healthy_volume_kg` | toutes les parcelles | parcelles avec mesures seulement | P2 |
| `GET /plots` — champs `hours_above_85`, etc. | lecture seule exposée | absents de l'API | P1 |
| Comptes de démo | 2 comptes | 2 + 1 compte hors ligne non documenté | P2 |

Le contrat §3 (ingestion) est, lui, correctement aligné : `device_id` contraint,
`timestamp` en secondes, sous-objets `climate` / `diagnostic_ia`, `geo_enc`
chiffré avant écriture dans la zone brute. Le test `test_contract.py` le
vérifie.

---

## 5. Ce qui est solide

- **Tests réels et reproductibles** : 95 backend, 17 JS, 10 contrôles E2E. Les
  tests couvrent l'ingestion, le pipeline, la sécurité, les KPIs, le prix, le
  diagnostic, le CRUD et le Store-and-Forward.
- **Sécurité de base correcte** : Argon2 pour les mots de passe, JWT signé,
  `geo_enc` chiffré en AES-256-GCM dans la zone brute, `device_id` contraint
  contre le path traversal, noms de fichiers nettoyés, rate limiting, CORS
  limité aux origines locales.
- **Dashboard fonctionnel** : connexion, cartes, graphiques Chart.js, grilles
  jQWidgets, CRUD, toasts, thème clair/sombre mémorisé, vue terrain. Vérifié
  dans le navigateur, sans erreur JS.
- **Store-and-Forward crédible** : tampon JSON Lines, réécriture atomique,
  arrêt sur échec temporaire, abandon des 422, reprise sans doublon. La
  reproduction donne 24/0/0.
- **Documentation abondante et honnête sur les limites** : le contrat, le
  design system, les reviews, les rétrospectives et le PV disent clairement
  que l'IA est un stub, que le firmware n'est pas flashé et que le prix v2
  n'est pas fait. C'est un point fort rare.
- **Hygiène Git** : `main` propre et synchronisé, 56 commits, tags annotés et
  poussés, CI verte sur le commit audité, pas de fichier sensible suivi
  (`.env`, `.db`, Data Lake brut, `.venv` sont ignorés).

---

## 6. Traçabilité et processus

| Point | État | Commentaire |
|---|---|---|
| Issues fermées avec preuve | 21 / 24 | #14, #17, #20 ouvertes |
| #14 IA | ouverte | justifié : modèle non entraîné, dataset vide |
| #17 validation PO | ouverte | justifié : PO indisponible |
| #20 E2E / prix v2 / tag | ouverte | E2E et tag faits, prix v2 non spécifié : à scinder |
| Milestone Sprint 2 | ouvert, 0 issue ouverte | à clore |
| Milestone Sprint 3 | ouvert, 2 ouvertes | #14, #17 |
| Milestone Sprint 4 | ouvert, 1 ouverte | #20 |
| Enseignant `@Metili` | spectateur | aucune issue assignée, conforme |
| Dates de sprint | non décalées | 28/10, 04/11, 11/11 respectées |
| PR | 1 seule (#25) | dashboard fusionné sans PR, assumé §9.2 |
| Commits directs sur `main` | 49 / 56 par le SM | écart de traçabilité assumé §9.1 |
| Branche `main` protégée | non | aucune règle de protection |

Le critère §17.8 (« l'historique Git montre le travail de chaque membre »)
reste **partiel**, et le dossier le dit. C'est honnête, mais cela signifie que
le projet ne peut pas revendiquer une conformité complète au CDC sur ce point.

---

## 7. Plan d'action priorisé

### Avant de présenter (P1)

1. **A1** — Ajouter le contrôle `409` sur `DELETE /plots` + test avec appareil
   rattaché.
2. **A2** — Enrichir `PlotRead` avec `hours_above_85`, `ia_detection_rate`,
   `infestation_index`, `level` (ou corriger le contrat §4.6 et l'assumer).
   Ajouter un test de contrat sur les modèles de lecture §4.4-4.8.
3. **A3** — Recréer le tag `v-final` avec un message listant les trois manques,
   ou le renommer `v4-partiel`. Ne pas le présenter comme complet.
4. **A4** — Réaligner `SPRINT_4_REVIEW.md`, `PV_RECETTE.md`,
   `CRITERES_ACCEPTATION.md` et `RETROSPECTIVES.md` sur les chiffres réels
   (95/17, 24/21, 56 commits, 49/3/2/2, 6/7 Sprint 4, chemins
   `docs/livrables/`, commit `886cb29`).

### Juste après (P2)

5. **A5/A6** — Corriger les deux libellés du dashboard (fenêtre de 7 jours,
   pourcentage du volume).
6. **A7** — Supprimer ou documenter le compte hors ligne `admin@agrodata.local`.
7. **A8** — Garde-fou sur les secrets par défaut.
8. **A9/A10** — Ajouter les tests JS et le scan de dépendances à la CI ;
   verrouiller les dépendances.
9. **A11/A12/A13** — Trancher le seuil 48 h, la fenêtre de
   `humidity_delta_7d` et le périmètre du volume sain.

### Hygiène (P3)

10. **A14-A22** — Commentaire de prix, test de contrat des lectures, protection
    de `main`, `LICENSE`, polices locales, affichage de l'indice, milestones,
    course sur les doublons.

---

## 8. Ce que cet audit ne couvre pas

- **Le firmware** : `firmware/agro_node/agro_node.ino` n'a été ni compilé ni
  flashé. Aucune conclusion matérielle n'est possible.
- **L'IA** : le modèle n'est pas entraîné, `ai/dataset` est vide. La route
  répond en mode démonstration déterministe ; aucune précision n'est mesurée.
- **Le Kanban GitHub Project** : l'état des colonnes n'a pas été inspecté
  directement ; seuls les issues et milestones l'ont été.
- **La charge et la concurrence** : les tests sont séquentiels ; le
  comportement sous plusieurs boîtiers simultanés n'est pas validé.
- **La sécurité offensive** : pas de test d'intrusion, pas de scan de
  dépendances, pas de revue cryptographique.

---

## 9. Conclusion

Le projet est **livrable et démontrable** : la chaîne fonctionne, les tests
passent, le dashboard s'affiche et le Store-and-Forward tient sa promesse. Le
travail technique est réel et le dossier assume ses limites.

Il n'est pas **audité au sens strict** tant que les points P1 ne sont pas
corrigés : l'API ne respecte pas deux clauses du contrat §4.6, le tag
`v-final` contredit la consigne, et les documents de clôture annoncent des
chiffres qui ne correspondent plus au dépôt. Ce sont des corrections courtes,
sans refonte : quelques dizaines de lignes de code, un test, un tag recréé et
une passe de mise à jour documentaire.

Une fois ces points traités, le dossier pourra être présenté comme
« prototype accepté avec réserves », ce qui est déjà la formulation du
`PV_RECETTE.md` §8.

---

## 10. Correctifs appliqués (12/11/2026)

Les constats P1 et P2 ont été corrigés après l'audit, sur la base du commit
`886cb29`. Chaque correctif est accompagné de sa preuve exécutable ; les
documents de clôture ont été réalignés sur l'état final.

| Constat | Correctif | Preuve |
|---|---|---|
| A1 | `DELETE /api/v1/plots/{id}` répond `409` si un appareil est rattaché | `test_crud.py` ; vérifié en direct : `HTTP 409 {"detail":"1 appareil(s) encore rattaché(s) à cette parcelle"}` |
| A2 | `PlotRead` expose `hours_above_85`, `ia_detection_rate`, `infestation_index`, `level` via `plot_indicators()` | `test_crud.py`, `test_contract.py` ; `GET /plots` vérifié en direct |
| A3 | Tag renommé **`v4-partiel`**, message annoté listant livré / non-livré | `git tag -n99 v4-partiel` |
| A4 | `SPRINT_4_REVIEW`, `PV_RECETTE`, `CRITERES_ACCEPTATION`, `RETROSPECTIVES`, `README`, `RITUELS_SCRUM`, `PLAN_DE_CODAGE` réalignés (106/18 tests, 24/21 issues, 58 commits, 51/3/2/2, 4 ✅/3 🟡) | relecture + `git log` |
| A5 | Libellé « 7 derniers jours » au lieu de « 24 dernières heures » | rendu navigateur |
| A6 | « 31 % du volume de référence » (372/1200) au lieu de 52 % | rendu navigateur |
| A7 | Comptes hors ligne alignés sur le contrat §4.8 : `acheteur@ebolowa.cm` / `lecteur@ebolowa.cm`, mot de passe `demo1234` ; `admin@agrodata.local` supprimé | `auth.test.js`, `demo-data.js` |
| A8 | `Settings.validate_production_settings()` refuse les secrets par défaut si `APP_ENV=production` | `test_config.py` |
| A9 | CI à quatre jobs : `backend`, `dashboard`, `demonstration`, `audit-dependances` ; `compileall` étendu à `scripts` | `.github/workflows/ci.yml`, run CI vert |
| A10 | Dépendances épinglées (`backend/requirements.txt`), `pip-audit` informatisé, `.github/dependabot.yml` | `pip install -r` reproductible |
| A11 | Seuil tranché : « 48 h ou plus » (`>=`) documenté au contrat §4.4 | `test_kpis.py` (48 h oui, 47 h non) |
| A12 | `humidity_delta_7d` comparé aux 7 jours précédant la fenêtre, indépendamment de `days` | `test_kpis.py` |
| A13 | Volume sain inclut toutes les parcelles, indice 0 sans mesure | `test_kpis.py` |
| A15 | `test_contract.py` valide les modèles de lecture §4.4 à §4.7 | `pytest -q` |

### État final vérifié

| Commande | Résultat |
|---|---|
| `cd backend && ../.venv/bin/python -m pytest -q` | **106 passed** |
| `node --test dashboard/js/*.test.js` | **18 pass**, 0 fail |
| `AGRO_API_BASE=http://127.0.0.1:8011 python scripts/demo_e2e.py` | **10 contrôles OK**, exit 0 |
| `gh run list` | CI verte sur le commit de livraison |

### Points restés ouverts (hors périmètre de l'audit)

- **Validation PO** : #14, #17 et #20 restent ouvertes ; milestones Sprint 2/3/4
  encore `open`. Le PV de recette est signé par le SM mandaté.
- **IA non entraînée** (§17.4) : `ai/dataset` vide, route en `is_demo: true`.
- **Firmware** : écrit, non compilé ni flashé.
- **Prix v2** : non spécifié par le PO ; seule la formule v1 est exposée.
- **Historique Git** (§17.8) : 51 des 58 commits de `main` sont du SM ; critère
  partiel, assumé et documenté en `SPRINT_4_REVIEW.md` §9.
