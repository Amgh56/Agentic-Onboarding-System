"use client";

import { useEffect, useState } from "react";
import type { ConnectionResult, EmailSettings, EmailSettingsForm } from "./email.model";
import { validateEmailSettings } from "./email.schema";
import * as emailService from "./email.service";

function toForm(settings: EmailSettings | null, defaultEmail: string): EmailSettingsForm {
  return {
    provider: settings?.provider ?? "smtp",
    email_address: settings?.email_address ?? defaultEmail,
    password: "",
    smtp_host: settings?.smtp_host ?? "smtp.gmail.com",
    smtp_port: String(settings?.smtp_port ?? 587),
    imap_host: settings?.imap_host ?? "imap.gmail.com",
    imap_port: String(settings?.imap_port ?? 993),
    allowed_recipients: (settings?.allowed_recipients ?? []).join("\n"),
  };
}

/** null while loading, then whether the company has email (or test mode) set up. */
export function useEmailReady() {
  const [ready, setReady] = useState<boolean | null>(null);

  useEffect(() => {
    emailService.getSettings().then((settings) => setReady(settings !== null));
  }, []);

  return ready;
}

export function useEmailSettings(defaultEmail: string) {
  const [values, setValues] = useState<EmailSettingsForm | null>(null);
  const [isSetUp, setIsSetUp] = useState(false);
  const [hasPassword, setHasPassword] = useState(false);
  const [errors, setErrors] = useState<ReturnType<typeof validateEmailSettings>>({});
  const [serverError, setServerError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<ConnectionResult | null>(null);

  useEffect(() => {
    emailService.getSettings().then((settings) => {
      setValues(toForm(settings, defaultEmail));
      setIsSetUp(settings !== null);
      setHasPassword(settings?.has_password ?? false);
    });
  }, [defaultEmail]);

  function set(field: keyof EmailSettingsForm, value: string) {
    if (!values) return;
    setValues({ ...values, [field]: value });
    setSaved(false);
    setResult(null);
  }

  async function save() {
    if (!values) return;
    const found = validateEmailSettings(values, hasPassword);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    setServerError("");
    try {
      const settings = await emailService.saveSettings(values);
      setValues(toForm(settings, defaultEmail));
      setIsSetUp(true);
      setHasPassword(settings.has_password);
      setSaved(true);
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Something went wrong");
    }
    setSaving(false);
  }

  async function test() {
    setTesting(true);
    setResult(await emailService.testConnection());
    setTesting(false);
  }

  return { values, isSetUp, hasPassword, errors, serverError, saving, saved, testing, result, set, save, test };
}
