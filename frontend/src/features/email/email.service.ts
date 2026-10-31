import { ApiError, api } from "@/shared/lib/api-client";
import type { ConnectionResult, EmailSettings, EmailSettingsForm } from "./email.model";

export async function getSettings(): Promise<EmailSettings | null> {
  try {
    return await api<EmailSettings>("/email-settings");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function saveSettings(values: EmailSettingsForm) {
  return api<EmailSettings>("/email-settings", {
    method: "PUT",
    body: {
      provider: values.provider,
      email_address: values.email_address.trim(),
      password: values.password.trim() || null,
      smtp_host: values.smtp_host.trim(),
      smtp_port: Number(values.smtp_port),
      imap_host: values.imap_host.trim(),
      imap_port: Number(values.imap_port),
      allowed_recipients: values.allowed_recipients.split("\n").map((line) => line.trim()).filter(Boolean),
    },
  });
}

export const testConnection = () => api<ConnectionResult>("/email-settings/test", { method: "POST" });
