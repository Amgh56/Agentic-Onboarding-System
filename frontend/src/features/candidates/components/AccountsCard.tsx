"use client";

import { useI18n } from "@/shared/lib/i18n";
import type { CandidateAccounts } from "../candidates.model";

const systemNames: Record<string, string> = {
  work_email: "Work email",
  erp: "ERP",
  github: "GitHub",
  slack: "Slack",
  teams: "Microsoft Teams",
};

export function AccountsCard({ accounts }: { accounts: CandidateAccounts }) {
  const { t } = useI18n();
  const empty = accounts.accounts.length === 0 && accounts.tickets.length === 0;

  return (
    <section className="card">
      <header className="card-header"><h3>{t("accounts.title")}</h3></header>
      {empty && <p className="muted">{t("accounts.empty")}</p>}
      <ul className="rows">
        {accounts.accounts.map((account) => (
          <li key={account.id} className="row">
            <div className="row-main">
              <div className="row-title">
                <strong>{systemNames[account.system_key] ?? account.system_key}</strong>
                <span className={account.status === "invited" ? "chip chip-pending" : "chip chip-onboarding"}>
                  {account.status === "invited" ? t("accounts.invited") : t("accounts.created")}
                </span>
              </div>
              <div className="muted" dir="ltr">{account.address}</div>
              {account.groups.length > 0 && <div className="muted">{account.groups.join(", ")}</div>}
            </div>
          </li>
        ))}
        {accounts.tickets.map((ticket) => (
          <li key={`ticket-${ticket.id}`} className="row">
            <div className="row-main">
              <div className="row-title">
                <strong>{t("accounts.ticket")}</strong>
                <span className="chip chip-onboarding">{t("accounts.created")}</span>
              </div>
              <div className="muted">{ticket.item}</div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
