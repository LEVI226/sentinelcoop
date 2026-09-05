# NOTE DE PRÉSENTATION DE LA SOLUTION

## SentinelleCoop — Filtrage LBC/FT/FP souverain et hors-ligne pour les coopératives financières

**Hackathon National d'Innovation CIF — Projet DigiCoop-WA+**

Thématique 01, Filtrage des clients : conformité LBC/FT/FP en matière de système d'information · Burkina Faso — Ouagadougou (4-6 septembre 2026) · Équipe SentinelleCoop, 4 membres · Chef d'équipe OUEDRAOGO Yannick U. L. — +226 70 85 99 88 — ouedraogoyannick24@gmail.com

---

## 1. Le problème adressé

**Les coopératives financières sont nommément assujetties.** La loi n° 046-2024/ALT du 30 décembre 2024, qui transpose au Burkina Faso la Loi uniforme UMOA de mars 2023, range « les systèmes financiers décentralisés ou institutions de microfinance » parmi les institutions financières soumises à l'intégralité du dispositif : vigilance constante sur toutes les opérations (art. 20), examen particulier des opérations atypiques (art. 21), détection des Personnes Politiquement Exposées (art. 29), déclaration immédiate à la CENTIF (art. 60), mise en œuvre sans délai des sanctions financières ciblées (art. 89), conservation décennale avec reconstitution des opérations (art. 23). Aucun régime allégé n'est prévu au titre de la taille de l'institution. La loi n° 001-2025/ALT sur la microfinance referme le dispositif par le versant système d'information — celui que nomme l'intitulé même de la Thématique 01 : son article 35 impose une « infrastructure informatique qui permet d'assurer la disponibilité, la confidentialité, la qualité, la fiabilité et l'intégrité des données ».

**Le risque n'est pas théorique.** L'Évaluation Nationale des Risques BC/FT (CENTIF / CNCA-LBC/FT, décembre 2025) classe le risque national de blanchiment comme élevé. Le secteur de l'inclusion financière, 124 SFD, 395,3 milliards FCFA d'encours de dépôts, y est évalué à un risque moyennement élevé. Et la charge croît : la BCEAO projette une progression des créances sur l'économie de 7,4 % en 2026. Davantage d'opérations à filtrer, à effectifs de conformité constants. L'écart n'est pas un problème de volonté, mais d'outillage. Quatre causes :

- **Inadaptation phonétique** : les moteurs classiques échouent sur les noms ouest-africains, générant des faux négatifs ou des faux positifs de masse.
- **Dépendance à la connectivité** : les solutions actuelles exigent un accès réseau synchrone, souvent impossible en zone rurale.
- **Coût prohibitif** : les plateformes du marché sont tarifées pour de grandes banques internationales.
- **Manque de traçabilité** : le respect du « sans délai » n'est pas mesuré, rendant la conformité difficile à prouver.

---

## 2. L'approche proposée

SentinelleCoop applique un principe directeur unique : **hors-ligne d'abord**. Le moteur, les listes et les règles résident sur le poste ou le serveur local de la coopérative. Le réseau ne sert qu'à synchroniser les mises à jour, jamais à répondre à une requête de guichet. Coupé du réseau, le système continue de filtrer.

**M1 — Référentiel et synchronisation différentielle.** Agrégation des listes publiques et gratuites (ONU, UE, OFAC), des listes nationales et des PPE internes. Un indicateur permanent affiche l'âge exact du référentiel, par exemple « liste ONU synchronisée il y a 4 minutes », rendant le « sans délai » démontrable.

**M2 — Moteur de correspondance phonétique ouest-africaine.** Basé sur les règles de translittération de l'espace UEMOA. Utilise un double seuil paramétrable : au-delà du seuil haut, l'alerte est bloquante ; entre les deux, elle est informative.

**M3 — Profilage client et consolidation multi-comptes.** Calcul continu du solde global consolidé de l'ensemble des comptes d'un même client, toutes agences confondues, pour détecter le fractionnement.

**M4 — Surveillance comportementale.** Détection de fractionnement, de comptes rebond et de cycles de transferts suspects entre comptes liés.

**M5 — Production automatique des actes de conformité.** Génération automatique des rapports confidentiels et projets de déclaration de soupçon pour la CENTIF.

### Couverture des exigences de la Thématique 01

| Exigence du TDR | Base légale | Module |
|---|---|---|
| Profilage des clients et des comptes | Art. 13 a) et b) | M3 |
| Filtrage en temps réel des clients et des transactions | Art. 20 | M2 |
| Prise en compte des PPE | Art. 29 | M1 + M3 + M5 |
| Suivi des mouvements sur les comptes | Art. 12 d), art. 20 | M4 |
| Alertes automatiques bloquantes ou informatives | Art. 21, art. 91 | M2 + M5 |
| Solde global de l'ensemble des comptes d'un même client | Art. 13 e) | M3 |
| Recensement des opérations par client occasionnel ou habituel | Art. 21 a), art. 23 | M3 |
| Identification des opérations suspectes ou inhabituelles | Art. 13 f), art. 60 | M4 + M5 |
| Sanctions ciblées prises en compte sans délai | Art. 89, art. 124 | M1 |
| Conservation décennale et reconstitution *(non listé au TDR)* | Art. 23 | M5 |
| Contraintes : connectivité limitée, faibles ressources | Art. 12 in fine | Architecture hors-ligne, base embarquée |

L'article 21 a) vise tout paiement dont le « montant unitaire ou total » atteint le seuil fixé : la loi impose explicitement le cumul, et non le seul contrôle opération par opération. C'est ce que le TDR reformule en « recensement des opérations effectuées par un même client », et ce que remplit M3.

---

## 3. Caractère innovant — et sa mesure

**3.1 — L'adaptation phonétique à l'onomastique ouest-africaine.** Notre moteur est calibré pour les noms de l'espace UEMOA. Sur un jeu de test de 99 couples de variantes attestées, filtré contre la liste consolidée réelle des Nations unies, il atteint **94,9 % de détection au seuil bloquant et 99,0 % au seuil informatif, contre 67,7 % pour Soundex**.

| Méthode | Détection | Faux positifs |
|---|---|---|
| Soundex (moteur classique du marché) | 67,7 % | 0,0 % |
| Moteur adapté, seuil bloquant | 94,9 % | 0,1 % |
| Moteur adapté, seuil informatif | 99,0 % | 0,5 % |

L'écart le plus net porte sur la palatalisation — Diallo / Jallo / Djallo — où Soundex détecte 8 % des couples contre 100 % pour le moteur adapté. Le filtrage complet s'exécute en 520 millisecondes, hors ligne, sur un poste standard.

**3.2 — Principes d'innovation :** le hors-ligne d'abord comme choix de conformité. La preuve du « sans délai » par horodatage inaltérable. De la détection à la production des actes réglementaires.

**Ce que nous ne revendiquons pas :** les briques élémentaires sont connues ; notre valeur réside dans leur calibrage spécifique au contexte local et leur architecture soutenable.

---

## 4. Faisabilité technique et plan de développement

**4.1 — Choix techniques.** Base embarquée avec indexation par trigrammes, service applicatif en Python, interface web légère utilisable depuis un poste de guichet modeste. Aucune dépendance à un service en nuage, aucune interface de programmation payante, aucun matériel spécifique.

**4.2 — Disponibilité des données.** Les listes de sanctions internationales sont publiques, gratuites et téléchargeables en formats structurés — le prototype ingère déjà la liste ONU du jour. La démonstration s'appuiera donc sur des données réelles et à jour pour tout le volet filtrage. Seules les données clients et transactionnelles seront simulées, selon des profils réalistes de coopérative. Une limite que nous préférons signaler : notre jeu de 99 variantes est construit à la main, et l'échantillon de bruit provient de la liste ONU, internationalement diverse. Dans un portefeuille ouest-africain réel, où les patronymes se répètent fortement, le taux de faux positifs sera supérieur à 0,5 %. C'est ce que la pondération par rareté vise à contenir ; le calibrage sur un échantillon anonymisé d'une coopérative membre est notre première demande d'accompagnement.

**4.3 — Plan des 72 heures.**

| Phase | Livrable |
|---|---|
| J1 matin | Modèle de données, ingestion ONU / UE / OFAC, normalisation |
| J1 après-midi | Première version du moteur, indexation, jeu de test de noms |
| J2 matin | Encodage phonétique ouest-africain, calibrage des seuils, mesure face au Soundex de référence |
| J2 après-midi | Profilage client, consolidation multi-comptes, alertes à double seuil |
| J3 matin | Synchronisation différentielle, indicateur de fraîcheur, règles comportementales |
| J3 après-midi | Actes de conformité (art. 21 et 60), revue des alertes, piste d'audit, répétition |

**4.4 — Risques et parades.** Calibrage des seuils trop long → seuils par défaut dès J1, affinés ensuite, jamais bloquant. Licence du référentiel PPE → le socle repose sur les listes de sanctions, libres d'usage ; les PPE sont une extension, non une dépendance. Ambition du module comportemental → règles indépendantes livrées par ordre de valeur ; la démonstration reste complète si les dernières ne sont pas atteintes.

---

## 5. Valeur ajoutée pour les coopératives membres de la CIF

**Une adoption qui ne dépend d'aucun changement de comportement.** Le filtrage LBC/FT/FP n'est pas un service optionnel : c'est une obligation légale déjà due, exécutée avec des moyens insuffisants. La solution n'introduit pas une pratique nouvelle — elle outille une pratique déjà obligatoire.

**Un alignement direct sur les priorités nationales.** L'ENR 2025 range parmi les risques émergents « globalement élevés et croissants » du mobile money l'ouverture de comptes multiples et le fractionnement des montants — exactement les deux mécanismes que traitent M3 et M4 — et retient comme orientation prioritaire d'« améliorer la qualité et la réactivité de la surveillance des transactions et des déclarations d'opérations suspectes ».

**Une réduction d'un risque pénal personnel.** L'article 197 punit d'une amende de 50 000 à 700 000 FCFA l'omission non intentionnelle d'une déclaration de soupçon ; l'article 198 sanctionne le manquement aux obligations de gel résultant d'une simple imprudence. L'agent de guichet et le responsable conformité sont personnellement exposés pour une défaillance qui n'a pas besoin d'être intentionnelle. Outiller le contrôle, c'est d'abord protéger ceux qui l'exercent.

**Une réplicabilité régionale immédiate, et une souveraineté des données.** Les listes internationales sont communes aux cinq pays du programme ; seuls les jeux de règles phonétiques et les listes nationales diffèrent, et se chargent sans modification du moteur : une solution validée au Burkina Faso est déployable au Togo, au Bénin, au Sénégal et au Mali au prix d'un paramétrage. Et aucune donnée client ne quitte l'institution — le filtrage s'exécute localement contre un référentiel téléchargé.

---

## 6. Composition et complémentarité de l'équipe

L'équipe réunit un ingénieur en informatique et intelligence artificielle et trois profils réseaux et télécommunications, chacun portant un axe distinct du projet.

- **OUEDRAOGO Yannick U. L.** *(chef d'équipe)* — Moteur de correspondance, IA et intégration au système d'information.
- **KOALA Wendpanga Gédéon** — Architecture hors-ligne et synchronisation du référentiel. Réseaux et machine learning.
- **MAMOUDOU Ayouba** — Sécurité du système d'information, piste d'audit et règles de conformité. Hacking éthique.
- **GUEL Fabrice** — Expérience utilisateur au guichet, déploiement et conduite de la démonstration.

**La connaissance du système d'information bancaire vient du terrain.** Le chef d'équipe a été développeur chez Serenity S.A.R.L, prestataire dont le cœur de métier est le déploiement de **Core Banking System** pour institutions financières, où il a développé un **système d'alertes bancaires par SMS destiné aux institutions de microfinance** — un travail qui suppose de lire les événements de transaction dans la base du core banking et d'en déclencher une notification. C'est précisément ce dont dépend la consolidation multi-comptes exigée par le TDR : calculer le solde global de tous les comptes d'un même client suppose de savoir comment ces comptes sont liés dans le système existant. C'est la différence entre une maquette et une solution pensée pour s'intégrer.

L'équipe compte un lauréat du Hackathon Orange Summer Challenge (prix EY), un lauréat de deux hackathons nationaux et deux participants à des épreuves de hacking éthique en compétition : le format des 72 heures ne sera une première pour aucun de ses membres.

---

**Sources :** Loi LBC/FT/FP n° 046-2024/ALT — Loi microfinance n° 001-2025/ALT — ENR BC/FT Burkina Faso (décembre 2025) — BCEAO, Rapport sur la politique monétaire dans l'UMOA (juin 2026).
