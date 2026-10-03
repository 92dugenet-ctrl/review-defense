import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { authToken } from "@/auth/AuthContext";
import { api } from "@/services/api/client";

import { MuseScene, Reveal } from "../MuseScene";

type BillingOffer = {
  offer_id: string;
  kind: string;
  amount: number | null;
  name_fr: string;
  description_fr?: string | null;
  paypal_hosted_button_id?: string | null;
};

type BillingCatalogResponse = {
  items?: BillingOffer[];
};

const billingGroups = [
  { title: "Abonnements", kinds: ["subscription"] },
  { title: "Audits", kinds: ["audit"] },
  { title: "Défense", kinds: ["defense_step", "defense_package"] },
];

const hostedButtonsClientId =
  "BAAftx79q4rSHY7vc2aYy_hgx3KB6GB15k__TBghUQyd1_ixXSqv71UHw1RXZvkR4cli25WsSirUKWt7zs";

async function loadPayPalSdk(url: string) {
  document
    .querySelector<HTMLScriptElement>('script[data-rd-paypal]')
    ?.remove();

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = url;
    script.async = true;
    script.dataset.rdPaypal = "1";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Impossible de charger PayPal."));
    document.head.appendChild(script);
  });
}

function formatPrice(offer: BillingOffer) {
  if (offer.amount === null) return "Sur devis";

  return (
    Number(offer.amount).toLocaleString("fr-FR", {
      maximumFractionDigits: 2,
    }) + " €"
  );
}

function getOfferLabel(kind: string) {
  if (kind === "subscription") return "ABONNEMENT";
  if (kind === "audit") return "AUDIT";
  return "DÉFENSE";
}

export function PricingCatalog() {
  const [catalog, setCatalog] = useState<BillingOffer[]>([]);
  const [error, setError] = useState("");
  const [selectedOfferId, setSelectedOfferId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<BillingCatalogResponse>("/v1/billing/catalog")
      .then((response) => setCatalog(response.items ?? []))
      .catch((cause) => {
        setError(
          cause instanceof Error ? cause.message : "Catalogue indisponible.",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  const payForOffer = async (offer: BillingOffer) => {
    setError("");
    setSelectedOfferId(offer.offer_id);

    try {
      if (!offer.paypal_hosted_button_id) {
        throw new Error("Paiement en ligne indisponible.");
      }

      const sdkUrl =
        "https://www.paypal.com/sdk/js" +
        "?client-id=" + hostedButtonsClientId +
        "&components=hosted-buttons&currency=EUR&locale=fr_FR";

      await loadPayPalSdk(sdkUrl);

      const paypal = (window as any).paypal;
      const containerId = "paypal-" + offer.offer_id;
      const container = document.getElementById(containerId);

      if (!paypal?.HostedButtons) {
        throw new Error("Les boutons PayPal hébergés sont indisponibles.");
      }
      if (!container) {
        throw new Error("Conteneur PayPal introuvable.");
      }

      container.innerHTML = "";
      paypal
        .HostedButtons({ hostedButtonId: offer.paypal_hosted_button_id })
        .render("#" + containerId);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Paiement indisponible.",
      );
      setSelectedOfferId(null);
    }
  };

  const subscribeToOffer = async (offer: BillingOffer) => {
    setError("");
    setSelectedOfferId(offer.offer_id);

    const token = authToken();
    if (!token) {
      setSelectedOfferId(null);
      window.location.href = "/register?next=/tarifs";
      return;
    }

    try {
      const config = await api.get<{
        configured: boolean;
        client_id?: string;
      }>("/v1/paypal/config");

      if (!config.configured || !config.client_id) {
        throw new Error(
          "Le paiement par abonnement n’est pas disponible pour le moment.",
        );
      }

      const plan = await api.get<{ plan_id: string }>(
        "/v1/paypal/subscription/config?offer_id=" +
          encodeURIComponent(offer.offer_id),
      );

      const sdkUrl =
        "https://www.paypal.com/sdk/js" +
        "?client-id=" + encodeURIComponent(config.client_id) +
        "&components=buttons&currency=EUR&locale=fr_FR&vault=true&intent=subscription";

      await loadPayPalSdk(sdkUrl);

      const paypal = (window as any).paypal;
      const containerId = "paypal-" + offer.offer_id;
      const container = document.getElementById(containerId);

      if (!paypal?.Buttons) {
        throw new Error("Les boutons d’abonnement PayPal sont indisponibles.");
      }
      if (!container) {
        throw new Error("Conteneur PayPal introuvable.");
      }

      container.innerHTML = "";
      paypal
        .Buttons({
          style: { layout: "vertical", label: "subscribe" },
          createSubscription: (_data: unknown, actions: any) =>
            actions.subscription.create({ plan_id: plan.plan_id }),
          onApprove: async (data: { subscriptionID: string }) => {
            await api.post(
              "/v1/paypal/subscription/confirm",
              {
                subscription_id: data.subscriptionID,
                offer_id: offer.offer_id,
              },
              { headers: { Authorization: "Bearer " + token } },
            );
            setError("");
            setSelectedOfferId(null);
          },
          onCancel: () => setSelectedOfferId(null),
          onError: (cause: { message?: string }) =>
            setError(cause.message ?? "Erreur de paiement PayPal."),
        })
        .render("#" + containerId);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "PayPal indisponible.",
      );
      setSelectedOfferId(null);
    }
  };

  return (
    <MuseScene className="muse-light">
      <Reveal>
        {error && (
          <div className="muse-price-error" role="alert">
            {error}
          </div>
        )}

        {loading && <p role="status">Chargement du catalogue…</p>}
        {!loading && catalog.length === 0 && !error && (
          <p role="status">Aucune offre disponible pour le moment.</p>
        )}

        <div className="muse-pricing-groups">
          {billingGroups.map((group) => {
            const offers = catalog.filter((offer) =>
              group.kinds.includes(offer.kind),
            );

            if (offers.length === 0) return null;

            return (
              <section key={group.title}>
                <div className="muse-eyebrow">
                  {group.title.toUpperCase()}
                </div>
                <h2>{group.title}</h2>

                <div className="muse-price-grid">
                  {offers.map((offer) => {
                    const isQuote = offer.amount === null;
                    const isSelected = selectedOfferId === offer.offer_id;

                    return (
                      <article key={offer.offer_id}>
                        <small>{getOfferLabel(offer.kind)}</small>
                        <h3>{offer.name_fr}</h3>
                        <strong>{formatPrice(offer)}</strong>
                        <p>
                          {offer.description_fr ||
                            "Format Review Defense adapté à votre besoin."}
                        </p>

                        {isQuote ? (
                          <Link className="muse-pill muse-blue" to="/contact">
                            Échanger →
                          </Link>
                        ) : isSelected ? (
                          <div
                            id={"paypal-" + offer.offer_id}
                            className="muse-paypal"
                          />
                        ) : (
                          <button
                            type="button"
                            className="muse-pill muse-blue"
                            onClick={() =>
                              offer.kind === "subscription"
                                ? void subscribeToOffer(offer)
                                : void payForOffer(offer)
                            }
                          >
                            Payer en ligne →
                          </button>
                        )}
                      </article>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </Reveal>
    </MuseScene>
  );
}
