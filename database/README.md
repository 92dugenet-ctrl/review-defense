# Database — organisation cible

Ce répertoire organise les schémas, politiques et références de migrations par responsabilité.

## Migration runner actif

Le script `scripts/migrate.py` charge actuellement exclusivement les fichiers `migrations/*.sql` à la racine. Ce chemin est la source d'exécution à préserver. Le répertoire `database/migrations/` n'est pas utilisé par ce runner.

Ne déplacer, renuméroter, dupliquer ou supprimer aucune migration déjà exécutée. Une future bascule vers `database/migrations/` devra modifier explicitement le runner et les workflows, vérifier l'historique `schema_migrations`, et garantir qu'aucune migration n'est rejouée.
