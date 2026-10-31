"use client";

import { useI18n } from "@/shared/lib/i18n";
import { TextField } from "@/shared/components/TextField";
import { useUser } from "@/shared/lib/user-context";
import { useEmailSettings } from "./email.controller";
import type { EmailProvider } from "./email.model";

const providers: { value: EmailProvider; label: "email.mode.smtp" | "email.mode.mock" }[] = [
  { value: "smtp", label: "email.mode.smtp" },
  { value: "mock", label: "email.mode.mock" },
];

export function EmailSettingsPage() {
  const { t } = useI18n();
  const user = useUser();
  const form = useEmailSettings(user.email);

  if (!form.values) return <p className="muted">{t("common.loading")}</p>;
  const values = form.values;

  return (
    <>
      <h2 className="page-title">{t("email.title")}</h2>
      <p className="muted">{t("email.intro")}</p>
      {!form.isSetUp && <p className="notice">{t("email.notSetUp")}</p>}

      <div className="card setup">
        <div className="field">
          <span className="field-label">{t("email.mode")}</span>
          <div className="choices">
            {providers.map((provider) => (
              <button
                key={provider.value}
                type="button"
                className={values.provider === provider.value ? "choice active" : "choice"}
                onClick={() => form.set("provider", provider.value)}
              >
                {t(provider.label)}
              </button>
            ))}
          </div>
        </div>

        <TextField label="email.address" type="email" value={values.email_address} error={form.errors.email_address} onChange={(v) => form.set("email_address", v)} />

        {values.provider === "smtp" && (
          <>
            <div className="field">
              <TextField
                label="email.password"
                type="password"
                value={values.password}
                error={form.errors.password}
                placeholder={form.hasPassword ? t("email.password.saved") : ""}
                onChange={(v) => form.set("password", v)}
              />
              <span className="muted hint">{t("email.password.hint")}</span>
            </div>
            <div className="field-row">
              <TextField label="email.smtpHost" value={values.smtp_host} onChange={(v) => form.set("smtp_host", v)} />
              <TextField label="email.smtpPort" value={values.smtp_port} error={form.errors.smtp_port} onChange={(v) => form.set("smtp_port", v)} />
              <TextField label="email.imapHost" value={values.imap_host} onChange={(v) => form.set("imap_host", v)} />
              <TextField label="email.imapPort" value={values.imap_port} error={form.errors.imap_port} onChange={(v) => form.set("imap_port", v)} />
            </div>
          </>
        )}

        <label className="field">
          <span className="field-label">{t("email.allowed")}</span>
          <span className="muted hint">{t("email.allowed.hint")}</span>
          <textarea rows={4} dir="ltr" value={values.allowed_recipients} onChange={(e) => form.set("allowed_recipients", e.target.value)} />
        </label>

        {form.serverError && <p className="field-error">{form.serverError}</p>}
        <div className="setup-actions">
          <button className="button" disabled={form.saving} onClick={form.save}>{t("email.save")}</button>
          {form.isSetUp && (
            <button className="button button-light" disabled={form.testing} onClick={form.test}>
              {form.testing ? t("email.testing") : t("email.test")}
            </button>
          )}
          {form.saved && <span className="muted">{t("email.saved")}</span>}
        </div>

        {form.result && (
          <dl className="details connection">
            <dt>{t("email.sending")}</dt>
            <dd className={form.result.smtp.startsWith("Failed") ? "field-error" : "ok-text"}>{form.result.smtp}</dd>
            <dt>{t("email.reading")}</dt>
            <dd className={form.result.imap.startsWith("Failed") ? "field-error" : "ok-text"}>{form.result.imap}</dd>
          </dl>
        )}
      </div>
    </>
  );
}
