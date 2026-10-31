import type { MessageKey } from "@/shared/lib/i18n";
import type { EmailSettingsForm } from "./email.model";

export function validateEmailSettings(
  values: EmailSettingsForm,
  hasPassword: boolean,
): Partial<Record<keyof EmailSettingsForm, MessageKey>> {
  const errors: Partial<Record<keyof EmailSettingsForm, MessageKey>> = {};
  if (!values.email_address.includes("@")) errors.email_address = "error.email";
  if (values.provider === "smtp") {
    if (!hasPassword && !values.password.trim()) errors.password = "error.required";
    if (!/^\d+$/.test(values.smtp_port)) errors.smtp_port = "error.port";
    if (!/^\d+$/.test(values.imap_port)) errors.imap_port = "error.port";
  }
  return errors;
}
