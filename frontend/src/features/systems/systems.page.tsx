"use client";

import { useI18n } from "@/shared/lib/i18n";
import { useSystems } from "./systems.controller";

export function SystemsPage() {
  const { t, locale } = useI18n();
  const { systems } = useSystems();

  if (!systems) return <p className="muted">{t("common.loading")}</p>;

  return (
    <>
      <h2 className="page-title">{t("systems.title")}</h2>
      <p className="muted">{t("systems.intro")}</p>
      <div className="systems-grid">
        {systems.map((system) => (
          <section key={system.key} className="card">
            <header className="card-header">
              <h3>{locale === "ar" ? system.name_ar : system.name}</h3>
              <span className="muted">{system.accounts.length + system.tickets.length}</span>
            </header>
            {system.accounts.length + system.tickets.length === 0 && <p className="muted">{t("systems.empty")}</p>}
            <ul className="rows">
              {system.accounts.map((account) => (
                <li key={account.id} className="row">
                  <div className="row-main">
                    <div className="row-title">
                      <strong>{account.display_name}</strong>
                      <span className={account.status === "invited" ? "chip chip-pending" : "chip chip-onboarding"}>
                        {account.status === "invited" ? t("accounts.invited") : t("accounts.created")}
                      </span>
                    </div>
                    <div className="muted" dir="ltr">{account.address}</div>
                    {account.groups.length > 0 && <div className="muted">{account.groups.join(", ")}</div>}
                  </div>
                </li>
              ))}
              {system.tickets.map((ticket) => (
                <li key={ticket.id} className="row">
                  <div className="row-main">
                    <div className="row-title">
                      <strong>{ticket.item}</strong>
                      <span className="chip chip-draft">{ticket.status}</span>
                    </div>
                    <div className="muted">{ticket.requester}</div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </>
  );
}
