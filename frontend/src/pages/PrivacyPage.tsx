import { useEffect, useState } from "react";

import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { StatusPill } from "@/components/layout/StatusPill";
import { api } from "@/services/api/client";

type PrivacyRequest = {
  id: string;
  request_type: string;
  status: string;
  due_at?: string;
  created_at?: string;
};

type PrivacyRequestsResponse = {
  items?: PrivacyRequest[];
};

const PRIVACY_REQUEST_TYPES = [
  "ACCESS",
  "RECTIFICATION",
  "ERASURE",
  "RESTRICTION",
  "OBJECTION",
  "PORTABILITY",
];

/**
 * Client workspace page for submitting and tracking personal-data requests.
 * The API remains responsible for validating and processing each request.
 */
export function PrivacyPage() {
  const [requests, setRequests] = useState<PrivacyRequest[]>([]);
  const [requestType, setRequestType] = useState("ACCESS");

  async function loadRequests() {
    const response = await api.get<PrivacyRequestsResponse>(
      "/v1/privacy/requests",
    );
    setRequests(response.items ?? []);
  }

  useEffect(() => {
    void loadRequests();
  }, []);

  async function createRequest() {
    await api.post("/v1/privacy/requests", {
      request_type: requestType,
      details: { source: "client" },
    });

    await loadRequests();
  }

  async function exportPersonalData() {
    const response = await api.get<unknown>("/v1/privacy/export");
    const file = new Blob([JSON.stringify(response, null, 2)], {
      type: "application/json",
    });
    const downloadUrl = URL.createObjectURL(file);
    const link = document.createElement("a");

    link.href = downloadUrl;
    link.download = "review-defense-data.json";
    link.click();
  }

  return (
    <section className="workspace">
      <PageHeading
        eyebrow="CONFIDENTIALITÉ"
        title="Vos données, à votre main."
        description="Exportez vos données et exercez vos droits depuis un espace unique."
        action={
          <button
            className="button button-dark"
            onClick={() => void exportPersonalData()}
          >
            Exporter mes données →
          </button>
        }
      />

      <div className="create-bar">
        <select
          value={requestType}
          onChange={(event) => setRequestType(event.target.value)}
        >
          {PRIVACY_REQUEST_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>

        <button
          className="button button-secondary"
          onClick={() => void createRequest()}
        >
          Créer une demande
        </button>
      </div>

      <div className="panel table-panel">
        {requests.map((request) => (
          <div className="case-row" key={request.id}>
            <div className="case-index">R</div>

            <div>
              <b>{request.request_type}</b>
              <p>{request.created_at ?? "—"}</p>
            </div>

            <StatusPill>{request.status}</StatusPill>
            <span>{request.due_at ?? "—"}</span>
          </div>
        ))}

        {!requests.length && (
          <FeedbackMessage className="empty">
            Aucune demande.
          </FeedbackMessage>
        )}
      </div>
    </section>
  );
}
