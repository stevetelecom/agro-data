# Product Backlog - AGRO-DATA

Priorite : Must / Should / Could. Estimation : S / M / L.

| ID | Source | User story | Bloc | Prio. | Est. |
|---|---|---|---|---|---|
| PB-01 | BF1 | En tant que producteur, je veux que le boîtier mesure chaque heure la température et l'humidité (DHT22). | C (Inc.1) | Must | M |
| PB-02 | BF1 | En tant que producteur, je veux que la caméra capture l'état visuel de la cabosse. | C (Inc.1) | Must | M |
| PB-03 | BNF1 | En tant que producteur, je veux que les données soient stockées sur MicroSD (Store-and-Forward) en cas de coupure internet. | C (Inc.1) | Must | L |
| PB-04 | BNF2 | En tant que coopérative, je veux un boîtier IP66 fixé à 2,5 m avec capteurs sous gaine blindée contre le sabotage. | C (Inc.1) | Should | M |
| PB-05 | BNF3 | En tant qu'exploitant, je veux chiffrer en AES-256 les données géospatiales et d'identification (Loi 2010/012). | C/A | Must | M |
| PB-06 | BF2 | En tant que système, je veux un prototype IA sur PC détectant les taches de pourriture brune. | A (Inc.2) | Must | L |
| PB-07 | BF3 | En tant que système, je veux nettoyer les flux JSON entrants (Data Lake) et filtrer les anomalies réseau. | A (Inc.2) | Must | L |
| PB-08 | BF3 | En tant qu'acheteur, je veux un Indice d'Infestation Global (alerte si humidité > 85 % pendant plus de 48 h). | A (Inc.2) | Must | M |
| PB-09 | BF3 | En tant qu'acheteur, je veux des courbes de prix prédictives réajustées selon l'indice. | A (Inc.2) | Should | L |
| PB-10 | BF2 | En tant que système, je veux basculer le diagnostic IA du PC vers le serveur de production. | A (Inc.2) | Should | L |
| PB-11 | BF4 | En tant qu'acheteur, je veux un Dashboard web affichant les KPIs et graphiques. | B (Inc.3) | Must | L |
| PB-12 | BF4 | En tant qu'acheteur, je veux un accès par abonnement sécurisé. | B (Inc.3) | Should | M |
| PB-13 | BF4 | En tant qu'acheteur, je veux une API REST pour intégrer les données à mes outils. | B (Inc.3) | Should | M |
| PB-14 | Obj. 2.2 | En tant que producteur, je veux des alertes de pulvérisation ciblée. | A/B | Could | M |
| PB-15 | BNF4 | En tant que producteur, je veux accomplir une tâche en moins de 60 secondes (interface « zéro-texte »). | B/C | Could | S |
