"use client";

import { useI18n } from "@/shared/lib/i18n";
import { CheckIcon, ClockIcon } from "@/shared/components/icons";
import type { PlanStep } from "@/features/plans/plans.model";
import { stepsDone, type Candidate } from "../candidates.model";

type State = "done" | "skipped" | "current" | "upcoming";

export function Timeline({ steps, candidate }: { steps: PlanStep[] | null; candidate: Candidate }) {
  const { t } = useI18n();

  if (!steps) {
    return (
      <section className="card">
        <header className="card-header"><h3>{t("candidates.timeline")}</h3></header>
        <p className="muted">{t("candidates.noPlan")}</p>
      </section>
    );
  }

  const started = candidate.status === "invited" || candidate.status === "in_progress";
  const current = started ? steps.findIndex((step) => !candidate.step_status[step.id]) : -1;
  const stateOf = (index: number): State => {
    const outcome = candidate.step_status[steps[index].id]?.outcome;
    if (outcome) return outcome;
    return index === current ? "current" : "upcoming";
  };

  return (
    <section className="card">
      <header className="card-header">
        <h3>{t("candidates.timeline")}</h3>
        <span className="muted">
          {stepsDone(candidate, steps.map((step) => step.id))} {t("candidates.of")} {steps.length} {t("candidates.steps")}
        </span>
      </header>
      <ol className="timeline">
        {steps.map((step, index) => {
          const state = stateOf(index);
          return (
            <li key={step.id} className={`t-step ${state}`}>
              <div className="t-marker">
                <span className="t-circle">
                  {state === "done" ? <CheckIcon /> : state === "current" ? <ClockIcon /> : state === "skipped" ? "–" : index + 1}
                </span>
              </div>
              <div className="t-body">
                <div className="t-title">{step.title}</div>
                <div className="t-sub">{t(`candidates.step.${state}`)}</div>
                {step.details && <div className="t-details">{step.details}</div>}
                {state === "skipped" && candidate.step_status[step.id]?.reason && (
                  <div className="t-details">{candidate.step_status[step.id].reason}</div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
