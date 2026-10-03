# Monitoring

Zone cible pour les configurations et runbooks de supervision.

État actuel : conserver `prometheus.yml`, `monitoring/alerts.yml` et les modules d'observabilité sous `src/`. Ne pas créer une seconde configuration de métriques ou d'alertes. Tout déplacement doit conserver les chemins consommés par Prometheus et les workflows.
