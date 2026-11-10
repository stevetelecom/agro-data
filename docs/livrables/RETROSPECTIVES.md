# Rétrospectives — AGRO-DATA

**Auteur** : MEKONTSO Olivier Steve (Scrum Master)
**Références** : `docs/livrables/RITUELS_SCRUM.md` §3, issue #24

Une section par sprint. Chaque rétrospective produit **au plus deux actions
principales**, suivies au sprint suivant. Le format est celui du classique
« ce qui a marché / ce qui n'a pas marché / actions ».

---

## Sprint 2 — Fondations

**Tenue le** : 10/11/2026 (échéance du sprint : 28/10/2026)
**Participants** : Olivier, Mourad, Mounpain, Patrick

### Ce qui a marché

- L'outillage a été posé en une journée : dépôt, arborescence, CI sur toutes
  les branches, 24 issues, labels, milestones, Kanban public. Le suivi est
  immédiatement lisible par l'enseignant.
- Le contrat JSON a été écrit **avant** le code, avec un test qui le compare au
  schéma Pydantic : les échanges entre simulateur, backend et dashboard ne
  peuvent plus diverger silencieusement.
- La maquette est devenue la référence visuelle : les 6 écrans ont servi à
  déduire les modèles de lecture du contrat (§4.4 à §4.8), au lieu de les
  inventer.

### Ce qui n'a pas marché

- **Le PO n'a jamais été disponible.** Le contrat (#4), les critères
  d'acceptation et les jeux de données (#9) sont restés en attente tout le
  sprint. Le contrat a dû être figé en version provisoire.
- **Deux tickets n'ont pas démarré** (#6 simulateur, #8 page de connexion),
  sans raison technique : personne ne les a pris.
- **Une maquette d'un autre projet a été poussée** dans le dépôt (TailleurPro)
  et a dû être retirée.
- **L'historique Git a été consolidé après l'échéance** : les commits du
  Sprint 2 portent la date du 10/11. Le travail est réel, mais la trace
  chronologique ne reflète pas le déroulé.

### Actions

| ID | Action | Responsable | Échéance | Statut |
|---|---|---|---|---|
| R2-1 | Poser un tag annoté à la fin de **chaque** sprint, avec un message qui dit explicitement si l'incrément est complet ou partiel | SM | fin de chaque sprint | ✅ fait le 10/11 (`v2`, `v3`), en retard |
| R2-2 | Ne plus bloquer une livraison sur la disponibilité du PO : figer une version provisoire, la signaler « en attente de confirmation », et la réviser dès son retour | SM | immédiat | ✅ appliqué (contrat v1.0 → v1.2) |
| R2-3 | Le SM reprend les modules dont le titulaire ne livre pas, pour ne pas laisser un ticket orphelin | SM | immédiat | ✅ appliqué (MOD-B1, MOD-B2 repris) |
| R2-4 | Une PR doit être fusionnable à la fin du sprint ; sinon elle est découpée | tous | Sprint 3 | ⚠️ partiellement appliqué (PR #25 toujours ouverte) |

---

## Sprint 3 — Traitement

**Tenue le** : 10/11/2026 (échéance du sprint : 04/11/2026)
**Participants** : Olivier, Mourad

### Ce qui a marché

- La **couche métier de #13 a été isolée** du reste : deux modules purs, 21
  tests, fusionnés dans `main` sans attendre la PR #25. C'est la seule
  livraison du sprint qui ne dépend de personne.
- Le **test de contrat** a fait son travail : en passant le contrat en v1.1
  puis v1.2, on a su exactement quels champs ajouter au schéma.
- Les comptes de démonstration ont été alignés sur la maquette **avant** la
  démo, ce qui évite un échec de connexion le jour J.
- La revue de code de la PR #25 a produit 5 remarques concrètes et
  actionnables (sécurité, CORS, longueur de champ), pas un simple « LGTM ».

### Ce qui n'a pas marché

- **Un seul point de défaillance : la PR #25.** Quatre tickets de deux
  personnes (#13 routes, #15, #16, #20) en dépendent. Elle est en brouillon
  depuis le Sprint 2, et le PO qui devait la valider est absent.
- **Une PR unique pour quatre modules** (ingestion, pipeline, chiffrement,
  CRUD) : 2 000 lignes à relire d'un coup, impossible à fusionner
  partiellement.
- **Le prototype IA (#14) n'a pas démarré** faute de jeu d'images validé.
  C'était prévisible : le risque était identifié dans le cahier des charges
  §18.
- **Aucun ticket fermé sur huit.** Le sprint n'a pas produit d'incrément
  accepté par le PO.

### Actions

| ID | Action | Responsable | Échéance | Statut |
|---|---|---|---|---|
| R3-1 | Trancher explicitement le sort de la PR #25 : fusion, découpage ou attente assumée avec une date. Ne pas laisser un blocage implicite | SM + PO | 10/11 | ✅ tranché le 10/11 : **attente de la validation PO**, blocage assumé et documenté |
| R3-2 | Un ticket qui peut vivre sans les autres ne doit pas attendre : livrer la couche métier séparément de ses routes | SM | immédiat | ✅ appliqué (`add13d4`) |
| R3-3 | Une PR = un module. Au-delà de 400 lignes modifiées, découper | tous | Sprint 4 | ⏳ à appliquer |
| R3-4 | Préparer une **démo de secours** sur données simulées (la maquette) au cas où le backend ne serait pas fusionné le 11/11 | SM | 11/11 | ⏳ en cours |
| R3-5 | Chaque module critique a un suppléant nommé, pour éviter le point de défaillance unique | SM | Sprint 4 | ⏳ à appliquer |

---

## Sprint 4 — Restitution et intégration

**Prévue le** : 11/11/2026

Rétrospective à tenir après la Sprint Review. Les points à examiner, déjà
connus :

- l'issue du blocage PR #25 et son effet sur la démonstration ;
- le respect (ou non) de la règle « une PR = un module » (R3-3) ;
- la qualité de la démo de secours (R3-4) ;
- ce que l'équipe referait différemment sur la répartition des modules.

---

## Suivi des actions

| Action | Sprint d'origine | Statut au 10/11/2026 |
|---|---|---|
| R2-1 tags de sprint | S2 | ✅ fait, en retard |
| R2-2 version provisoire du contrat | S2 | ✅ appliqué |
| R2-3 reprise des modules orphelins | S2 | ✅ appliqué |
| R2-4 PR fusionnable en fin de sprint | S2 | ⚠️ partiel |
| R3-1 trancher la PR #25 | S3 | ✅ tranché (attente PO) |
| R3-2 livrer la couche métier seule | S3 | ✅ appliqué |
| R3-3 une PR = un module | S3 | ⏳ Sprint 4 |
| R3-4 démo de secours | S3 | ⏳ en cours |
| R3-5 suppléant par module | S3 | ⏳ Sprint 4 |
