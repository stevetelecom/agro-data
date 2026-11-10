# Cahier des charges - AGRO-DATA (AgroData-DaaS)

| | |
|---|---|
| Version | 1.0 |
| Date | 24 octobre 2026 |
| Cours | GSA 712 / GSI 712 - Construire une Équipe Projet (ESTLC) |
| Enseignant | METILI Donatien |
| Scrum Master | MEKONTSO Olivier Steve (également développeur) |
| Product Owner | MESSANGA MESSANGA Mike |
| Équipe de développement | NTEINTIE Mounpain, NTYAM Angue, NKWANE Mourad, NEGOUE Patrick, MEKONTSO Olivier Steve |
| Livrable final | 11 novembre 2026 |

Les éléments marqués **[Hypothèse]** sont des propositions de l'équipe, à valider par le Product Owner et, si besoin, par l'enseignant.

---

## 1. Présentation du projet

AGRO-DATA est un service numérique d'intelligence d'affaires agricole fondé sur le modèle **Data-as-a-Service (DaaS)**. Il mesure en continu les conditions microclimatiques sous la canopée de cacaoyères de la commune d'Ambam (Cameroun), détecte et anticipe la pourriture brune des cabosses, puis vend aux acheteurs urbains (Ebolowa, Yaoundé) des indicateurs et des courbes de prix prédictives.

## 2. Contexte et problématique

- Ambam est le deuxième bassin de production cacaoyère du Cameroun en volume.
- La pourriture brune, causée par *Phytophthora megakarya*, détruit jusqu'à 80 % des récoltes lors des pics d'humidité de la saison des pluies. Une cabosse touchée est perdue à 100 %.
- Au-delà de 85 % d'humidité relative, la maladie se propage très vite : une plantation peut passer de saine à fortement infestée en moins de 7 jours.
- Les acheteurs urbains déplacent leurs camions sans visibilité sur les volumes réellement disponibles (pistes dégradées, carburant coûteux).
- Il existe donc une asymétrie d'information entre la production rurale et le marché urbain, qui favorise la spéculation sur les prix et maintient les producteurs dans la précarité.

## 3. Objectifs

### 3.1 Objectif général
Concevoir un service DaaS qui prédit le risque d'infestation, réduit l'asymétrie d'information et aide les producteurs à agir.

### 3.2 Objectifs spécifiques
| ID | Objectif |
|---|---|
| OBJ-1 | Prédire le risque d'infestation en mesurant en continu les facteurs microclimatiques. |
| OBJ-2 | Centraliser les indicateurs sanitaires dans un Data Lake serveur pour anticiper les prix du marché. |
| OBJ-3 | Aider les cultivateurs par des alertes de pulvérisation ciblée et préventive. |
| OBJ-4 | Fournir aux acheteurs un tableau de bord et une API fiables, sous abonnement sécurisé. |

### 3.3 Objectifs pédagogiques (cours GSA 712 / GSI 712)
Montrer la construction et le fonctionnement d'une équipe Scrum : rôles, répartition des tâches, gouvernance, communication, outils collaboratifs, progression visible sprint après sprint.

## 4. Parties prenantes et public cible

| Partie prenante | Rôle | Besoin principal |
|---|---|---|
| Producteurs d'Ambam | Fournisseurs de données brutes | Dispositif automatisé, interface « zéro-texte », alertes simples |
| Acheteurs et exportateurs (Ebolowa, Yaoundé) | Clients finaux du DaaS | KPIs clairs, graphiques, courbes de prix, accès API |
| Coopératives | Propriétaires ou gardiens des boîtiers | Matériel protégé contre le sabotage |
| Product Owner (Mike) | Porte la vision produit | Backlog priorisé, livrables validés |
| Enseignant (METILI Donatien) | Évaluateur | Respect des délais, progression visible, prototype |
| Autorités et régulateurs (ART, CICC) | Cadre réglementaire | Non-spéculation abusive, conformité Loi n° 2010/012 |

## 5. Périmètre

### 5.1 Dans le périmètre du prototype (11 novembre 2026)
- Acquisition de données (matériel réel si disponible, sinon simulateur fidèle au format JSON).
- Stockage tampon local de type MicroSD (Store-and-Forward), même émulé.
- API d'ingestion, pipeline de nettoyage, Data Lake simplifié.
- Calcul de l'Indice d'Infestation Global et d'une courbe de prix prédictive simple.
- Prototype IA de détection de la pourriture brune, exécuté sur PC.
- Dashboard web sécurisé avec KPIs, graphiques, tableau de données et gestion (CRUD).
- API REST documentée pour les acheteurs.

### 5.2 Hors périmètre du prototype
- Déploiement massif de boîtiers sur le terrain.
- Entraînement du modèle IA sur des milliers d'images terrain.
- Paiement en ligne des abonnements.
- Application mobile native.

## 6. Architecture fonctionnelle : trois blocs, trois incréments

```
[ INCRÉMENT 1 : BLOC C ] --> [ INCRÉMENT 2 : BLOC A ] --> [ INCRÉMENT 3 : BLOC B ]
 Acquisition et matériel      Traitement et Data Lake     Restitution et Dashboard
 (DHT22, caméra, MicroSD)     (PC puis serveur)           (Web et API pour acheteurs)
```

- **Bloc C** : capture des données et écriture locale résiliente.
- **Bloc A** : nettoyage, diagnostic IA, indice d'infestation, courbes de prix. Le traitement est d'abord fait sur un PC simulant le serveur, puis bascule sur le serveur central.
- **Bloc B** : portail web (dashboard) et API REST pour les acheteurs.

## 7. Besoins fonctionnels détaillés

### BF1 - Acquisition automatisée (Bloc C)
| ID | Exigence |
|---|---|
| BF1.1 | Mesurer la température et l'humidité de l'air toutes les heures. |
| BF1.2 | Mesurer l'humidité du sol toutes les heures. |
| BF1.3 | Capturer une image de la cabosse à une fréquence configurable. **[Hypothèse]** 1 image par jour par défaut. |
| BF1.4 | Horodater chaque mesure (timestamp entier en secondes). |
| BF1.5 | Associer chaque mesure à un identifiant d'appareil géolocalisant la parcelle. |
| BF1.6 | Écrire chaque mesure sur la carte MicroSD avant toute transmission. |
| BF1.7 | Transmettre les mesures au serveur dès que la connexion est disponible. |

### BF2 - Analyse IA (Bloc A)
| ID | Exigence |
|---|---|
| BF2.1 | Phase prototype : exécuter le diagnostic sur un PC servant de centre de traitement local. |
| BF2.2 | Détecter par vision artificielle les taches de pourriture brune sur la cabosse. |
| BF2.3 | Produire un drapeau binaire (1 détecté, 0 sain) et un score de confiance. |
| BF2.4 | Phase finale : exécuter le même diagnostic sur le serveur central. |
| BF2.5 | Rendre le seuil de détection configurable. |

### BF3 - Traitement Data Lake (Bloc A)
| ID | Exigence |
|---|---|
| BF3.1 | Ingérer les messages JSON envoyés par les appareils. |
| BF3.2 | Nettoyer les flux : filtrer les anomalies de connexion rurale, doublons, valeurs hors plage. |
| BF3.3 | Appliquer une corrélation statistique croisée entre humidité et diagnostic IA. |
| BF3.4 | Calculer l'Indice d'Infestation Global (voir section 12). |
| BF3.5 | Si l'humidité dépasse 85 % pendant plus de 48 h, anticiper la baisse de volume sain sous 7 jours et réajuster les courbes de prix prédictives. |
| BF3.6 | Générer des alertes de pulvérisation ciblée pour les producteurs. |
| BF3.7 | Journaliser les calculs de prix pour audit anti-spéculation. |

### BF4 - Visualisation web (Bloc B)
| ID | Exigence |
|---|---|
| BF4.1 | Authentification et accès par abonnement sécurisé. |
| BF4.2 | Afficher les KPIs : indice d'infestation, humidité moyenne, nombre d'alertes, volume sain estimé. |
| BF4.3 | Afficher des graphiques d'évolution (humidité, indice, prix prédictif). |
| BF4.4 | Afficher un tableau dynamique des mesures et des parcelles. |
| BF4.5 | Gérer les parcelles, appareils et abonnés (création, lecture, modification, suppression) dans des fenêtres modales. |
| BF4.6 | Afficher une notification de confirmation à chaque action validée. |
| BF4.7 | Exposer les données via une API REST documentée. |
| BF4.8 | Interface responsive (ordinateur, tablette, téléphone). |

## 8. Besoins non fonctionnels

| ID | Catégorie | Exigence |
|---|---|---|
| BNF1 | Résilience réseau | Stratégie Store-and-Forward sur MicroSD : sauvegarder 100 % des données en cas de coupure internet. |
| BNF2 | Sécurité physique | Architecture sectorisée IP66 : boîtier principal fixé hors de portée à 2,5 m, capteurs déportés sous gaine en acier blindé flexible. |
| BNF3 | Conformité légale | Chiffrer en AES-256 les métriques géospatiales et d'identification (Loi n° 2010/012 sur la cybersécurité). |
| BNF4 | Ergonomie | Temps d'exécution par tâche inférieur à 60 secondes pour l'utilisateur terrain. |
| BNF5 | Sécurité applicative | Validation de toutes les entrées, protection contre l'injection SQL et le XSS, mots de passe hachés, jetons d'authentification, HTTPS. |
| BNF6 | Performance | Affichage du dashboard en moins de 3 secondes sur connexion standard. **[Hypothèse]** |
| BNF7 | Maintenabilité | Code structuré en modules, commenté, versionné sur Git, testé. |
| BNF8 | Fiabilité | Aucune perte de message : toute mesure acceptée est persistée ou rejetée avec une erreur explicite. |
| BNF9 | Autonomie énergétique | Boîtier alimenté sans réseau électrique (solaire et batterie). |

## 9. Contraintes

- **Délai** : version finale le 11 novembre 2026, une version du livrable chaque semaine (28 octobre, 4 novembre, 11 novembre).
- **Équipe** : 5 développeurs (dont le Scrum Master) et 1 Product Owner, étudiants en 4e année.
- **Légale** : Loi n° 2010/012 du 21 décembre 2010 sur la cybersécurité et la cybercriminalité au Cameroun. Audit des prix prédictifs pour la non-spéculation (directives ART et CICC).
- **Terrain** : zone rurale à connectivité intermittente, humidité élevée, risque de vol et de sabotage.
- **Budget** : à chiffrer par l'équipe avec les prix locaux (aucun budget n'est fixé à ce jour).

## 10. Liste du matériel

### 10.1 Matériel du boîtier d'acquisition (Bloc C)

| Réf. | Composant | Rôle | Qté | Statut |
|---|---|---|---|---|
| M01 | Carte ESP32-CAM (modèle AI-Thinker, caméra OV2640 et lecteur MicroSD intégrés) | Microcontrôleur, caméra et stockage local | 1 par boîtier | Obligatoire |
| M02 | Adaptateur USB-série pour ESP32-CAM (ou carte de programmation dédiée) | Programmer l'ESP32-CAM | 1 pour l'équipe | Obligatoire |
| M03 | Capteur DHT22 (AM2302) | Température et humidité de l'air | 1 | Obligatoire |
| M04 | Capteur d'humidité du sol capacitif | Humidité du sol | 1 | Obligatoire |
| M05 | Carte MicroSD 16 à 32 Go, classe 10, formatée FAT32 | Tampon Store-and-Forward | 1 | Obligatoire |
| M06 | Module horloge temps réel DS3231 | Horodatage fiable hors réseau | 1 | Recommandé |
| M07 | Module GSM/4G (par exemple SIM800L ou SIM7600) et carte SIM avec forfait data | Transmission en zone sans Wi-Fi | 1 | Obligatoire en production, remplaçable par Wi-Fi en laboratoire |
| M08 | Panneau solaire 5 à 6 V | Alimentation | 1 | Obligatoire en production |
| M09 | Batterie Li-ion 18650 et support | Stockage d'énergie | 1 à 2 | Obligatoire en production |
| M10 | Module de charge solaire (par exemple TP4056 avec protection) et régulateur 5 V | Gestion de la charge | 1 | Obligatoire en production |
| M11 | Boîtier étanche IP66 avec presse-étoupes | Protection du boîtier principal | 1 | Obligatoire |
| M12 | Gaine métallique flexible en acier blindé et raccords | Protection des câbles des capteurs déportés (anti-sabotage) | 2 à 3 m | Obligatoire |
| M13 | Mât ou support de fixation à 2,5 m, colliers, visserie inox | Fixation hors de portée | 1 | Obligatoire |
| M14 | Câbles, fils Dupont, breadboard, résistance de rappel 10 kΩ, connecteurs étanches | Câblage et prototypage | 1 lot | Obligatoire |

### 10.2 Outillage
- Multimètre, fer à souder et étain, pince à dénuder, tournevis.
- Câble USB et alimentation de laboratoire 5 V.

### 10.3 Équipement informatique
- Un PC de traitement local pour la phase prototype (au moins 8 Go de RAM, carte graphique utile mais non obligatoire).
- Un smartphone ou un appareil photo pour constituer un jeu d'images de cabosses.
- Un compte GitHub par membre, `gh` (GitHub CLI) et `git` installés.

### 10.4 Alternative sans matériel (simulateur)
Si les composants ne sont pas disponibles avant la démonstration, un **simulateur** logiciel génère les mêmes messages JSON que le boîtier (scénarios sain, humidité critique, coupure réseau). Le reste de la chaîne (API, Data Lake, IA, dashboard) reste identique. Les composants M01 à M05 suffisent pour une démonstration matérielle réelle en laboratoire avec Wi-Fi.

## 11. Logiciels et services

| Domaine | Choix proposé **[Hypothèse, à valider par consensus]** |
|---|---|
| Langages | Python 3.11 ou plus, JavaScript, C++ (Arduino) pour le boîtier |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Base de données | SQLite pour le prototype, PostgreSQL pour la production |
| Sécurité | Argon2 ou bcrypt, JWT, bibliothèque `cryptography` (AES-256-GCM) |
| IA | TensorFlow/Keras (transfert d'apprentissage MobileNetV2), export TFLite possible |
| Frontend | HTML, CSS, JavaScript, jQWidgets (tableaux dynamiques), Chart.js, icônes Material, polices Google Fonts |
| Outils | Git et GitHub (dépôt, Issues, Projects), GitHub Actions (intégration continue) |
| Hébergement | À décider : serveur local pour la démo, service d'hébergement gratuit ou VPS pour la mise en ligne |

## 12. Modèle de données et règles métier

### 12.1 Format d'échange (JSON logique)

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
  "geo_enc": "<champ chiffré AES-256-GCM encodé en base64>"
}
```

| Champ | Type | Description |
|---|---|---|
| `device_id` | chaîne | Identifiant de l'appareil, géolocalise la parcelle |
| `timestamp` | entier | Seconde exacte de la mesure |
| `climate` | objet | Température et humidités (réels) |
| `diagnostic_ia` | objet | 1 si *Phytophthora megakarya* détecté, 0 si sain, et score de confiance |
| `geo_enc` | chaîne | Métriques géospatiales et identifiants chiffrés avant transmission |

### 12.2 Règles métier
- **RM1 - Alerte humidité** : si l'humidité de l'air est supérieure à 85 % pendant plus de 48 heures consécutives, déclencher une alerte et anticiper une baisse du volume sain sous 7 jours.
- **RM2 - Indice d'Infestation Global (0 à 100)** **[Hypothèse]** : `indice = 60 x min(1, heures_au_dessus_de_85 / 48) + 40 x taux_de_détection_IA`, calculé par parcelle puis agrégé. Niveaux : moins de 30 faible, de 30 à 60 modéré, plus de 60 élevé.
- **RM3 - Courbe de prix prédictive** **[Hypothèse]** : prix de référence ajusté à la hausse quand l'indice augmente. Les coefficients sont à calibrer avec des données publiques (ICCO, CICC). Le prototype affiche une courbe de démonstration clairement identifiée comme telle.
- **RM4 - Anomalies** : une mesure est rejetée si elle sort des plages physiques (température, humidité hors de 0 à 100 %), si son horodatage est incohérent ou si elle est en doublon.
- **RM5 - Audit** : chaque calcul de prix est journalisé (entrées, version de la formule, résultat).

## 13. Sécurité

| Menace | Mesure |
|---|---|
| Injection SQL | Requêtes paramétrées via l'ORM, aucune concaténation de SQL |
| XSS | Échappement systématique des sorties, validation des entrées, en-tête CSP |
| Accès non autorisé | Authentification par jeton, rôles (producteur, acheteur, administrateur), clé d'API par appareil |
| Vol de mots de passe | Hachage Argon2 ou bcrypt, champ mot de passe avec icône pour afficher ou masquer la saisie |
| Interception | HTTPS en production |
| Force brute et abus | Limitation du nombre de requêtes par client |
| Sabotage physique | Boîtier IP66 à 2,5 m, gaine d'acier blindée |
| Fuite de données personnelles | Chiffrement AES-256 des identifiants et des coordonnées, conformité à la Loi n° 2010/012 |

## 14. Interface utilisateur

- Design moderne et responsive, inspiré des interfaces de grandes entreprises.
- Aucune émoticône : icônes Material et polices Google Fonts.
- Tableaux dynamiques animés (jQWidgets) aux couleurs soignées.
- Actions de création, modification et suppression dans des fenêtres modales.
- Notification (toast) de confirmation à chaque action validée.
- Interface producteur « zéro-texte » : pictogrammes, couleurs (vert, orange, rouge) et indicateurs visuels.

## 15. Organisation de l'équipe

| Membre | Rôle Scrum | Compétences fortes |
|---|---|---|
| MEKONTSO Olivier Steve | Scrum Master et développeur | Gestion de projet |
| MESSANGA MESSANGA Mike | Product Owner | Communication |
| NKWANE Mourad | Développeur | Développement |
| NTYAM Angue | Développeur | Design et UX |
| NEGOUE Patrick | Développeur | Design et UX |
| NTEINTIE Mounpain | Développeur | Développement (niveau intermédiaire) |

Compétence manquante identifiée : Data/IA et IoT embarqué. Risque traité par la montée en compétences et le partage des tâches (voir `PLAN_DE_CODAGE.md`).

Rituels : Sprint Planning en début de semaine, Daily Scrum, Sprint Review avec le Product Owner, Rétrospective. Les décisions importantes se prennent par consensus, les arbitrages de priorité par le Product Owner.

## 16. Planning et livrables

| Sprint | Date de livraison | Objectif | Livrable |
|---|---|---|---|
| 2 | 28 octobre 2026 | Fondations : structure du dépôt, contrat JSON, simulateur, squelette API, maquettes | Version 2 du dossier et premier code |
| 3 | 4 novembre 2026 | Traitement : pipeline, indice, prototype IA, authentification | Version 3 du dossier et backend fonctionnel |
| 4 | 11 novembre 2026 | Restitution et intégration : dashboard, API REST, démonstration | Livrable final et prototype complet |

## 17. Critères d'acceptation du prototype

1. Un message JSON conforme part du simulateur ou du boîtier et arrive dans le Data Lake.
2. Une coupure réseau simulée ne fait perdre aucune mesure (reprise de l'envoi au retour du réseau).
3. Une série d'humidité supérieure à 85 % pendant plus de 48 h fait monter l'indice et déclenche une alerte.
4. Le prototype IA retourne un drapeau et un score pour une image de cabosse donnée.
5. Un acheteur se connecte, voit les KPIs, les graphiques et le tableau, et obtient les mêmes données par l'API REST.
6. Les entrées invalides ou malveillantes sont rejetées.
7. Chaque action de gestion affiche une notification de confirmation.
8. L'historique Git montre le travail de chaque membre, sprint après sprint.


## 18. Risques

| Risque | Probabilité | Impact | Réponse |
|---|---|---|---|
| Matériel indisponible ou en retard | Élevée | Moyen | Utiliser le simulateur, matériel en option |
| Manque de compétences IA | Élevée | Moyen | Transfert d'apprentissage, modèle simple, jeu d'images public à vérifier |
| Jeu d'images insuffisant ou mal licencié | Moyenne | Élevé | Vérifier la licence, compléter par des photos de l'équipe |
| Délai trop court (18 jours) | Élevée | Élevé | Tranche verticale minimale, priorisation Must / Should / Could par le PO |
| Conflits d'intégration entre membres | Moyenne | Moyen | Contrat JSON figé en Sprint 2, branches par fonctionnalité, revue avant fusion |
| Coupure de connexion pendant la démonstration | Moyenne | Moyen | Démonstration locale possible, données de secours |

## 19. Glossaire

- **DaaS** : Data-as-a-Service, vente de données et d'indicateurs comme service.
- **Data Lake** : espace de stockage central des données brutes et traitées.
- **Store-and-Forward** : stockage local puis envoi différé des données.
- **IP66** : indice de protection contre la poussière et les jets d'eau puissants.
- **KPI** : indicateur clé de performance.
- **PO / SM** : Product Owner / Scrum Master.
- **ICCO** : Organisation internationale du cacao. **CICC** : Conseil Interprofessionnel du Cacao et du Café. **ART** : Agence de Régulation des Télécommunications.
