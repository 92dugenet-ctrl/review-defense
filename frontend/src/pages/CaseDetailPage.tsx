import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { BackLink } from "@/components/layout/BackLink";
import { DetailMeta } from "@/components/layout/DetailMeta";
import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { SignalRow } from "@/components/layout/SignalRow";
import { StatusPill } from "@/components/layout/StatusPill";
import { api } from "@/services/api/client";

type Evidence = {
  evidence_id: string;
  filename: string;
  evidence_type: string;
  status: string;
};

type CaseWorkspace = {
  state: string;
  priority: string;
  review: {
    author_display_name?: string | null;
    text?: string;
    rating?: number;
    source?: string;
  };
  evidence: Evidence[];
  evidence_coverage?: number;
  claims?: Array<{
    claim_id: string;
    text: string;
    claim_type: string;
    status: string;
  }>;
  policies?: Array<{
    code: string;
    status: string;
    justification?: string;
  }>;
  contradictions?: Array<{
    contradiction_id: string;
    description: string;
    requires_human_review: boolean;
  }>;
};

type EvidenceTask = {
  task_id: string;
  evidence_requirement: string;
  priority: string;
  status: string;
};

type CaseWorkspaceResponse = {
  workspace: CaseWorkspace;
  evidence_tasks: EvidenceTask[];
  requires_human_review: boolean;
};

/**
 * Displays the evidence workspace for a single case.
 * The case ID comes from the route; all workspace data is loaded from the API.
 */
export function CaseDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState<CaseWorkspaceResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let isActive = true;

    if (id) {
      api
        .get<CaseWorkspaceResponse>(`/v1/cases/${id}/workspace`)
        .then((response) => {
          if (isActive) {
            setData(response);
          }
        })
        .catch((caught) => {
          if (isActive) {
            setError(
              caught instanceof Error
                ? caught.message
                : "Impossible de charger le dossier",
            );
          }
        });
    }

    // Ignore late responses if the user navigates to another case.
    return () => {
      isActive = false;
    };
  }, [id]);

  if (error) {
    return (
      <section className="workspace">
        <BackLink to="/app/cases">← Tous les dossiers</BackLink>
        <FeedbackMessage className="form-error" role="alert">
          {error}
        </FeedbackMessage>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="workspace">
        <FeedbackMessage className="empty">
          Chargement du dossier…
        </FeedbackMessage>
      </section>
    );
  }

  const workspace = data.workspace;
  const review = workspace.review;
  const evidence = workspace.evidence ?? [];
  const evidenceTasks = data.evidence_tasks ?? [];

  return (
    <section className="workspace">
      <BackLink to="/app/cases">← Tous les dossiers</BackLink>

      <PageHeading
        eyebrow="DOSSIER"
        title={id ?? "Dossier"}
        description="Workspace de décision et de preuves."
        action={<StatusPill>{workspace.state ?? "OPEN"}</StatusPill>}
      />

      <div className="content-grid">
        <article className="panel">
          <span className="eyebrow">AVIS</span>
          <h2>{review.author_display_name ?? "Avis sélectionné"}</h2>
          <blockquote>{review.text ?? "Aucun texte disponible."}</blockquote>

          <DetailMeta>
            <span>Note</span>
            <b>{review.rating ?? "—"}</b>

            <span>Source</span>
            <b>{review.source ?? "—"}</b>

            <span>Priorité</span>
            <b>{workspace.priority ?? "—"}</b>
          </DetailMeta>
        </article>

        <article className="panel">
          <span className="eyebrow">PREUVES</span>
          <h2>Éléments du dossier</h2>

          {evidence.map((item) => (
            <SignalRow key={item.evidence_id}>
              {item.filename} · {item.status}
            </SignalRow>
          ))}

          {!evidence.length && (
            <FeedbackMessage className="empty">
              Aucune preuve enregistrée.
            </FeedbackMessage>
          )}

          <div className="panel-head">
            <h3>Éléments à réunir</h3>
          </div>

          {evidenceTasks.map((task) => (
            <SignalRow key={task.task_id}>
              {task.evidence_requirement} · {task.status}
            </SignalRow>
          ))}

          {!evidenceTasks.length && (
            <FeedbackMessage className="empty">
              Aucun élément manquant identifié.
            </FeedbackMessage>
          )}

          <p>
            Couverture des preuves :{" "}
            {Math.round((workspace.evidence_coverage ?? 0) * 100)}%
          </p>
        </article>
      </div>
    </section>
  );
}
