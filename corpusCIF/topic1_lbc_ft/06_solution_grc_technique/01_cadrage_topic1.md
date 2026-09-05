# Cadrage Topic 1 - Ce que les équipes doivent livrer

## Demande officielle

La thématique 01 porte sur la conformité LBC/FT/FP dans le système d'information des coopératives financières. L'équipe doit concevoir une solution numérique qui aide les SFD à filtrer les clients et les transactions, repérer les risques et produire des alertes exploitables.

Le briefing précise le sujet ainsi: concevoir une solution de filtrage automatisé des clients et des transactions au regard des listes de sanctions LBC/FT et des profils de Personnes Politiquement Exposées, adaptée aux contraintes techniques et organisationnelles des SFD d'Afrique de l'Ouest.

## Fonctions attendues

- Profilage des clients et des comptes ouverts.
- Filtrage des clients au moment de l'entrée en relation.
- Filtrage en temps réel ou quasi temps réel des transactions.
- Détection des Personnes Politiquement Exposées.
- Suivi des mouvements sur les comptes.
- Génération automatique d'alertes informatives ou bloquantes.
- Calcul du solde global de tous les comptes d'un même client.
- Recensement des opérations effectuées par un client occasionnel ou habituel.
- Identification des opérations suspectes ou inhabituelles.
- Prise en compte rapide des modifications de listes de sanctions ciblées.

## Contraintes non négociables

- Fonctionner sur smartphone Android ou ordinateur Windows.
- Prévoir un mode faible connectivité.
- Utiliser des données synthétiques ou publiques, jamais des données personnelles réelles.
- Versionner et documenter le code avec un README compréhensible.
- Préparer une démonstration live, pas seulement des diapositives.
- Expliquer la construction du jeu de données synthétique.

## Lecture jury

La notation pousse à montrer trois choses en même temps:

- Compréhension métier: obligations LBC/FT/FP, réalité des caisses, limites des SFD.
- Prototype testable: parcours complet, données simulées, alertes visibles, logs.
- Déploiement réaliste: faible connectivité, ressources modestes, gouvernance humaine.

## Angle recommandé

Présenter la solution comme un assistant conformité léger pour SFD:

- Un moteur de filtrage noms, sanctions et PPE.
- Un moteur de règles transactionnelles.
- Un tableau de revue conformité.
- Un journal d'audit.
- Un mécanisme de synchronisation des listes en mode connecté/déconnecté.

L'idée forte à défendre: la solution ne remplace pas le responsable conformité. Elle accélère le tri, documente les décisions et réduit les oublis dans des caisses peu équipées.
