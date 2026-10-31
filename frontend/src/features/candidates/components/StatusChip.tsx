"use client";

import { useI18n } from "@/shared/lib/i18n";
import type { CandidateStatus } from "../candidates.model";

const styles: Record<CandidateStatus, string> = {
  draft: "chip chip-draft",
  invited: "chip chip-pending",
  in_progress: "chip chip-pending",
  completed: "chip chip-onboarding",
};

export function StatusChip({ status }: { status: CandidateStatus }) {
  const { t } = useI18n();
  return <span className={styles[status]}>{t(`candidates.status.${status}`)}</span>;
}
