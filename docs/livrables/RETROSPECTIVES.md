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
| R2-4 | Une PR doit être fusionnable à la fin du sprint ; sinon elle est découpée | tous | Sprint 3 | ⚠️ partiellement appliqué (PR #25 fusionnée le 10/11, en retard) |

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

**Tenue le** : 11/11/2026 — section rédigée le 10/11 à partir de l'état du
dépôt, à confirmer en séance.

### Ce qui a marché

- Le backend a été livré en entier et fusionné (PR #25) : 79 tests verts en CI,
  contrat JSON testé, ingestion chiffrée, CRUD, KPIs et prix.
- Les modules métier purs (`infestation`, `pricing`, `pipeline`) ont été
  testables seuls et ont survécu au blocage de la PR, contrairement aux routes.
- Le plan de secours (démo hors ligne sur la maquette) était prêt avant la
  revue : aucune improvisation le jour J.
- Le Kanban a été remis à jour la veille (5 issues fermées avec preuves,
  cases cochées) au lieu de rester décorrélé du code.

### Ce qui n'a pas marché

- **Deux blocs entiers sans code exécutable** : simulateur/boîtier (C) et
  dashboard (B). Les assignés n'ont livré aucun commit utile en quatre
  sprints, et le SM n'a pas escaladé assez tôt (action R3-5 non appliquée).
- **Travail direct sur `main` assumé par le SM** : 33 des 35 commits y sont
  allés directement, sans PR ni revue. Ce n'est pas un oubli mais une pratique
  choisie (seul développeur backend, itérations courtes) ; elle reste un écart
  à la DoD, et le critère §17.8 (historique montrant le travail de chacun) n'est
  pas satisfait. À trancher avec le PO : entériner la pratique dans la DoD ou
  revenir à des branches courtes fusionnées.
- **Le PO n'a validé aucun artefact** depuis le Sprint 2 : contrat, design
  system, critères §17 et PV de recette sont restés en attente jusqu'à la
  veille de la livraison.
- **Le board a menti jusqu'au 10/11** : issues terminées encore ouvertes,
  cases non cochées, statuts obsolètes. Le pilotage s'est fait sur le code, pas
  sur le Kanban.
- Une case de l'issue #20 annonçait une intégration E2E « simulateur → API »
  alors que le simulateur n'existe pas : corrigée le 10/11.

### Actions

| Réf. | Action | Porteur | Échéance |
|---|---|---|---|
| R4-1 | Créer le tag `v-final` avec un message listant explicitement ce qui est livré et ce qui ne l'est pas | SM | ✅ fait le 10/11 |
| R4-2 | Livrer #6, #12, #8 et #22 en PR séparées, avec un test par issue, avant toute nouvelle démonstration | Mounpain, Patrick | prochaine itération |
| R4-3 | Ne plus jamais cocher une case sans preuve exécutable (test, route, capture) | tous | immédiat |
| R4-4 | Obtenir la validation du PO sur le contrat, le design system et les critères §17, ou consigner formellement son absence en Review | PO + SM | 11/11 |
| R4-5 | Découper chaque module en tickets de 2 jours maximum et vérifier l'avancement à mi-sprint, pas à J-1 | SM | prochaine itération |

---

## Suivi des actions

| Action | Sprint d'origine | Statut au 10/11/2026 |
|---|---|---|
| R2-1 tags de sprint | S2 | ✅ fait, en retard |
| R2-2 version provisoire du contrat | S2 | ✅ appliqué |
| R2-3 reprise des modules orphelins | S2 | ✅ appliqué |
| R2-4 PR fusionnable en fin de sprint | S2 | ⚠️ partiel |
| R3-1 trancher la PR #25 | S3 | ✅ fusionnée le 10/11 à 13:16 |
| R3-2 livrer la couche métier seule | S3 | ✅ appliqué |
| R3-3 une PR = un module | S3 | ❌ non appliqué — travail direct sur `main` assumé par le SM |
| R3-4 démo de secours | S3 | ✅ maquette prête (`maquettes/agro-data-maquette.html`) |
| R3-5 suppléant par module | S3 | ❌ non appliqué (blocs B et C sans code) |
| R4-1 tag `v-final` annoté et partiel | S4 | ✅ fait le 10/11 (reste à pousser sur `origin`) |
| R4-2 livrer #6, #12, #8, #22 en PR | S4 | ⏳ prochaine itération |
| R4-3 aucune case cochée sans preuve | S4 | ✅ appliqué le 10/11 (issue #20 corrigée) |
| R4-4 validation PO ou absence consignée | S4 | ⏳ 11/11 |
| R4-5 tickets de 2 jours maximum | S4 | ⏳ prochaine itération |
