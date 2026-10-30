"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useI18n } from "@/shared/lib/i18n";
import { ChevronLeftIcon } from "@/shared/components/icons";
import { useCandidateProfile } from "./candidates.controller";
import { getProgress } from "./candidates.model";
import { ActivityLog } from "./components/ActivityLog";
import { DetailsCard } from "./components/DetailsCard";
import { Timeline } from "./components/Timeline";

const initials = (name: string) =>
  name.split(" ").filter(Boolean).slice(0, 2).map((word) => word[0].toUpperCase()).join("");

export function CandidateProfilePage() {
  const { t } = useI18n();
  const { candidateId } = useParams<{ candidateId: string }>();
  const { candidate, job, events, move } = useCandidateProfile(Number(candidateId));

  if (!candidate || !job) return <p className="muted">{t("common.loading")}</p>;

  const progress = getProgress(job.stages, candidate.stage);

  return (
    <>
      <Link href={`/jobs/${job.id}`} className="back-link back-link-icon">
        <ChevronLeftIcon />
        {job.title}
      </Link>
      <div className="profile-header">
        <span className="avatar avatar-large">{initials(candidate.full_name_en)}</span>
        <div>
          <div className="profile-name-row">
            <h2 className="page-title">{candidate.full_name_en}</h2>
            <span className={progress.completed ? "chip chip-onboarding" : "chip chip-pending"}>
              {progress.completed ? t("candidates.completed") : job.stages[progress.index]}
            </span>
          </div>
          <p className="muted">{candidate.email} · <span dir="ltr">{candidate.phone}</span></p>
        </div>
      </div>
      <div className="profile-grid">
        <Timeline stages={job.stages} stage={candidate.stage} onMove={move} />
        <div className="profile-side">
          <DetailsCard candidate={candidate} />
          <ActivityLog events={events} />
        </div>
      </div>
    </>
  );
}
