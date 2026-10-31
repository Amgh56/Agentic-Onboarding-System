"use client";

import { useI18n } from "@/shared/lib/i18n";
import { ChartIcon, EmployeesIcon, JobsIcon, SparkleIcon } from "@/shared/components/icons";

type Page = "dashboard" | "messages" | "openings" | "applications" | "employees";

const cardIcons = [<JobsIcon key="a" />, <ChartIcon key="b" />, <EmployeesIcon key="c" />];

/** A placeholder for a page that is not built yet. Only Onboarding works today. */
export function ComingSoon({ page }: { page: Page }) {
  const { t } = useI18n();

  return (
    <>
      <div>
        <h2 className="page-title">{t(`nav.${page}`)}</h2>
        <p className="muted">{t(`soon.${page}.sub`)}</p>
      </div>
      <section className="soon">
        <div className="soon-preview" aria-hidden>
          <div className="soon-stats">
            {[0, 1, 2].map((i) => (
              <div key={i} className="soon-tile">
                <span className="soon-bar soon-bar-short" />
                <span className="soon-bar soon-bar-strong" />
              </div>
            ))}
          </div>
          {[0, 1].map((i) => (
            <div key={i} className={`soon-row ${i === 1 ? "soon-row-faded" : ""}`}>
              <span className="soon-pill" />
              <span className="soon-dot" />
              <span className="soon-lines">
                <span className="soon-bar soon-bar-long" />
                <span className="soon-bar soon-bar-thin" />
              </span>
            </div>
          ))}
        </div>

        <span className="soon-chip"><SparkleIcon />{t("soon.chip")}</span>
        <h3 className="soon-title">{t(`soon.${page}.title`)}</h3>
        <p className="muted">{t("soon.intro")}</p>

        <div className="soon-cards">
          {([1, 2, 3] as const).map((n, index) => (
            <div key={n} className="soon-card">
              <span className="soon-icon">{cardIcons[index]}</span>
              <strong>{t(`soon.${page}.card${n}`)}</strong>
              <span className="muted">{t(`soon.${page}.card${n}.text`)}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
