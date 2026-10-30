"use client";

import { useRouter } from "next/navigation";
import type { JobCounts } from "@/features/candidates/candidates.model";
import { useI18n } from "@/shared/lib/i18n";
import { relativeTime } from "@/shared/lib/time";
import { ChevronRightIcon } from "@/shared/components/icons";
import type { Job, JobStatus } from "../jobs.model";
import { StatusSelect } from "./StatusSelect";

type Props = {
  jobs: Job[];
  counts: Record<number, JobCounts>;
  onStatusChange: (job: Job, status: JobStatus) => void;
};

export function JobsTable({ jobs, counts, onStatusChange }: Props) {
  const { t, locale } = useI18n();
  const router = useRouter();

  return (
    <div className="card table-card">
      <table className="table">
        <thead>
          <tr>
            <th>{t("jobs.col.job")}</th>
            <th>{t("jobs.col.template")}</th>
            <th>{t("jobs.col.applicants")}</th>
            <th>{t("jobs.col.inProgress")}</th>
            <th>{t("jobs.col.completed")}</th>
            <th>{t("jobs.col.status")}</th>
            <th>{t("jobs.col.activity")}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="clickable" onClick={() => router.push(`/jobs/${job.id}`)}>
              <td>
                <div className="job-title">{job.title}</div>
                {job.overview && <div className="job-sub">{job.overview}</div>}
              </td>
              <td>{job.procedure ? t("jobs.procedureAdded") : t("jobs.noTemplate")}</td>
              <td>{counts[job.id]?.applicants ?? 0}</td>
              <td>{counts[job.id]?.in_progress ?? 0}</td>
              <td>{counts[job.id]?.completed ?? 0}</td>
              <td>
                <StatusSelect status={job.status} onChange={(status) => onStatusChange(job, status)} />
              </td>
              <td className="muted">{relativeTime(job.created_at, locale)}</td>
              <td className="muted">
                <ChevronRightIcon />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
