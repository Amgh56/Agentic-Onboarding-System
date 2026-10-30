"use client";

import Link from "next/link";
import { useI18n } from "@/shared/lib/i18n";
import { useLoginForm, useSignupForm } from "./auth.controller";
import { TextField } from "@/shared/components/TextField";

export function LoginPage() {
  const { t } = useI18n();
  const form = useLoginForm();

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={form.onSubmit} noValidate>
        <h1>{t("auth.login.title")}</h1>
        <TextField label="auth.email" type="email" value={form.values.email} error={form.errors.email} onChange={(v) => form.onChange("email", v)} />
        <TextField label="auth.password" type="password" value={form.values.password} error={form.errors.password} onChange={(v) => form.onChange("password", v)} />
        {form.serverError && <p className="field-error">{form.serverError}</p>}
        <button className="button" disabled={form.submitting}>{t("auth.login.submit")}</button>
        <p className="auth-switch">
          {t("auth.login.noAccount")} <Link href="/signup">{t("auth.login.toSignup")}</Link>
        </p>
      </form>
    </main>
  );
}

export function SignupPage() {
  const { t } = useI18n();
  const form = useSignupForm();

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={form.onSubmit} noValidate>
        <h1>{t("auth.signup.title")}</h1>
        <TextField label="auth.companyName" value={form.values.company_name} error={form.errors.company_name} onChange={(v) => form.onChange("company_name", v)} />
        <TextField label="auth.fullName" value={form.values.full_name} error={form.errors.full_name} onChange={(v) => form.onChange("full_name", v)} />
        <TextField label="auth.email" type="email" value={form.values.email} error={form.errors.email} onChange={(v) => form.onChange("email", v)} />
        <TextField label="auth.password" type="password" value={form.values.password} error={form.errors.password} onChange={(v) => form.onChange("password", v)} />
        {form.serverError && <p className="field-error">{form.serverError}</p>}
        <button className="button" disabled={form.submitting}>{t("auth.signup.submit")}</button>
        <p className="auth-switch">
          {t("auth.signup.haveAccount")} <Link href="/login">{t("auth.signup.toLogin")}</Link>
        </p>
      </form>
    </main>
  );
}
