# Billing — page de facturation

Regroupe l'interface de consultation du catalogue et des informations de facturation. Les paiements, abonnements, webhooks et changements de droits restent pilotés par le backend et le fournisseur de paiement.

Ne jamais exposer de secret PayPal dans le bundle frontend. Préserver les contrats API et les retours d'état de paiement.

Structure cible sous `application/`; ne pas la confondre avec une route de production active sans vérifier le routeur et le serveur.
