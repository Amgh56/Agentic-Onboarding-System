"use client";

import { useI18n } from "@/shared/lib/i18n";
import { CheckIcon, ClockIcon } from "@/shared/components/icons";
import { getProgress } from "../candidates.model";

type Props = {
  stages: string[];
  stage: string;
  onMove: (stage: string) => void;
};

export function Timeline({ stages, stage, onMove }: Props) {
  const { t } = useI18n();
  const { index, completed, done, total } = getProgress(stages, stage);

  return (
    <section className="card">
      <header className="card-header">
        <h3>{t("candidates.timeline")}</h3>
        <span className="muted">
          {done} {t("candidates.of")} {total} {t("candidates.steps")}
        </span>
      </header>
      <ol className="timeline">
        {stages.map((name, i) => {
          const state = i < index || (completed && i === index) ? "done" : i === index ? "current" : "upcoming";
          return (
            <li key={name} className={`t-step ${state}`}>
              <div className="t-marker">
                <span className="t-circle">
                  {state === "done" ? <CheckIcon /> : state === "current" ? <ClockIcon /> : i + 1}
                </span>
              </div>
              <div className="t-body">
                <div className="t-title">{name}</div>
                <div className="t-sub">{t(`candidates.step.${state}`)}</div>
                {i === index && (
                  <div className="t-actions">
                    {i > 0 && (
                      <button className="button button-light button-small" onClick={() => onMove(stages[i - 1])}>
                        {t("candidates.moveBack")}
                      </button>
                    )}
                    {i < stages.length - 1 && (
                      <button className="button button-small" onClick={() => onMove(stages[i + 1])}>
                        {t("candidates.markDone")}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
