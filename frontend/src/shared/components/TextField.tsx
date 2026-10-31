import { useI18n, type MessageKey } from "@/shared/lib/i18n";

type Props = {
  label: MessageKey;
  value: string;
  error?: MessageKey;
  type?: string;
  placeholder?: string;
  onChange: (value: string) => void;
};

export function TextField({ label, value, error, type = "text", placeholder, onChange }: Props) {
  const { t } = useI18n();
  return (
    <label className="field">
      <span className="field-label">{t(label)}</span>
      <input type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} />
      {error && <span className="field-error">{t(error)}</span>}
    </label>
  );
}
