"use client";

import { useRef, useState, type ChangeEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { PlusIcon, UploadIcon } from "@/shared/components/icons";
import { useCandidates } from "./candidates.controller";
import { CandidateDialog } from "./components/CandidateDialog";
import { CandidatesTable } from "./components/CandidatesTable";

export function CandidatesPage({ jobId, stages }: { jobId: number; stages: string[] }) {
  const { t } = useI18n();
  const { candidates, importError, add, importCsv } = useCandidates(jobId);
  const [adding, setAdding] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function onFileChosen(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) await importCsv(file);
    event.target.value = "";
  }

  return (
    <>
      <div className="toolbar">
        <input ref={fileInput} type="file" accept=".csv" hidden onChange={onFileChosen} />
        <button className="button button-light" onClick={() => fileInput.current?.click()}>
          <UploadIcon />
          {t("candidates.upload")}
        </button>
        <button className="button" onClick={() => setAdding(true)}>
          <PlusIcon />
          {t("candidates.add")}
        </button>
      </div>
      {importError && <p className="field-error">{importError}</p>}
      {candidates.length === 0 ? (
        <p className="muted">{t("candidates.empty")}</p>
      ) : (
        <CandidatesTable jobId={jobId} stages={stages} candidates={candidates} />
      )}
      {adding && <CandidateDialog onCreate={add} onClose={() => setAdding(false)} />}
    </>
  );
}
