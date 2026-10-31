"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ApprovalCard } from "@/features/approvals/components/ApprovalCard";
import { useI18n } from "@/shared/lib/i18n";
import { ChevronLeftIcon } from "@/shared/components/icons";
import { useCandidateProfile } from "./candidates.controller";
import { AccountsCard } from "./components/AccountsCard";
import { ActivityLog } from "./components/ActivityLog";
import { Avatar } from "./components/Avatar";
import { DetailsCard } from "./components/DetailsCard";
import { DocumentsCard } from "./components/DocumentsCard";
import { StatusChip } from "./components/StatusChip";
import { Timeline } from "./components/Timeline";

export function CandidateProfilePage() {
  const { t, locale } = useI18n();
  const { candidateId } = useParams<{ candidateId: string }>();
  const { profile, busy, error, decide, simulateReply, download } = useCandidateProfile(Number(candidateId));

  if (!profile) return <p className="muted">{t("common.loading")}</p>;
  const { candidate, job, plan } = profile;

  return (
    <>
      <Link href={`/jobs/${job.id}`} className="back-link back-link-icon">
        <ChevronLeftIcon />
        {job.title}
      </Link>
      <div className="profile-header">
        <Avatar candidate={candidate} large />
        <div className="profile-main">
          <div className="profile-name-row">
            <h2 className="page-title">{locale === "ar" ? candidate.full_name_ar : candidate.full_name_en}</h2>
            <StatusChip status={candidate.status} />
          </div>
          <p className="muted">{candidate.email} · <span dir="ltr">{candidate.phone}</span></p>
        </div>
      </div>
      {candidate.status === "draft" && !plan?.approved && <p className="notice">{t("candidates.waitingForProcedure")}</p>}
      {busy && <p className="banner">{t("candidates.working")}</p>}
      {error && <p className="field-error">{error}</p>}

      <div className="profile-grid">
        <div className="profile-side">
          <Timeline steps={plan?.approved ? plan.steps : null} candidate={candidate} />
          <AccountsCard accounts={profile.accounts} />
        </div>
        <div className="profile-side">
          {profile.approvals.length > 0 && (
            <section className="card attention">
              <header className="card-header"><h3>{t("approvals.title")}</h3></header>
              <div className="approval-list">
                {profile.approvals.map((approval) => (
                  <ApprovalCard
                    key={approval.id}
                    approval={approval}
                    busy={busy}
                    onDecide={(approve, note) => decide(approval, approve, note)}
                  />
                ))}
              </div>
            </section>
          )}
          <DocumentsCard
            documents={profile.documents}
            testMode={profile.testMode && candidate.status !== "draft" && candidate.status !== "completed"}
            busy={busy}
            onDownload={download}
            onSimulate={simulateReply}
          />
          <ActivityLog events={profile.events} />
          <DetailsCard candidate={candidate} />
        </div>
      </div>
    </>
  );
}
