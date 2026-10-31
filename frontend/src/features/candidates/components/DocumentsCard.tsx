"use client";

import { useRef, type ChangeEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { UploadIcon } from "@/shared/components/icons";
import type { CandidateDocument } from "../candidates.model";

const chip: Record<CandidateDocument["status"], string> = {
  received: "chip chip-draft",
  valid: "chip chip-onboarding",
  rejected: "chip chip-closed",
  disputed: "chip chip-pending",
};

// Accepted documents first, rejected ones last. The sort is stable, so each group keeps its order.
const rank: Record<CandidateDocument["status"], number> = { valid: 0, received: 1, disputed: 1, rejected: 2 };

type Props = {
  documents: CandidateDocument[];
  testMode: boolean;
  busy: boolean;
  onDownload: (document: CandidateDocument) => void;
  onSimulate: (files: File[]) => void;
};

export function DocumentsCard({ documents, testMode, busy, onDownload, onSimulate }: Props) {
  const { t } = useI18n();
  const fileInput = useRef<HTMLInputElement>(null);

  function onFileChosen(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length > 0) onSimulate(files);
    event.target.value = "";
  }

  return (
    <section className="card">
      <header className="card-header"><h3>{t("docs.title")}</h3></header>
      {documents.length === 0 && <p className="muted">{t("docs.empty")}</p>}
      <ul className="rows">
        {[...documents].sort((a, b) => rank[a.status] - rank[b.status]).map((document) => (
          <li key={document.id} className="row">
            <div className="row-main">
              <div className="row-title">
                <span>{document.filename}</span>
                <span className={chip[document.status]}>{t(`docs.status.${document.status}`)}</span>
              </div>
              {document.reason && <div className="muted">{document.reason}</div>}
            </div>
            <button className="button button-light button-small" onClick={() => onDownload(document)}>
              {t("docs.download")}
            </button>
          </li>
        ))}
      </ul>
      {testMode && (
        <div className="simulate">
          <input ref={fileInput} type="file" multiple hidden onChange={onFileChosen} />
          <button className="button button-light button-small" disabled={busy} onClick={() => fileInput.current?.click()}>
            <UploadIcon />
            {t("docs.simulate")}
          </button>
          <span className="muted hint">{t("docs.simulate.hint")}</span>
        </div>
      )}
    </section>
  );
}
