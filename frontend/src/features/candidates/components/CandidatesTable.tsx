"use client";

import { useRouter } from "next/navigation";
import { useI18n } from "@/shared/lib/i18n";
import { ChevronRightIcon } from "@/shared/components/icons";
import { getProgress, type Candidate } from "../candidates.model";

type Props = {
  jobId: number;
  stages: string[];
  candidates: Candidate[];
};

export function CandidatesTable({ jobId, stages, candidates }: Props) {
  const { t } = useI18n();
  const router = useRouter();

  return (
    <div className="card table-card">
      <table className="table">
        <thead>
          <tr>
            <th>{t("candidates.col.name")}</th>
            <th>{t("candidates.email")}</th>
            <th>{t("candidates.phone")}</th>
            <th>{t("candidates.col.stage")}</th>
            <th>{t("candidates.col.progress")}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => {
            const progress = getProgress(stages, candidate.stage);
            return (
              <tr
                key={candidate.id}
                className="clickable"
                onClick={() => router.push(`/jobs/${jobId}/candidates/${candidate.id}`)}
              >
                <td>
                  <div className="job-title">{candidate.full_name_en}</div>
                  <div className="job-sub" dir="rtl">{candidate.full_name_ar}</div>
                </td>
                <td>{candidate.email}</td>
                <td dir="ltr">{candidate.phone}</td>
                <td>
                  <span className={progress.completed ? "chip chip-onboarding" : "chip chip-pending"}>
                    {stages[progress.index]}
                  </span>
                </td>
                <td className="muted">
                  {progress.done} {t("candidates.of")} {progress.total} {t("candidates.steps")}
                </td>
                <td className="muted">
                  <ChevronRightIcon />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
