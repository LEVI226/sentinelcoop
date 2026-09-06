# SentinelleCoop — conception du parcours local, données et ML

Date : 2026-09-06
Statut : conception proposée, revue utilisateur attendue ; aucune fonctionnalité déclarée implémentée par ce document.
Accord de cadrage : « allons », après la proposition dataset / entraînement / edge / PWA / PostgreSQL.

## 1. Objectif et périmètre

Livrer un démonstrateur maintenable du thème 1 CIF : client habituel ou occasionnel, comptes et soldes, filtrage PPE/sanctions, opération contrôlée, alertes persistantes, revue humaine, audit, fonctionnement local et mise à jour du référentiel. Toutes les identités et listes du mode concours sont fictives et clairement étiquetées.

L'application est une couche de conformité. Le MVP comporte un registre d'opérations simulées pour la démonstration ; il ne prétend pas remplacer un core banking. Une future intégration conserve l'autorité du core banking sur les écritures.

Premier lot indépendant : générateur synthétique, dictionnaire, tests d'intégrité, baseline de screening, entraînement et rapport d'évaluation. Les lots suivants raccordent ce socle au parcours opérationnel.

Hors premier périmètre : LLM autonome, déclaration réglementaire automatique, GNN, federated learning, paiement distribué hors ligne et ingestion de données nominatives réelles. Le rapprochement automatique inter-institutions n'est pas autorisé ; la démo simule plusieurs caisses d'une institution.

## 2. Architecture et responsabilités

- React + TypeScript : interface, aucune règle de décision indépendante du backend.
- Service Worker : cache de l'application ; aucune mise en cache générale des API sensibles.
- IndexedDB : brouillons et file locale limitée au périmètre utilisateur. Stockage navigateur non considéré comme sauvegarde.
- FastAPI local : validation, screening, contrôle des opérations, droits, audit et synchronisation.
- SQLite local : registre durable de la caisse et outbox.
- FastAPI central + PostgreSQL : réception idempotente, consolidation, versions des artefacts et jobs.
- Worker central : réévaluations, traitements réseau et distribution des packs. Jobs PostgreSQL avec bail, reprises bornées et état d'échec consultable ; RabbitMQ non requis au MVP.
- ML hors caisse : entraînement sur poste de développement. Inference locale Python en première version ; ONNX navigateur seulement après validation de parité et de compatibilité.

Le poste Windows conserve les fonctions locales sans Internet. Un Android isolé du service local conserve des brouillons et un filtrage provisoire seulement si les ressources ont été préchargées. Les retraits requérant une autorité distante restent en attente. L'installation initiale et le provisioning doivent précéder la coupure.

La PWA doit être servie dans un contexte sécurisé : localhost sur le poste ou HTTPS avec certificat reconnu sur le réseau local. Tester les origines et la session ; ne pas supposer qu'une adresse HTTP privée permet toutes les API PWA.

## 3. Données canoniques

Tables : institutions, branches, customers, identity_documents, accounts, ownership_links, transactions, watchlist_entities, watchlist_aliases, screening_decisions, alerts, review_events, audit_events, sync_inbox, sync_outbox, background_jobs, model_versions, watchlist_versions.

Identifiants UUID, institution_id obligatoire et contrôlé côté serveur. Les appartenances client-compte-caisse sont validées. Client occasionnel sans compte possible : les parties de l'opération sont distinctes des comptes optionnels.

Montants entiers en unités mineures, devise explicite. Solde initial + mouvements effectifs, annulés par compensation documentée. Aucun mélange de devises. Solde global présenté par devise et avec couverture locale/consolidée et date du snapshot.

Dates UTC avec fuseau obligatoire ; conserver occurred_at et received_at. À réception invalide, rejeter explicitement plutôt que substituer silencieusement la date courante.

Une relation d'identité vérifiée est distincte d'une correspondance potentielle. Ni nom, téléphone ni hash d'un nom n'établissent une identité réseau certaine. Identifiants pseudonymes ne signifient pas anonymat.

## 4. Générateur synthétique et contrôles

Configuration reproductible : seed 42, horloge fixe documentée, identifiants déterministes, distribution de scénarios versionnée. Premier fixture : 20 dossiers métier vérifiables. Extension paramétrable : 5 caisses, 2000 personnes fictives, 3000 comptes, 50000 opérations sur 90 jours et 200 entrées fictives de référentiel. Ces nombres sont des cibles de génération, pas des mesures réalisées.

Générer dans l'ordre : organisations, identités, liens, comptes, activité habituelle, scénarios, perturbations. Activités légitimes : épargne, commerce, collecte, tontine, remboursements et transferts internes. Scénarios à examiner : convergence, redistribution rapide, fractionnement et cycle temporel. Ajouter homonymes, dates manquantes ou partielles, fautes de frappe et alias. Aucun pays ne détermine mécaniquement le label.

Séparer dataset canonique et flux de transport perturbé : duplications, retards et reprises ne créent pas de nouvelles transactions canoniques. Les annulations sont des événements distincts liés à l'original.

Contrôles bloquants : unicité, références, montants positifs, devises cohérentes, ordre des versions, conservation des soldes et absence de fuite des labels dans les features. Produire un manifeste avec paramètres, compteurs, seed, horloge, hash de chaque fichier et version du générateur.

Sources synthétiques marquées SYNTHETIC_DEMO, jamais présentées comme une vraie inscription ONU ou nationale. L'existence historique de fichiers ONU dans le dépôt ne doit entraîner aucun chargement automatique.

## 5. Entraînement du screening

Cible : same_identity sur des paires d'identités fictives. Séparer les identités 60/20/20 avant génération des variantes et paires ; toutes les identités d'une paire appartiennent au même split. Vérifier les intersections vides. Réserver des familles de perturbations au test.

Construire positifs, négatifs simples et homonymes difficiles ; documenter la proportion, qui ne représente pas une prévalence réelle. Évaluation supplémentaire par requête contre un référentiel synthétique, avec cas sans correspondance.

Features : Jaro-Winkler, Levenshtein normalisée, WAPE, recouvrement tokens, longueur, accord année/date complète, précision et indicateurs d'attributs absents. Exclure IDs, noms de scénarios, décisions et label. Prétraitements appris uniquement sur train.

Baseline : moteur existant, avec politique PPE corrigée séparément. Candidat : régression logistique, comparaison sur validation. Réserver dans validation une portion pour calibration et une pour choix du seuil, sans consulter le test. Le score ne sera appelé probabilité calibrée que dans les limites de l'évaluation synthétique documentée.

Rapport : rappel de récupération des candidats, précision/rappel du classement, faux positifs sur homonymes, charge de revue pour 1000 requêtes, intervalles d'incertitude groupés par identité et latence sur machine documentée. Comparer à rappel comparable. Le test final n'est consulté qu'après sélection ; une nouvelle itération est déclarée comme telle et nécessite une nouvelle évaluation indépendante pour une nouvelle revendication.

Promotion : intégrité et séparation des données passent ; sorties finies ; au point de fonctionnement choisi sur validation, pas de perte de rappel observée par rapport à la baseline sur le test et réduction observée des faux positifs. Ce critère de démonstration n'est pas une validation bancaire. Si le candidat ne l'atteint pas, conserver la baseline et publier honnêtement le résultat.

Conserver features, métriques, environnement verrouillé, modèle, politique, manifeste et MODEL_CARD. Aucun réentraînement ni déploiement automatique après un simple clic analyste. Les décisions humaines ne deviennent pas automatiquement des labels de vérité.

## 6. Politique et opérations

Séparer match_score, priority_score, identity_resolution et operational_decision. PPE identifiée = vigilance selon politique ; pas de blocage au seul statut. Similarité forte = candidat à examiner ; sanction confirmée = traitement prévu par une politique validée. Moteur indisponible ou référentiel expiré = contrôle incomplet.

États de la demande : DRAFT → PENDING_CHECK → READY ou HELD ; READY → POSTED après revalidation atomique ; rejet explicite possible. POSTED ne redevient pas DRAFT : compensation pour annuler. Une revue ne poste pas automatiquement une demande si solde, données ou version ont changé.

Dans le simulateur, aucune opération HELD ne modifie le solde. Validation et écriture utilisent transaction et contrôle de concurrence ; un même identifiant ne produit qu'un seul effet. Retrait négatif, mauvais propriétaire, mandat invalide ou solde insuffisant : refus explicite. En contexte réel, le mécanisme de commit relève de l'adaptateur core banking.

Règles temporelles : bornes basse et haute explicites, événements disponibles à l'instant d'analyse, pas de mélange de devises, recalcul après réception tardive et annulation. Chaque alerte cite ses événements et sa version de règle. Le graphe cherche des motifs temporels bornés ; centralité seule insuffisante pour conclure au risque.

## 7. Synchronisation et versions

POST /sync/push : lot limité à 100 événements ; accusé par événement. Clé unique institution_id/device_id/event_id, payload_hash. Même clé et même contenu = précédent résultat ; même clé et contenu différent = conflit 409. Serveur dérive institution et appareil des credentials, pas du seul payload. Dépendance manquante = en attente de dépendance, pas abandon silencieux.

Réception centrale atomique : inbox, événement, projection et outbox dans la même transaction PostgreSQL. Côté SQLite, effet local et outbox atomiques. Reprise de jobs par bail expiré ; retries avec backoff exponentiel plafonné à 60 secondes et jitter. Accusé perdu = renvoi sans double effet. Erreur permanente consultable et non réessayée indéfiniment.

GET /sync/pull?cursor= : changements autorisés paginés et curseur opaque monotone. Aucun last-write-wins sur soldes ; fiches clients avec version attendue et conflit explicite. Pas de réplication intégrale des données entre caisses.

Synchronisation déclenchée à l'ouverture, au retour au premier plan, par bouton et périodiquement lorsque l'app reste ouverte. Background Sync seulement comme optimisation ; navigateur fermé ne garantit pas une tâche en arrière-plan.

Deux canaux : montée des événements, descente des référentiels/politiques/modèles. Nouveau pack reçu : signature et hash vérifiés, compatibilité, activation atomique, job durable de réexamen, état de progression visible. Version de liste distincte du modèle ; mise à jour liste sans entraînement.

Une liste distante non reçue pendant une coupure ne peut être appliquée. Afficher couverture et expiration, mesurer réception→activation et activation→fin de réexamen séparément. Contrôle de régression des numéros de version ; restauration autorisée d'un modèle distincte d'un retour à une ancienne liste de sanctions.

## 8. Interfaces et sécurité

API locale : /customers, /customers/{id}/accounts, /customers/{id}/transactions, /screenings, /operation-requests, /operation-requests/{id}/commit, /alerts, /alerts/{id}/reviews, /reference-status, /health.

API centrale supplémentaire : /sync/push, /sync/pull, /artifacts/manifest et téléchargement autorisé des packs.

Rôles : agent de caisse, conformité caisse, conformité institution, administrateur technique. Autorisation côté serveur et filtrage institution/caisse ; acteur des décisions issu de session vérifiée. L'administrateur technique ne reçoit pas automatiquement les preuves métier. Session offline bornée par un bail local ; expiration sans possibilité de réauthentification = accès limité, pas contournement.

TLS, protection de session, origines contrôlées, limites de taille et absence de secrets dans Git. Audit append-only applicatif ; ne pas le présenter comme inviolable contre l'administrateur de la base. Références juridiques traçables et politiques de démonstration distinguées des obligations nationales validées.

## 9. Recette et exploitation

Tests obligatoires : données reproductibles et cohérentes ; séparation train/test ; PPE non bloquée par statut ; homonyme en revue ; débit suspendu sans effet ; rejeu sans doublon ; mauvais propriétaire refusé ; annulation cohérente ; client occasionnel sans compte ; redémarrage avec alertes conservées ; crash avant/après accusé ; événement tardif ; signature invalide ; pack incompatible ; référentiel expiré ; perte de stockage navigateur ; accès inter-caisse interdit ; sauvegarde restaurée.

Mesures : latence p50/p95, mémoire, taille modèle, poids du pack, file en attente, délai d'activation et de réexamen. Aucun chiffre de performance annoncé avant mesure.

Livraison documentaire : dictionnaire, carte du modèle, README de démarrage, guide opérateur, diagnostic, sauvegarde/restauration, CHANGELOG et prompts avec décisions humaines. Un second membre reproduit le parcours sans IA et signe une fiche de recette.

## 10. Ordre de réalisation

1. Dataset + baseline + expérimentation ML reproductible.
2. Réparation backend, persistance et contrats opérationnels.
3. Interface React raccordée et parcours métier.
4. Synchronisation caisse/siège et packs versionnés.
5. Tests de panne, mesures, documentation et répétition de huit minutes.

Chaque lot a un résultat testable ; l'entraînement ne retarde pas la réparation des contrôles métier. Pas de migration destructive de fichiers existants. Les composants téléchargés sans licence identifiée ne sont pas copiés dans l'implémentation.

## 11. Sources et décisions de cadrage

Sources de règles : briefing CIF v2.0 et TDR déjà examinés ; demande explicite edge/PWA/PostgreSQL et maintenance sans IA. Les six textes joints du dernier message sont des références secondaires et des propositions, pas des prescriptions réglementaires. Les articles AML, cycle ML et MLOps inspirent la reproductibilité ; aucune statistique marketing n'est reprise.

Choix retenus : identité avant anomalie ML ; règles déterministes pour monitoring initial ; pas de nom automatique CIF-NEXUS ; conservation de SentinelleCoop ; pas de risque égal à nationalité, centralité ou profession seule ; pas de déclaration automatique ; pas de promesse de synchronisation instantanée hors réseau.

Auto-revue documentaire : périmètre et interfaces cohérents ; limites explicites ; aucun résultat fictif présenté comme mesuré. La revue utilisateur de cette spécification précède le plan détaillé, conformément à la méthode brainstorming fournie.
