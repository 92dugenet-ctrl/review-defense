// Centre de notifications : affiche les messages en attente et propose des actions explicites.
// La liste provient de /v1/notifications ; livrer ou annuler déclenche une commande API dédiée.
// Le navigateur ne transmet qu'une intention : l'état réel, les autorisations et la livraison
// asynchrone restent gérés par le backend et ses workers.

import { useEffect, useState } from "react";

import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { api } from "@/services/api/client";

type Notification = {
  notification_id: string;
  status?: string;
  subject?: string;
  body?: string;
  created_at?: string;
};

type NotificationsResponse = {
  items?: Notification[];
};

type NotificationAction = "deliver" | "cancel";

/** Displays queued notifications and exposes their explicit delivery actions. */
export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);

  async function loadNotifications() {
    try {
      const response = await api.get<NotificationsResponse>(
        "/v1/notifications",
      );
      setNotifications(response.items ?? []);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Impossible de charger les notifications.",
      );
    }
  }

  useEffect(() => {
    void loadNotifications();
  }, []);

  async function runAction(
    notificationId: string,
    action: NotificationAction,
  ) {
    const actionKey = `${notificationId}-${action}`;

    setBusyAction(actionKey);
    setError("");

    try {
      await api.post(
        `/v1/notifications/${notificationId}/${action}`,
      );
      await loadNotifications();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Action impossible.",
      );
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <section className="workspace">
      <PageHeading
        as="header"
        className="module-heading"
        eyebrow="NOTIFICATIONS"
        title="Ce qui demande votre attention."
        description="Les notifications restent traçables et chaque livraison est contrôlée."
      />

      {error && (
        <FeedbackMessage className="form-error" role="alert">
          {error}
        </FeedbackMessage>
      )}

      <div className="notification-list">
        {notifications.map((notification) => {
          const deliveryKey = `${notification.notification_id}-deliver`;
          const cancellationKey = `${notification.notification_id}-cancel`;

          return (
            <article
              className="notification-row"
              key={notification.notification_id}
            >
              <div>
                <span>{notification.status ?? "EN ATTENTE"}</span>
                <h2>{notification.subject ?? "Notification"}</h2>
                <p>{notification.body ?? "—"}</p>
                <small>{notification.created_at ?? "—"}</small>
              </div>

              <div className="notification-actions">
                <button
                  disabled={busyAction !== null}
                  onClick={() =>
                    void runAction(
                      notification.notification_id,
                      "deliver",
                    )
                  }
                >
                  {busyAction === deliveryKey ? "Livraison…" : "Livrer"}
                </button>

                <button
                  disabled={busyAction !== null}
                  onClick={() =>
                    void runAction(
                      notification.notification_id,
                      "cancel",
                    )
                  }
                >
                  {busyAction === cancellationKey ? "Annulation…" : "Annuler"}
                </button>
              </div>
            </article>
          );
        })}

        {!notifications.length && (
          <FeedbackMessage className="module-empty">
            Aucune notification.
          </FeedbackMessage>
        )}
      </div>
    </section>
  );
}
