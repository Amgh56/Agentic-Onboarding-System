"use client";

import { useI18n, type MessageKey } from "@/shared/lib/i18n";
import { ChevronDownIcon } from "@/shared/components/icons";
import type { JobStatus } from "../jobs.model";

const labels: Record<JobStatus, MessageKey> = {
  draft: "status.draft",
  onboarding: "status.onboarding",
  closed: "status.closed",
};

export function StatusSelect({ status, onChange }: { status: JobStatus; onChange: (status: JobStatus) => void }) {
  const { t } = useI18n();

  return (
    <span className={`chip chip-${status} chip-select`} onClick={(event) => event.stopPropagation()}>
      <select value={status} onChange={(event) => onChange(event.target.value as JobStatus)}>
        {(Object.keys(labels) as JobStatus[]).map((value) => (
          <option key={value} value={value}>{t(labels[value])}</option>
        ))}
      </select>
      <ChevronDownIcon />
    </span>
  );
}
