"use client";

import { useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { DocumentsEditor } from "@/features/documents/components/DocumentsEditor";
import type { Job, JobSetup } from "../jobs.model";
import { DescriptionField } from "./DescriptionField";

export function SetupForm({ job, onSave }: { job: Job; onSave: (setup: JobSetup) => Promise<void> }) {
  const { t } = useI18n();
  const [description, setDescription] = useState(job.description);
  const [procedure, setProcedure] = useState(job.procedure);
  const [saved, setSaved] = useState(false);

  async function save() {
    await onSave({ description, procedure });
    setSaved(true);
  }

  function edit<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value);
      setSaved(false);
    };
  }

  return (
    <div className="card setup">
      <DescriptionField value={description} rows={8} onChange={edit(setDescription)} />
      <label className="field">
        <span className="field-label">{t("jobs.procedure")}</span>
        <span className="muted hint">{t("jobs.procedure.hint")}</span>
        <textarea rows={8} value={procedure} onChange={(e) => edit(setProcedure)(e.target.value)} />
      </label>
      <div className="field">
        <span className="field-label">{t("jobs.documents")}</span>
        <span className="muted hint">{t("jobs.documents.hint")}</span>
        <DocumentsEditor jobId={job.id} />
      </div>
      <div className="setup-actions">
        <button className="button" onClick={save}>{t("common.save")}</button>
        {saved && <span className="muted">{t("jobs.saved")}</span>}
      </div>
    </div>
  );
}
