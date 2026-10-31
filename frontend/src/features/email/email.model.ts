export type EmailProvider = "smtp" | "mock";

export type EmailSettings = {
  provider: EmailProvider;
  email_address: string;
  smtp_host: string;
  smtp_port: number;
  imap_host: string;
  imap_port: number;
  allowed_recipients: string[];
  has_password: boolean;
};

export type EmailSettingsForm = {
  provider: EmailProvider;
  email_address: string;
  password: string;
  smtp_host: string;
  smtp_port: string;
  imap_host: string;
  imap_port: string;
  allowed_recipients: string;
};

export type ConnectionResult = {
  ok: boolean;
  smtp: string;
  imap: string;
};
