# Lot U — rate limiting partagé et validation réelle des uploads

## Corrections intégrées

- Les quotas généraux, de connexion et de récupération utilisent désormais
  une opération PostgreSQL atomique en mode persistant. Le compteur est commun
  aux workers Gunicorn et repose sur une fenêtre fixe.
- Les identifiants de quota sont hachés avant persistance ; la table ne stocke
  ni adresse IP ni adresse email en clair.
- Une indisponibilité du compteur partagé provoque un refus temporaire (503)
  au lieu d'un retour silencieux à des quotas locaux moins stricts.
- La table de quotas possède une expiration et un nettoyage périodique des
  entrées expirées.
- Les fichiers PDF, JPEG, PNG et WebP sont contrôlés par signature binaire.
  Les fichiers texte/CSV sont contrôlés en UTF-8 et rejetés s'ils contiennent
  des octets de contrôle incompatibles avec du texte.
- Le contrôle vérifie aussi la cohérence entre taille annoncée et taille réelle,
  ainsi que les noms trop longs ou contenant des caractères de contrôle.
- Les deux frontières de stockage de preuves et le parcours d'upload de
  documents client transmettent désormais les octets au validateur.

## Limites et suites nécessaires

- Le mode sans PostgreSQL conserve volontairement le limiteur mémoire : il
  n'est pas distribué et ne doit pas être utilisé comme garantie multi-instance.
- La CSP conserve unsafe-inline pour les scripts et styles. L'interface
  historique contient des styles inline et des gestionnaires d'événements
  inline ; retirer ces directives sans migrer ces usages casserait des parcours.
  Une CSP stricte nécessite d'abord de supprimer les gestionnaires inline,
  d'extraire les styles inline ou d'introduire une stratégie nonce/hash avec
  propagation contrôlée par le serveur.
- Les fichiers restent traités par les extracteurs applicatifs existants.
  Aucun service antivirus ou bac à sable de parsing n'est configuré dans le
  dépôt ; la signature réduit l'usurpation MIME mais ne garantit pas qu'un
  document est inoffensif.
- Le bearer token React reste dans sessionStorage. Une évolution vers cookie
  HttpOnly doit être accompagnée d'une politique CSRF et d'une migration des
  clients ; ce lot ne change pas le contrat d'authentification.

## Vérification statique

Inspection des appels de limitation, des frontières de stockage, des signatures
de fichiers, du schéma PostgreSQL et des usages frontend inline. Aucun test,
build, typecheck, lint ou workflow GitHub Actions n'a été exécuté.
