// Liste des dossiers visibles pour l'organisation de la session courante.
// Le chargement lit /v1/cases puis transforme la réponse en lignes de navigation vers le détail.
// La page ne calcule pas elle-même les droits ni le périmètre tenant : l'API filtre et autorise
// les données avant de les retourner au navigateur.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { StatusPill } from "@/components/layout/StatusPill";
import { api } from "@/services/api/client";

type CaseSummary = {
  case_id: string;
  status: string;
  priority?: string;
};

type CasesResponse = {
  items?: CaseSummary[];
};

/** Lists the cases available to the currently authenticated organization. */
export function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<CasesResponse>("/v1/cases")
      .then((response) => setCases(response.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="workspace">
      <PageHeading
        eyebrow="DOSSIERS"
        title="Un dossier par décision."
        description="Suivez le statut, les preuves et les prochaines actions sans perdre le contexte."
      />

      <div className="panel table-panel">
        {loading ? (
          <FeedbackMessage className="empty">
            Chargement…
          </FeedbackMessage>
        ) : (
          cases.map((item) => (
            <Link
              className="case-row"
              key={item.case_id}
              to={`/app/cases/${item.case_id}`}
            >
              <div className="case-index">D</div>

              <div>
                <b>{item.case_id}</b>
                <p>
                  {item.status} · priorité {item.priority ?? "standard"}
                </p>
              </div>

              <StatusPill>{item.status}</StatusPill>
              <span>→</span>
            </Link>
          ))
        )}

        {!loading && !cases.length && (
          <FeedbackMessage className="empty">
            Aucun dossier. Créez-en un depuis un avis.
          </FeedbackMessage>
        )}
      </div>
    </section>
  );
}
