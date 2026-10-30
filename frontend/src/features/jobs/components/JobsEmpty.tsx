"use client";

import { useI18n } from "@/shared/lib/i18n";
import { JobsIcon, PlusIcon } from "@/shared/components/icons";

export function JobsEmpty({ onCreate }: { onCreate: () => void }) {
  const { t } = useI18n();

  return (
    <div className="card empty">
      <span className="empty-icon">
        <JobsIcon />
      </span>
      <h3>{t("jobs.empty.title")}</h3>
      <p className="muted">{t("jobs.empty.text")}</p>
      <button className="button" onClick={onCreate}>
        <PlusIcon />
        {t("jobs.empty.cta")}
      </button>
    </div>
  );
}
