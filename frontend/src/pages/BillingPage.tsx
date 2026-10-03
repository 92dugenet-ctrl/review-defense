// Interface de facturation et d'abonnement : lit l'état de facturation et le catalogue depuis l'API.
// Le backend fournit la configuration publique PayPal et les identifiants d'offres ; le navigateur
// charge ensuite le SDK PayPal pour afficher les boutons. Après approbation, l'identifiant
// d'abonnement est transmis au backend, qui reste responsable de la confirmation et de l'état payé.

import { useEffect, useRef, useState } from "react";

import { authToken } from "@/auth/AuthContext";
import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { StatusPill } from "@/components/layout/StatusPill";
import { api } from "@/services/api/client";

declare global {
  interface Window {
    paypal?: {
      Buttons: (options: any) => {
        render: (selector: string) => Promise<void> | void;
      };
    };
  }
}

/** Shared promise prevents multiple PayPal SDK script downloads. */
let paypalSdkPromise: Promise<void> | null = null;

/**
 * Loads the PayPal JavaScript SDK once for the current page session.
 * The client ID is supplied by the backend configuration endpoint.
 */
async function loadPayPalSdk(clientId: string) {
  if (window.paypal) return;

  if (!paypalSdkPromise) {
    paypalSdkPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src =
        "https://www.paypal.com/sdk/js?client-id=" +
        encodeURIComponent(clientId) +
        "&components=buttons&vault=true&intent=subscription";
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Impossible de charger PayPal"));
      document.head.appendChild(script);
    });
  }

  return paypalSdkPromise;
}

/**
 * Displays the current billing state and available subscription offers.
 * Subscription creation and confirmation remain backend-controlled.
 */
export function BillingPage() {
  const [billing, setBilling] = useState<any>(null);
  const [catalog, setCatalog] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [selectedOffer, setSelectedOffer] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const isMounted = useRef(false);

  async function loadBilling() {
    try {
      const [billingResponse, catalogResponse] = await Promise.all([
        api.get<any>("/v1/billing"),
        api.get<any>("/v1/billing/catalog"),
      ]);

      setBilling(billingResponse);
      setCatalog(catalogResponse.items ?? []);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Facturation indisponible",
      );
    }
  }

  useEffect(() => {
    isMounted.current = true;
    void loadBilling();

    return () => {
      isMounted.current = false;
    };
  }, []);

  async function subscribeToOffer(offer: any) {
    setError("");
    setMessage("");
    setSelectedOffer(offer.offer_id);

    try {
      const paypalConfig = await api.get<any>("/v1/paypal/config");

      if (!paypalConfig.configured || !paypalConfig.client_id) {
        throw new Error("PayPal n’est pas encore configuré.");
      }

      const plan = await api.get<any>(
        "/v1/paypal/subscription/config?offer_id=" +
          encodeURIComponent(offer.offer_id),
      );

      await loadPayPalSdk(paypalConfig.client_id);

      const containerId = "paypal-" + offer.offer_id;
      const container = document.getElementById(containerId);

      if (!container) {
        throw new Error("Conteneur PayPal introuvable.");
      }

      container.innerHTML = "";

      await window.paypal!.Buttons({
        style: {
          layout: "vertical",
          shape: "rect",
          label: "subscribe",
        },
        createSubscription: (_data: any, actions: any) =>
          actions.subscription.create({ plan_id: plan.plan_id }),
        onApprove: async (paypalData: any) => {
          const token = authToken();

          await api.post(
            "/v1/paypal/subscription/confirm",
            {
              subscription_id: paypalData.subscriptionID,
              offer_id: offer.offer_id,
            },
            {
              headers: token
                ? { Authorization: "Bearer " + token }
                : undefined,
            },
          );

          if (isMounted.current) {
            setMessage(
              "Abonnement enregistré. Votre compte sera synchronisé avec les événements PayPal.",
            );
            await loadBilling();
          }
        },
        onError: (caught: any) => {
          setError(
            caught instanceof Error
              ? caught.message
              : "Paiement PayPal impossible",
          );
        },
      }).render("#" + containerId);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "PayPal indisponible",
      );
    } finally {
      setSelectedOffer(null);
    }
  }

  const subscriptionOffers = catalog.filter(
    (offer) => offer.kind === "subscription",
  );
  const billingEvents = billing?.events ?? [];

  return (
    <section className="workspace">
      <PageHeading
        eyebrow="FACTURATION"
        title="Une offre qui suit votre activité."
        description="Choisissez une offre récurrente. Le paiement est présenté par PayPal et l’état est confirmé par le backend."
      />

      {error && (
        <FeedbackMessage className="form-error" role="alert">
          {error}
        </FeedbackMessage>
      )}

      {message && <div className="success-message">{message}</div>}

      <div className="billing-banner">
        <div>
          <span className="eyebrow inverse">ÉTAT DU COMPTE</span>
          <h2>{billing?.account?.status ?? "Aucun abonnement actif"}</h2>
        </div>
        <StatusPill>
          {billing?.paypal_configured ? "PayPal prêt" : "PayPal à configurer"}
        </StatusPill>
      </div>

      <div className="plan-grid">
        {subscriptionOffers.map((offer) => (
          <article className="plan-card panel" key={offer.offer_id}>
            <span className="eyebrow">{offer.name_fr ?? offer.name}</span>
            <h2>
              {offer.amount
                ? offer.amount + " " + offer.currency
                : "Sur devis"}
            </h2>
            <p>
              Abonnement récurrent. Vous gardez le contrôle de la validation.
            </p>

            {offer.paypal_plan_id ? (
              <>
                <button
                  className="button button-dark button-wide"
                  disabled={
                    selectedOffer === offer.offer_id ||
                    Boolean(selectedOffer)
                  }
                  onClick={() => void subscribeToOffer(offer)}
                >
                  {selectedOffer === offer.offer_id
                    ? "Chargement PayPal…"
                    : "Choisir cette offre"}
                </button>

                {selectedOffer === offer.offer_id && (
                  <div
                    className="paypal-slot"
                    id={"paypal-" + offer.offer_id}
                  />
                )}
              </>
            ) : (
              <button className="button button-secondary button-wide">
                Nous contacter
              </button>
            )}
          </article>
        ))}
      </div>

      <article className="panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">HISTORIQUE</span>
            <h2>Événements de facturation</h2>
          </div>
        </div>

        {billingEvents.map((event: any, index: number) => (
          <div className="list-row" key={event.id ?? index}>
            <div>
              <b>{event.type ?? event.status ?? "Événement"}</b>
              <p>{event.created_at ?? "—"}</p>
            </div>
            <span>
              {event.amount ? event.amount + " " + event.currency : ""}
            </span>
          </div>
        ))}

        {!billingEvents.length && (
          <FeedbackMessage className="empty">
            Aucun événement.
          </FeedbackMessage>
        )}
      </article>
    </section>
  );
}
