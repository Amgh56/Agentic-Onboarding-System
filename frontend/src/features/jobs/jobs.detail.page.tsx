"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CandidatesPage } from "@/features/candidates/candidates.page";
import { useI18n } from "@/shared/lib/i18n";
import { useJob } from "./jobs.controller";
import { SetupForm } from "./components/SetupForm";
import { StatusSelect } from "./components/StatusSelect";

export function JobDetailPage() {
  const { t } = useI18n();
  const { id } = useParams<{ id: string }>();
  const { job, changeStatus, saveSetup } = useJob(Number(id));
  const [tab, setTab] = useState<"applicants" | "setup">("applicants");

  if (!job) return <p className="muted">{t("common.loading")}</p>;

  return (
    <>
      <Link href="/jobs" className="back-link">{t("jobs.back")}</Link>
      <div className="page-header">
        <div>
          <h2 className="page-title">{job.title}</h2>
          {job.overview && <p className="muted">{job.overview}</p>}
        </div>
        <StatusSelect status={job.status} onChange={changeStatus} />
      </div>
      <div className="tabs">
        <button className={tab === "applicants" ? "tab active" : "tab"} onClick={() => setTab("applicants")}>
          {t("jobs.tab.applicants")}
        </button>
        <button className={tab === "setup" ? "tab active" : "tab"} onClick={() => setTab("setup")}>
          {t("jobs.tab.setup")}
        </button>
      </div>
      {tab === "applicants" ? (
        <CandidatesPage jobId={job.id} stages={job.stages} />
      ) : (
        <SetupForm job={job} onSave={saveSetup} />
      )}
    </>
  );
}
