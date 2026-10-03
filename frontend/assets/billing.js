// Billing and PayPal integration isolated from the console shell.
const PAYPAL_HOSTED_CLIENT_ID =
  'BAAftx79q4rSHY7vc2aYy_hgx3KB6GB15k__TBghUQyd1_ixXSqv71UHw1RXZvkR4cli25WsSirUKWt7zs';
const PAYPAL_SUBSCRIPTION_CLIENT_ID =
  'BAADwFz5aRpmMnNRVADMoONwkWyHzC3Y-l75vTda13-4tfwv2gSa4TdAq_jguOBTz2kBqsU1ARHCQ7nz6k';

let PAYPAL_RUNTIME_CLIENT_ID = '';

async function paypalClientId() {
  if (PAYPAL_RUNTIME_CLIENT_ID) {
    return PAYPAL_RUNTIME_CLIENT_ID;
  }

  try {
    const config = await api('/v1/paypal/config');

    if (config?.client_id) {
      PAYPAL_RUNTIME_CLIENT_ID = String(config.client_id);
    }
  } catch (_) {
    // Fall back to the hosted client ID when runtime configuration is absent.
  }

  return PAYPAL_RUNTIME_CLIENT_ID || PAYPAL_HOSTED_CLIENT_ID;
}

function selectClientBillingOffer(type, name, price, offerId) {
  try {
    localStorage.setItem(
      'rd_selected_offer',
      JSON.stringify({
        type,
        name,
        price,
        offer_id: offerId || null,
        selected_at: new Date().toISOString()
      })
    );
  } catch (_) {
    // The selection can still be used for the current page session.
  }

  if (offerId) {
    showBillingPayment();
  }
}

function selectedBillingOffer() {
  try {
    return JSON.parse(localStorage.getItem('rd_selected_offer') || 'null');
  } catch (_) {
    return null;
  }
}

async function loadPayPalSdk(clientId, components, locale, extra = '') {
  const key = clientId + '|' + components + '|' + locale;

  if (window.__rdPayPalSdkKey === key && window.paypal) {
    return window.paypal;
  }

  const source =
    'https://www.paypal.com/sdk/js?client-id=' +
    encodeURIComponent(clientId) +
    '&components=' +
    components +
    '&currency=EUR&locale=' +
    locale +
    extra;

  await new Promise((resolve, reject) => {
    const previous = document.querySelector(
      'script[data-review-defense-paypal]'
    );

    if (previous) {
      previous.remove();
    }

    const script = document.createElement('script');
    script.src = source;
    script.async = true;
    script.dataset.reviewDefensePaypal = '1';
    script.onload = resolve;
    script.onerror = () => {
      const message = locale === 'en_GB'
        ? 'Unable to load PayPal.'
        : 'Impossible de charger PayPal.';

      reject(new Error(message));
    };

    document.head.appendChild(script);
  });

  if (!window.paypal) {
    const message = locale === 'en_GB'
      ? 'PayPal is unavailable.'
      : 'PayPal est indisponible.';

    throw new Error(message);
  }

  window.__rdPayPalSdkKey = key;
  return window.paypal;
}

async function loadBillingCatalog() {
  return api('/v1/billing/catalog');
}

async function renderHostedButton(buttonId, english) {
  const hostId =
    'paypal-hosted-' + String(buttonId).replace(/[^a-zA-Z0-9_-]/g, '');
  const container = document.getElementById('paypal-button-container');

  if (!container) {
    const message = english
      ? 'PayPal checkout container is missing.'
      : 'Conteneur de paiement PayPal introuvable.';

    throw new Error(message);
  }

  container.innerHTML = '<div id="' + hostId + '"></div>';

  const paypal = await loadPayPalSdk(
    await paypalClientId(),
    'hosted-buttons',
    english ? 'en_GB' : 'fr_FR'
  );

  if (!paypal.HostedButtons) {
    const message = english
      ? 'Hosted PayPal buttons are unavailable.'
      : 'Les boutons PayPal hébergés sont indisponibles.';

    throw new Error(message);
  }

  paypal.HostedButtons({ hostedButtonId: buttonId }).render('#' + hostId);
}

async function renderSubscriptionButton(offerId, english) {
  const config = await api(
    '/v1/paypal/subscription/config?offer_id=' +
    encodeURIComponent(offerId)
  );
  const paypal = await loadPayPalSdk(
    PAYPAL_SUBSCRIPTION_CLIENT_ID,
    'buttons',
    english ? 'en_GB' : 'fr_FR',
    '&vault=true&intent=subscription'
  );

  paypal.Buttons({
    style: {
      layout: 'vertical',
      label: 'subscribe'
    },
    createSubscription: (data, actions) =>
      actions.subscription.create({ plan_id: config.plan_id }),
    onApprove: async (data) => {
      try {
        await api('/v1/paypal/subscription/confirm', {
          method: 'POST',
          body: JSON.stringify({
            offer_id: offerId,
            subscription_id: data.subscriptionID
          })
        });

        toast(
          english ? 'Subscription confirmed' : 'Abonnement confirmé',
          'success'
        );
        closeModal();
        await window.reviewDefenseRender();
      } catch (error) {
        const message =
          error?.message ||
          (
            english
              ? 'Subscription confirmation failed'
              : 'Échec de la confirmation de l’abonnement'
          );

        toast(message, 'error');

        const container = document.getElementById(
          'paypal-button-container'
        );

        if (container) {
          container.insertAdjacentHTML(
            'beforeend',
            '<div class="error-state" style="margin-top:12px">' +
              esc(message) +
            '</div>'
          );
        }
      }
    },
    onCancel: () => {
      toast(
        english ? 'Payment cancelled' : 'Paiement annulé',
        'error'
      );
    },
    onError: (error) => {
      const message =
        error?.message ||
        (english ? 'PayPal payment error' : 'Erreur de paiement PayPal');

      toast(message, 'error');
    }
  }).render('#paypal-button-container');
}

async function showBillingPayment() {
  const selected = selectedBillingOffer();
  const offerId = selected?.offer_id || 'monitoring_professional';
  const english = window.ReviewDefenseI18n?.getLanguage?.() === 'en';

  let catalog;

  try {
    catalog = await loadBillingCatalog();
  } catch (error) {
    toast(error.message || 'Catalogue indisponible', 'error');
    return;
  }

  const offer = (catalog.items || []).find(
    (item) => item.offer_id === offerId
  );

  if (!offer) {
    toast(
      english ? 'This offer is unavailable.' : 'Cette offre est indisponible.',
      'error'
    );
    return;
  }

  const subscription = offer.kind === 'subscription';
  const configured = subscription
    ? Boolean(offer.paypal_plan_id)
    : Boolean(offer.paypal_hosted_button_id);

  if (!configured) {
    toast(
      english
        ? 'This payment is not configured yet.'
        : 'Ce paiement n’est pas encore configuré.',
      'error'
    );
    return;
  }

  const title = english ? 'PayPal payment' : 'Paiement PayPal';
  const label = english
    ? (offer.name_en || offer.offer_id)
    : (offer.name_fr || offer.offer_id);
  const price = offer.amount === null
    ? (english ? 'Custom quote' : 'Sur devis')
    : offer.amount + ' €' + (subscription ? ' / month' : '');

  modal(
    title,
    '<div class="stack">' +
      '<div class="billing-checkout-summary">' +
        '<strong>' + esc(label) + '</strong>' +
        '<span>' + esc(price) + '</span>' +
      '</div>' +
      '<p>' +
        esc(
          english
            ? 'Secure checkout powered directly by PayPal.'
            : 'Paiement sécurisé directement via PayPal.'
        ) +
      '</p>' +
      '<div id="paypal-button-container"></div>' +
      '<p class="human-note">' +
        esc(
          english
            ? 'Payment does not trigger external Google action.'
            : 'Le paiement ne déclenche aucune action externe Google.'
        ) +
      '</p>' +
    '</div>'
  );

  try {
    if (subscription) {
      await renderSubscriptionButton(offerId, english);
    } else {
      await renderHostedButton(offer.paypal_hosted_button_id, english);
    }
  } catch (error) {
    const message = error?.message || 'PayPal error';
    toast(message, 'error');

    const container = document.getElementById('paypal-button-container');

    if (container) {
      container.insertAdjacentHTML(
        'beforeend',
        '<div class="error-state" style="margin-top:12px">' +
          esc(message) +
        '</div>'
      );
    }
  }
}

async function openBillingPlanSelector() {
  const english = window.ReviewDefenseI18n?.getLanguage?.() === 'en';

  try {
    const catalog = await loadBillingCatalog();
    const items = (catalog.items || []).filter(
      (item) => item.kind === 'subscription'
    );

    const html =
      '<div class="billing-selector">' +
        items.map((item) =>
          '<article class="billing-option">' +
            '<div>' +
              '<strong>' +
                esc(english ? item.name_en : item.name_fr) +
              '</strong>' +
              '<span>' + esc(item.offer_id) + '</span>' +
            '</div>' +
            '<div><b>' + esc(item.amount || '—') + ' €</b></div>' +
            '<button class="primary billing-offer-btn" ' +
              'data-billing-offer="subscription" ' +
              'data-billing-name="' +
                esc(english ? item.name_en : item.name_fr) +
              '" data-billing-price="' +
                esc(item.amount || '') +
              '" data-billing-id="' +
                esc(item.offer_id) +
              '">' +
              (english ? 'Choose' : 'Choisir') +
            '</button>' +
          '</article>'
        ).join('') +
      '</div>';

    modal(
      english ? 'Choose a plan' : 'Choisir une formule',
      html
    );
  } catch (error) {
    toast(error.message || 'Catalogue indisponible', 'error');
  }
}
