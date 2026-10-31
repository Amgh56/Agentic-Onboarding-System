"use client";

import { useState } from "react";
import type { Plan } from "@/features/plans/plans.model";
import { useI18n } from "@/shared/lib/i18n";
import { PlusIcon } from "@/shared/components/icons";
import { useCandidates } from "./candidates.controller";
import { CandidateDialog } from "./components/CandidateDialog";
import { CandidatesTable } from "./components/CandidatesTable";

export function CandidatesPage({ jobId, plan }: { jobId: number; plan: Plan | null }) {
  const { t } = useI18n();
  const { candidates, error, addMany } = useCandidates(jobId);
  const [adding, setAdding] = useState(false);
  const hasProcedure = Boolean(plan?.approved);

  return (
    <>
      <div className="toolbar">
        <button className="button" onClick={() => setAdding(true)}>
          <PlusIcon />
          {t("candidates.add")}
        </button>
      </div>
      {!hasProcedure && <p className="notice">{t("candidates.waitingForProcedure")}</p>}
      {error && <p className="field-error">{error}</p>}
      {candidates.length === 0 ? (
        <p className="muted">{t("candidates.empty")}</p>
      ) : (
        <CandidatesTable jobId={jobId} stepIds={plan?.steps.map((step) => step.id) ?? []} candidates={candidates} />
      )}
      {adding && <CandidateDialog onCreate={addMany} onClose={() => setAdding(false)} />}
    </>
  );
}
