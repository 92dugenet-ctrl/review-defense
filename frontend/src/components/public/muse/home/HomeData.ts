/**
 * Static copy for the home-page process and FAQ sections.
 * Kept separate from presentation so wording can be reviewed independently.
 */
export const homeProcess = [
  ["01", "Recevoir", "Le signal entre dans le dossier.", "Entrée"],
  [
    "02",
    "Qualifier",
    "Le contenu est distingué entre établi, disponible et à vérifier.",
    "Lecture",
  ],
  [
    "03",
    "Réunir",
    "Les captures, documents et sources utiles sont rattachés.",
    "Preuves",
  ],
] as const;

export const homeFaqs = [
  [
    "Que fait Review Defense ?",
    "Review Defense rassemble l'avis, son contexte, les éléments disponibles, les pièces utiles et les étapes de traitement dans un même espace.",
  ],
  [
    "Comment fonctionne le traitement ?",
    "Le dossier est structuré étape par étape : réception, qualification, preuves, préparation, validation et suivi.",
  ],
  [
    "Est-ce que les réponses sont envoyées automatiquement ?",
    "Non. Les actions sensibles restent sous validation humaine.",
  ],
  [
    "Que contient un dossier ?",
    "L'avis reçu, le contexte disponible, les preuves et sources associées, l'historique du traitement et la prochaine étape.",
  ],
] as const;
