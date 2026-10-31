"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CandidatesPage } from "@/features/candidates/candidates.page";
import { useCandidates } from "@/features/candidates/candidates.controller";
import { useEmailReady } from "@/features/email/email.controller";
import { usePlan } from "@/features/plans/plans.controller";
import { startJob } from "@/features/plans/plans.service";
import { PlanReview } from "@/features/plans/components/PlanReview";
import { ChevronLeftIcon } from "@/shared/components/icons";
import { useI18n } from "@/shared/lib/i18n";
import { useJob } from "./jobs.controller";
import type { JobSetup } from "./jobs.model";
import { SetupForm } from "./components/SetupForm";

export function JobDetailPage() {
  const { t } = useI18n();
  const { id } = useParams<{ id: string }>();
  const { job, saveSetup } = useJob(Number(id));
  const planState = usePlan(Number(id));
  const emailReady = useEmailReady();
  const [tab, setTab] = useState<"applicants" | "setup">("applicants");
  const { candidates } = useCandidates(Number(id));
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState("");

  if (!job || planState.loading) return <p className="muted">{t("common.loading")}</p>;

  const waiting = candidates.filter((candidate) => candidate.status === "draft").length;
  const started = starting || (candidates.length > 0 && waiting === 0);

  async function startAgent() {
    setStarting(true);
    setStartError("");
    try {
      await startJob(job!.id);
    } catch (failure) {
      setStarting(false);
      setStartError(failure instanceof Error ? failure.message : "Something went wrong");
    }
  }

  /** Saving the procedure turns it into the plan, and waiting applicants start on their own. */
  async function saveAndApply(setup: JobSetup) {
    const procedureChanged = setup.procedure.trim() !== job!.procedure.trim();
    await saveSetup(setup);
    if (setup.procedure.trim() && (procedureChanged || !planState.plan)) await planState.draft();
  }

  return (
    <>
      <Link href="/jobs" className="back-link back-link-icon">
        <ChevronLeftIcon />
        {t("jobs.back")}
      </Link>
      <div className="page-header">
        <div>
          <h2 className="page-title">{job.title}</h2>
          {job.overview && <p className="muted">{job.overview}</p>}
        </div>
      </div>
      {emailReady === false && (
        <p className="notice">
          {t("email.notSetUpJob")} <Link href="/settings/email">{t("email.openSettings")}</Link>
        </p>
      )}
      <div className="tabs">
        <button className={tab === "applicants" ? "tab active" : "tab"} onClick={() => setTab("applicants")}>
          {t("jobs.tab.applicants")}
        </button>
        <button className={tab === "setup" ? "tab active" : "tab"} onClick={() => setTab("setup")}>
          {t("jobs.tab.setup")}
        </button>
      </div>
      {tab === "applicants" ? (
        <CandidatesPage jobId={job.id} plan={planState.plan} />
      ) : (
        <div className="setup-grid">
          <SetupForm job={job} onSave={saveAndApply} />
          <PlanReview
            plan={planState.plan}
            hasProcedure={job.procedure.trim() !== ""}
            drafting={planState.drafting}
            error={planState.error || startError}
            started={started}
            canStart={!starting && waiting > 0}
            onStart={startAgent}
          />
        </div>
      )}
    </>
  );
}
