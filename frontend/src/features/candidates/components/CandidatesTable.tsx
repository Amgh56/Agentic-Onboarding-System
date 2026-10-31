"use client";

import { useRouter } from "next/navigation";
import { useI18n } from "@/shared/lib/i18n";
import { ChevronRightIcon } from "@/shared/components/icons";
import { stepsDone, type Candidate } from "../candidates.model";
import { Avatar } from "./Avatar";
import { StatusChip } from "./StatusChip";

type Props = {
  jobId: number;
  stepIds: string[];
  candidates: Candidate[];
};

export function CandidatesTable({ jobId, stepIds, candidates }: Props) {
  const { t, locale } = useI18n();
  const router = useRouter();

  return (
    <div className="card table-card">
      <table className="table">
        <thead>
          <tr>
            <th>{t("candidates.col.name")}</th>
            <th>{t("candidates.email")}</th>
            <th>{t("candidates.col.status")}</th>
            <th>{t("candidates.col.progress")}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr key={candidate.id} className="clickable" onClick={() => router.push(`/jobs/${jobId}/candidates/${candidate.id}`)}>
              <td>
                <div className="applicant">
                  <Avatar candidate={candidate} />
                  <div>
                    <div className="job-title">{locale === "ar" ? candidate.full_name_ar : candidate.full_name_en}</div>
                    <div className="job-sub">{candidate.role}</div>
                  </div>
                </div>
              </td>
              <td>{candidate.email}</td>
              <td>
                <StatusChip status={candidate.status} />
              </td>
              <td className="muted">
                {stepIds.length > 0 && `${stepsDone(candidate, stepIds)} ${t("candidates.of")} ${stepIds.length} ${t("candidates.steps")}`}
              </td>
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
