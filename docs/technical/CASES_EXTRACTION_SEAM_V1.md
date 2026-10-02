# Review Defense — Cases Extraction Seam V1

## Purpose

Cette note définit le premier point d'extraction du contexte **Cases** après la cartographie V1.

Elle est volontairement préparatoire : elle ne modifie aucun comportement, aucune route, aucun schéma DB et aucune configuration serveur.

## 1. Périmètre actuellement observé

Le bloc `/v1/cases` de `src/api_server.py` couvre actuellement :

- création et listing des cases ;
- chargement/hydratation d'un case depuis `MemoryStore` ou le repository ;
- hydratation des reviews et des données Evidence ;
- lecture du case et du workspace ;
- SLA et pause/reprise ;
- analyse des contradictions ;
- extraction de faits depuis les preuves ;
- checklist et readiness ;
- lecture/matrice des contradictions ;
- disposition humaine des contradictions ;
- création de décision ;
- freeze du dossier ;
- approbation ;
- préparation de soumission.

Le même bloc appelle directement `MemoryStore`, le repository et plusieurs modules métier.

## 2. Premier seam retenu

Le premier seam doit être **le chargement du contexte Case**, avant de déplacer les transitions métier.

Périmètre proposé :

`organization_id + case_id` → Case + Review + Evidence/Facts nécessaires à la route.

Responsabilités du seam :

1. retrouver le Case ;
2. hydrater le Case depuis la persistence si nécessaire ;
3. charger la Review associée ;
4. charger les Evidence associées au Case ;
5. charger les Evidence Facts associés ;
6. placer les données dans une représentation explicite consommable par les opérations Cases.

Le seam ne doit pas :

- décider d'une autorisation ;
- créer une décision ;
- modifier le statut métier ;
- calculer une approbation ;
- envoyer une notification ;
- appeler PayPal/Google/SMTP ;
- modifier le schéma DB ;
- modifier la configuration serveur.

## 3. Pourquoi ce seam en premier

Le chargement/hydratation est répété ou implicite dans plusieurs branches.

En particulier, le bloc Case :

- charge le Case depuis `MemoryStore` puis éventuellement PostgreSQL ;
- charge les Evidence pour chaque requête Case ;
- charge les Facts associés ;
- charge la Review si elle n'est pas en mémoire.

Ce couplage est une dépendance structurelle commune aux routes Cases. Le déplacer en premier permet ensuite de traiter séparément les opérations métier sans mélanger plusieurs changements.

## 4. Frontière proposée

Direction :

`HTTP route → Cases application seam → persistence contract / current store → domain modules`

La route conserve temporairement :

- parsing HTTP ;
- authentification/autorisation ;
- sérialisation HTTP ;
- traduction des erreurs.

Le seam prend progressivement en charge :

- résolution du Case ;
- hydratation de son contexte de travail.

Aucun nouveau système de persistence ne doit être introduit.

## 5. Source de vérité

Pendant cette première extraction :

- `MemoryStore` reste la source runtime existante ;
- le repository reste la source persistante existante ;
- aucune duplication de stockage n'est créée ;
- le seam ne possède pas une nouvelle copie durable du Case ;
- les contrats repository existants sont réutilisés.

## 6. Ordre des extractions ultérieures

Après validation du premier seam :

1. workspace/read models ;
2. SLA ;
3. contradictions et dispositions ;
4. checklist/readiness ;
5. decision/freeze/approval ;
6. submission preparation.

Chaque extraction doit rester indépendante et conserver les routes existantes.

## 7. Invariants obligatoires

Chaque commit suivant doit préserver :

- les chemins HTTP ;
- les méthodes HTTP ;
- les codes de réponse ;
- les payloads JSON ;
- les contrôles de rôle ;
- les effets repository existants ;
- les événements d'audit ;
- le comportement idempotent ;
- le schéma DB ;
- la configuration serveur ;
- les intégrations externes.

## 8. Processus obligatoire

Un seul changement structurel par commit.

Séquence :

`1 commit → workflow → attendre le résultat → analyse → commit suivant`

En cas d'échec : corriger uniquement l'échec dans un nouveau commit, puis relancer le workflow.

## 9. État

Cette note ne réalise pas encore l'extraction. Elle fixe uniquement le seam à implémenter dans le prochain changement atomique.
