"use client";

import { useState, type FormEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import type { JobForm as JobFormValues, JobStatus } from "../jobs.model";
import { validateJob } from "../jobs.schema";
import { DescriptionField } from "./DescriptionField";

const empty: JobFormValues = { title: "", overview: "", description: "", status: "draft" };
const statuses: JobStatus[] = ["draft", "onboarding", "closed"];

type Props = {
  onCreate: (values: JobFormValues) => Promise<void>;
  onClose: () => void;
};

export function JobForm({ onCreate, onClose }: Props) {
  const { t } = useI18n();
  const [values, setValues] = useState(empty);
  const [errors, setErrors] = useState<ReturnType<typeof validateJob>>({});
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateJob(values);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    await onCreate(values);
    onClose();
  }

  return (
    <div className="overlay" onMouseDown={onClose}>
      <form className="modal" onMouseDown={(e) => e.stopPropagation()} onSubmit={onSubmit} noValidate>
        <h2>{t("jobs.new")}</h2>
        <label className="field">
          <span className="field-label">{t("jobs.jobTitle")}</span>
          <input autoFocus value={values.title} onChange={(e) => setValues({ ...values, title: e.target.value })} />
          {errors.title && <span className="field-error">{t(errors.title)}</span>}
        </label>
        <label className="field">
          <span className="field-label">{t("jobs.overview")}</span>
          <input value={values.overview} onChange={(e) => setValues({ ...values, overview: e.target.value })} />
        </label>
        <DescriptionField value={values.description} onChange={(description) => setValues({ ...values, description })} />
        <label className="field">
          <span className="field-label">{t("jobs.status")}</span>
          <select value={values.status} onChange={(e) => setValues({ ...values, status: e.target.value as JobStatus })}>
            {statuses.map((status) => (
              <option key={status} value={status}>{t(`status.${status}`)}</option>
            ))}
          </select>
        </label>
        <div className="modal-actions">
          <button type="button" className="button button-light" onClick={onClose}>{t("common.cancel")}</button>
          <button className="button" disabled={saving}>{t("jobs.create")}</button>
        </div>
      </form>
    </div>
  );
}
