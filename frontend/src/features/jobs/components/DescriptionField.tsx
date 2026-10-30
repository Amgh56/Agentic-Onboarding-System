"use client";

import { useRef, type ChangeEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { UploadIcon } from "@/shared/components/icons";

type Props = {
  value: string;
  rows?: number;
  onChange: (value: string) => void;
};

export function DescriptionField({ value, rows = 5, onChange }: Props) {
  const { t } = useI18n();
  const fileInput = useRef<HTMLInputElement>(null);

  async function onFileChosen(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onChange(await file.text());
    event.target.value = "";
  }

  return (
    <div className="field">
      <span className="field-label">{t("jobs.description")}</span>
      <span className="muted hint">{t("jobs.description.hint")}</span>
      <textarea rows={rows} value={value} onChange={(event) => onChange(event.target.value)} />
      <input ref={fileInput} type="file" accept=".txt,.md" hidden onChange={onFileChosen} />
      <button type="button" className="button button-light button-small" onClick={() => fileInput.current?.click()}>
        <UploadIcon />
        {t("jobs.description.upload")}
      </button>
    </div>
  );
}
