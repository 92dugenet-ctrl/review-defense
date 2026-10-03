// SEO/editorial renderer isolated from the public shell.
function resourcesPage() {
  const articles = window.REVIEW_DEFENSE_SEO_ARTICLES || {};
  const featuredSlugs = [
    'suppression-avis-google',
    'faux-avis-google',
    'comment-reconnaitre-un-faux-avis-google',
    'comment-prouver-qu-un-avis-google-est-faux',
    'signaler-un-avis-google',
    'comment-preparer-un-dossier-de-signalement-d-un-avis-google',
    'que-faire-quand-google-refuse-de-supprimer-un-avis',
    'avis-google-concurrent',
    'avis-google-menace'
  ];

  const featuredCards = featuredSlugs
    .map((slug) => articles[slug])
    .filter(Boolean);
  const allArticles = Object.values(articles);
  const clusterCount = allArticles.reduce((counts, article) => {
    counts[article.cluster] = (counts[article.cluster] || 0) + 1;
    return counts;
  }, {});

  const hero =
    '<section class="page-hero resources-hub-hero">' +
      '<div class="page-mountain"></div>' +
      '<span>CONSEILS · GUIDES · SEO</span>' +
      '<h1>La bibliothèque Review Defense<br>' +
        '<span>pour comprendre avant d’agir.</span>' +
      '</h1>' +
      '<p>Des guides approfondis sur les faux avis, les signalements, les refus, ' +
        'les preuves et les situations particulières. Chaque article distingue ' +
        'les faits vérifiables, les démarches possibles et les limites de ce ' +
        'qui peut être conclu.</p>' +
      '<div class="resource-hub-stats">' +
        '<span><b>' + allArticles.length + '</b> guides éditoriaux</span>' +
        '<span><b>' + Object.keys(clusterCount).length + '</b> thématiques</span>' +
        '<span><b>1</b> principe : validation humaine</span>' +
      '</div>' +
    '</section>';

  const introduction =
    '<section class="rd-section resource-editorial-intro">' +
      '<div class="rd-container">' +
        '<div class="rd-section-heading">' +
          '<span class="rd-eyebrow">UNE VRAIE BASE DE CONNAISSANCES</span>' +
          '<h2>Des articles conçus pour<br>' +
            '<span>répondre à une recherche précise.</span>' +
          '</h2>' +
          '<p>Chaque page possède une intention éditoriale propre, un mot-clé ' +
            'principal, des sections structurées, une FAQ, du maillage interne ' +
            'et un appel à l’analyse. L’objectif est d’être utile au visiteur ' +
            'avant même toute conversion.</p>' +
        '</div>' +
        '<div class="resource-cluster-pills">' +
          Object.entries(clusterCount)
            .map(([name, count]) => '<span>' + name + ' · ' + count + '</span>')
            .join('') +
        '</div>' +
      '</div>' +
    '</section>';

  const featured =
    '<section class="article-grid premium-articles resource-featured-grid">' +
      featuredCards.map((article, index) =>
        '<article>' +
          '<div class="article-image article-' + (index % 6) + '"></div>' +
          '<small>' + article.cluster.toUpperCase() + '</small>' +
          '<h3>' + article.title + '</h3>' +
          '<p>Réponse directe, méthode de vérification, éléments à conserver, ' +
            'démarches possibles et conduite à tenir en cas de refus.</p>' +
          '<a href="/' + article.slug + '/">Lire l’article complet <span>→</span></a>' +
        '</article>'
      ).join('') +
    '</section>';

  const directory =
    '<section class="rd-section resource-directory">' +
      '<div class="rd-container">' +
        '<div class="rd-section-heading centered">' +
          '<span class="rd-eyebrow">TOUS LES GUIDES</span>' +
          '<h2>Explorez toute la base<br><span>par sujet.</span></h2>' +
          '<p>Les autres articles sont accessibles directement ci-dessous. ' +
            'Chaque URL répond à une intention distincte.</p>' +
        '</div>' +
        '<div class="resource-directory-grid">' +
          allArticles.map((article) =>
            '<a href="/' + article.slug + '/">' +
              '<small>' + article.cluster + '</small>' +
              '<strong>' + article.title + '</strong>' +
              '<span>' + article.keyword + ' →</span>' +
            '</a>'
          ).join('') +
        '</div>' +
      '</div>' +
    '</section>';

  const callToAction =
    '<section class="newsletter-band">' +
      '<div>' +
        '<span class="rd-eyebrow">ANALYSE</span>' +
        '<h2>Vous avez un avis précis à examiner&nbsp;?</h2>' +
        '<p>Commencez par structurer les faits et les éléments disponibles ' +
          'avant toute démarche externe.</p>' +
      '</div>' +
      '<a class="btn-primary" href="/analyse-avis-google/">' +
        'Analyser mon avis →' +
      '</a>' +
    '</section>';

  return hero + introduction + featured + directory + callToAction;
}
