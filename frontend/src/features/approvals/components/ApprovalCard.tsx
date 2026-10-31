"use client";

import Link from "next/link";
import { useI18n } from "@/shared/lib/i18n";
import { formatDateTime } from "@/shared/lib/time";
import { useDecisionNote } from "../approvals.controller";
import type { Approval } from "../approvals.model";

type Props = {
  approval: Approval;
  showCandidate?: boolean;
  busy: boolean;
  onDecide: (approve: boolean, note: string) => void;
};

export function ApprovalCard({ approval, showCandidate = false, busy, onDecide }: Props) {
  const { t, locale } = useI18n();
  const { note, setNote } = useDecisionNote();
  const isEscalation = approval.kind === "escalation";

  return (
    <div className="approval">
      <div className="approval-head">
        <span className={isEscalation ? "chip chip-closed" : "chip chip-pending"}>{t(`approvals.kind.${approval.kind}`)}</span>
        {showCandidate && (
          <Link href={`/jobs/${approval.job_id}/candidates/${approval.candidate_id}`} className="approval-candidate">
            {approval.candidate_name}
          </Link>
        )}
        <span className="muted approval-time">{formatDateTime(approval.created_at, locale)}</span>
      </div>
      {approval.action && <strong>{approval.action}</strong>}
      <p className="muted">{approval.reason}</p>
      {isEscalation && <p className="hint muted">{t("approvals.escalationHint")}</p>}
      <textarea rows={2} placeholder={t("approvals.note")} value={note} onChange={(e) => setNote(e.target.value)} />
      <div className="approval-actions">
        <button className="button button-small" disabled={busy} onClick={() => onDecide(true, note)}>
          {isEscalation ? t("approvals.continue") : t("approvals.approve")}
        </button>
        <button className="button button-light button-small" disabled={busy} onClick={() => onDecide(false, note)}>
          {t("approvals.decline")}
        </button>
      </div>
    </div>
  );
}
