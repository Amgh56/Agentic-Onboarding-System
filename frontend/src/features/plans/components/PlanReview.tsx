"use client";

import { useI18n } from "@/shared/lib/i18n";
import type { Plan } from "../plans.model";

type Props = {
  plan: Plan | null;
  hasProcedure: boolean;
  drafting: boolean;
  error: string;
  started: boolean;
  canStart: boolean;
  onStart: () => void;
};

export function PlanReview({ plan, hasProcedure, drafting, error, started, canStart, onStart }: Props) {
  const { t } = useI18n();

  return (
    <section className="card setup">
      <header className="card-header">
        <h3>{t("plan.title")}</h3>
      </header>

      {!plan && !drafting && <p className="muted">{hasProcedure ? t("plan.none") : t("plan.needProcedure")}</p>}
      {drafting && <p className="banner">{t("plan.drafting")}</p>}
      {error && <p className="field-error">{error}</p>}

      {plan && (
        <>
          <div className="field">
            <span className="field-label">{t("plan.steps")}</span>
            <ol className="timeline">
              {plan.steps.map((step, index) => (
                <li key={step.id} className="t-step">
                  <div className="t-marker">
                    <span className="t-circle">{index + 1}</span>
                  </div>
                  <div className="t-body">
                    <div className="t-title">{step.title}</div>
                    {step.details && <div className="t-details">{step.details}</div>}
                  </div>
                </li>
              ))}
            </ol>
          </div>
          <div className="field">
            <span className="field-label">{t("plan.departments")}</span>
            {plan.departments.length === 0 && <span className="muted">{t("plan.noDepartments")}</span>}
            <ul className="rows">
              {plan.departments.map((department) => (
                <li key={department.name} className="row">
                  <div>
                    <strong>{department.name}</strong>
                    <div className="muted">{department.handles}</div>
                  </div>
                  {department.email ? (
                    <span dir="ltr" className="muted">{department.email}</span>
                  ) : (
                    <span className="field-error">{t("plan.noEmail")}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {hasProcedure && (
        <div className="setup-actions">
          <button className="button" disabled={drafting || !canStart} onClick={onStart}>
            {started ? t("plan.started") : t("plan.start")}
          </button>
        </div>
      )}
    </section>
  );
}
