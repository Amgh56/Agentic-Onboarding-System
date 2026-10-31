"use client";

import { useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { PenIcon } from "@/shared/components/icons";
import { DocumentsEditor } from "@/features/documents/components/DocumentsEditor";
import type { Job, JobSetup } from "../jobs.model";

export function SetupForm({ job, onSave }: { job: Job; onSave: (setup: JobSetup) => Promise<void> }) {
  const { t } = useI18n();
  const [procedure, setProcedure] = useState(job.procedure);
  const [saved, setSaved] = useState(job.procedure.trim() !== "");

  async function save() {
    await onSave({ procedure, start_mode: job.start_mode });
    setSaved(true);
  }

  return (
    <div className="card setup">
      <label className="field">
        <span className="field-label">{t("jobs.procedure")}</span>
        <span className="muted hint">{t("jobs.procedure.hint")}</span>
        <textarea
          rows={10}
          className={saved ? "locked" : ""}
          readOnly={saved}
          tabIndex={saved ? -1 : 0}
          value={procedure}
          onChange={(e) => setProcedure(e.target.value)}
        />
      </label>
      <div className="field">
        <span className="field-label">{t("jobs.documents")}</span>
        <span className="muted hint">{t("jobs.documents.hint")}</span>
        <DocumentsEditor jobId={job.id} />
      </div>
      <div className="setup-actions">
        {saved ? (
          <button className="button button-light" onClick={() => setSaved(false)}>
            <PenIcon />
            {t("common.edit")}
          </button>
        ) : (
          <button className="button" onClick={save}>{t("common.save")}</button>
        )}
      </div>
    </div>
  );
}
