const menuButton = document.querySelector('.menu-button');
const drawer = document.querySelector('.drawer');
const scrim = document.querySelector('.scrim');
const closeButton = document.querySelector('.drawer-close');

function setMenu(open) {
  drawer.classList.toggle('open', open);
  scrim.classList.toggle('open', open);
  drawer.setAttribute('aria-hidden', String(!open));
  menuButton.setAttribute('aria-expanded', String(open));
  document.body.style.overflow = open ? 'hidden' : '';
}

menuButton.addEventListener('click', () => setMenu(true));
closeButton.addEventListener('click', () => setMenu(false));
scrim.addEventListener('click', () => setMenu(false));

drawer.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => setMenu(false));
});

const tabs = [...document.querySelectorAll('.tabs button')];
const experienceImage = document.querySelector('[data-experience-image]');
const experiencePrimary = document.querySelector(
  '[data-experience-text="primary"]'
);
const experienceSecondary = document.querySelector(
  '[data-experience-text="secondary"]'
);

const experienceStates = {
  analyse: {
    image: 'assets/resources-analyse.svg',
    alt: 'Aperçu de l’analyse d’un avis dans Review Defense',
    primary: 'Analysez le contenu d’un avis et identifiez les informations qui méritent d’être examinées.',
    secondary: 'Comprenez le contexte disponible, repérez les éléments à vérifier et préparez la suite à partir d’informations structurées.'
  },
  reponse: {
    image: 'assets/resources-reponse.svg',
    alt: 'Aperçu d’une réponse préparée dans Review Defense',
    primary: 'Préparez une réponse adaptée à la situation à partir des éléments disponibles.',
    secondary: 'Relisez le contenu proposé, ajustez-le si nécessaire et gardez la validation avant toute action importante.'
  },
  securite: {
    image: 'assets/resources-securite.svg',
    alt: 'Illustration des données protégées dans Review Defense',
    primary: 'Gardez la maîtrise des informations utilisées dans chaque dossier.',
    secondary: 'Retrouvez les informations utiles dans un espace organisé et examinez les actions importantes avant leur exécution.'
  },
  dossier: {
    image: 'assets/resources-dossier.svg',
    alt: 'Aperçu d’un dossier Review Defense',
    primary: 'Regroupez avis, fichiers, contexte et éléments utiles dans un même dossier.',
    secondary: 'Gardez une vision claire de ce qui a été analysé, préparé et validé, sans perdre le fil de la situation.'
  }
};

function selectExperience(tab) {
  tabs.forEach((item) => item.classList.remove('active'));
  tab.classList.add('active');

  const state =
    experienceStates[tab.dataset.experience] || experienceStates.analyse;

  if (experienceImage) {
    experienceImage.src = state.image;
    experienceImage.alt = state.alt;
  }

  if (experiencePrimary) {
    experiencePrimary.textContent = state.primary;
  }

  if (experienceSecondary) {
    experienceSecondary.textContent = state.secondary;
  }
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => selectExperience(tab));
});
