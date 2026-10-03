(() => {
  const root = document.querySelector('.rd-home');

  if (!root) {
    return;
  }

  const reduce = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  const reveal = () => {
    const elements = root.querySelectorAll('[data-reveal]');

    if (reduce) {
      elements.forEach((element) => {
        element.classList.add('is-visible');
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    elements.forEach((element) => observer.observe(element));
  };

  reveal();

  const menu = root.querySelector('.menu-toggle');
  const mobile = root.querySelector('.mobile-menu');

  if (menu) {
    menu.addEventListener('click', () => {
      const open = mobile.classList.toggle('open');
      menu.setAttribute('aria-expanded', String(open));
    });

    mobile.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        mobile.classList.remove('open');
        menu.setAttribute('aria-expanded', 'false');
      });
    });
  }

  if (!reduce) {
    const hero = root.querySelector('.hero');

    hero.addEventListener('pointermove', (event) => {
      const bounds = hero.getBoundingClientRect();
      const x = (event.clientX - bounds.left) / bounds.width - 0.5;
      const y = (event.clientY - bounds.top) / bounds.height - 0.5;

      root.style.setProperty('--mx', `${x * 16}px`);
      root.style.setProperty('--my', `${y * 10}px`);
    });

    hero.addEventListener('pointerleave', () => {
      root.style.setProperty('--mx', '0px');
      root.style.setProperty('--my', '0px');
    });
  }

  const form = root.querySelector('.contact-form');

  if (form) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();

      const data = new FormData(form);
      const subject = encodeURIComponent(
        'Demande Review Defense — ' +
        String(data.get('company') || 'Contact')
      );
      const body = encodeURIComponent(
        'Nom : ' + String(data.get('name') || '') +
        '\nE-mail : ' + String(data.get('email') || '') +
        '\nEntreprise : ' + String(data.get('company') || '') +
        '\n\nMessage :\n' + String(data.get('message') || '')
      );

      window.location.href =
        'mailto:contact@review-defense.com?subject=' +
        subject +
        '&body=' +
        body;
    });
  }

  const newsletter = root.querySelector('.newsletter');

  if (newsletter) {
    const input = newsletter.querySelector('input[type=email]');
    const button = newsletter.querySelector('button');

    if (button && input) {
      button.addEventListener('click', () => {
        if (!input.checkValidity()) {
          input.reportValidity();
          return;
        }

        window.location.href =
          'mailto:contact@review-defense.com?subject=' +
          encodeURIComponent('Inscription aux ressources Review Defense') +
          '&body=' +
          encodeURIComponent(
            'Je souhaite recevoir les ressources à cette adresse : ' +
            input.value
          );
      });
    }
  }

  root.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', (event) => {
      const target = root.querySelector(link.getAttribute('href'));

      if (target) {
        event.preventDefault();
        target.scrollIntoView({
          behavior: reduce ? 'auto' : 'smooth'
        });
      }
    });
  });
})();

/* V6.40 Premium landing micro-interactions */
(() => {
  const root = document.querySelector('.rd-home');

  if (!root) {
    return;
  }

  root
    .querySelectorAll('.hero-actions a,.public-actions a,.how-cta a')
    .forEach((link) => {
      link.addEventListener('pointerdown', () => {
        link.classList.add('is-pressed');
      });

      ['pointerup', 'pointerleave'].forEach((eventName) => {
        link.addEventListener(eventName, () => {
          link.classList.remove('is-pressed');
        });
      });
    });
})();
