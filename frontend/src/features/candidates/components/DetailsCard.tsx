"use client";

import { useI18n } from "@/shared/lib/i18n";
import type { Candidate } from "../candidates.model";

export function DetailsCard({ candidate }: { candidate: Candidate }) {
  const { t, locale } = useI18n();

  return (
    <section className="card">
      <header className="card-header">
        <h3>{t("candidates.details")}</h3>
      </header>
      <dl className="details">
        {candidate.role && (
          <>
            <dt>{t("candidates.role")}</dt>
            <dd>{candidate.role}</dd>
          </>
        )}
        <dt>{t("candidates.email")}</dt>
        <dd>{candidate.email}</dd>
        <dt>{t("candidates.phone")}</dt>
        <dd dir="ltr">{candidate.phone}</dd>
        <dt>{t("candidates.dob")}</dt>
        <dd>{new Date(candidate.date_of_birth).toLocaleDateString(locale, { dateStyle: "medium" })}</dd>
      </dl>
    </section>
  );
}
