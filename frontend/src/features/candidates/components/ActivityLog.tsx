"use client";

import { useI18n } from "@/shared/lib/i18n";
import { formatDateTime } from "@/shared/lib/time";
import type { CandidateEvent } from "../candidates.model";

export function ActivityLog({ events }: { events: CandidateEvent[] }) {
  const { t, locale } = useI18n();

  return (
    <section className="card">
      <header className="card-header">
        <h3>{t("candidates.activity")}</h3>
      </header>
      {events.length === 0 && <p className="muted">{t("candidates.activity.empty")}</p>}
      <ul className="activity">
        {events.map((event) => (
          <li key={event.id}>
            <span className="muted activity-time">{formatDateTime(event.created_at, locale)}</span>
            <div>
              <div className="activity-title">
                {event.title}
                <span className={`actor actor-${event.actor}`}>{t(`actor.${event.actor}`)}</span>
              </div>
              {event.detail && <div className="muted">{event.detail}</div>}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
