"use client";

import { useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { PlusIcon } from "@/shared/components/icons";
import { useJobs } from "./jobs.controller";
import { JobForm } from "./components/JobForm";
import { JobsEmpty } from "./components/JobsEmpty";
import { JobsTable } from "./components/JobsTable";

export function JobsPage() {
  const { t } = useI18n();
  const { jobs, counts, loading, createJob, changeStatus } = useJobs();
  const [creating, setCreating] = useState(false);

  if (loading) return <p className="muted">{t("common.loading")}</p>;

  return (
    <>
      <div className="page-header">
        <h2 className="page-title">{t("jobs.title")}</h2>
        {jobs.length > 0 && (
          <button className="button" onClick={() => setCreating(true)}>
            <PlusIcon />
            {t("jobs.new")}
          </button>
        )}
      </div>
      {jobs.length === 0 ? (
        <JobsEmpty onCreate={() => setCreating(true)} />
      ) : (
        <JobsTable jobs={jobs} counts={counts} onStatusChange={changeStatus} />
      )}
      {creating && <JobForm onCreate={createJob} onClose={() => setCreating(false)} />}
    </>
  );
}
