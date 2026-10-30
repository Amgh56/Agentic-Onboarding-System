"use client";

import { useI18n } from "@/shared/lib/i18n";
import { useOverview } from "./dashboard.controller";

export function OverviewPage({ name }: { name: string }) {
  const { t } = useI18n();
  const { jobCount } = useOverview();

  return (
    <>
      <h2 className="page-title">{t("overview.title")}</h2>
      <p className="muted">{t("overview.welcome")} {name}</p>
      <div className="card stat">
        <span className="muted">{t("overview.jobs")}</span>
        <strong>{jobCount}</strong>
      </div>
    </>
  );
}
