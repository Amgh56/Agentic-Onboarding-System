"use client";

import { useState, type FormEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { TextField } from "@/shared/components/TextField";
import type { CandidateForm } from "../candidates.model";
import { validateCandidate } from "../candidates.schema";

const empty: CandidateForm = { full_name_en: "", full_name_ar: "", phone: "", email: "", date_of_birth: "" };

type Props = {
  onCreate: (values: CandidateForm) => Promise<void>;
  onClose: () => void;
};

export function CandidateDialog({ onCreate, onClose }: Props) {
  const { t } = useI18n();
  const [values, setValues] = useState(empty);
  const [errors, setErrors] = useState<ReturnType<typeof validateCandidate>>({});
  const [saving, setSaving] = useState(false);

  const set = (field: keyof CandidateForm) => (value: string) => setValues({ ...values, [field]: value });

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateCandidate(values);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    await onCreate(values);
    onClose();
  }

  return (
    <div className="overlay" onMouseDown={onClose}>
      <form className="modal" onMouseDown={(e) => e.stopPropagation()} onSubmit={onSubmit} noValidate>
        <h2>{t("candidates.new")}</h2>
        <TextField label="candidates.nameEn" value={values.full_name_en} error={errors.full_name_en} onChange={set("full_name_en")} />
        <TextField label="candidates.nameAr" value={values.full_name_ar} error={errors.full_name_ar} onChange={set("full_name_ar")} />
        <TextField label="candidates.phone" type="tel" value={values.phone} error={errors.phone} onChange={set("phone")} />
        <TextField label="candidates.email" type="email" value={values.email} error={errors.email} onChange={set("email")} />
        <TextField label="candidates.dob" type="date" value={values.date_of_birth} error={errors.date_of_birth} onChange={set("date_of_birth")} />
        <div className="modal-actions">
          <button type="button" className="button button-light" onClick={onClose}>{t("common.cancel")}</button>
          <button className="button" disabled={saving}>{t("candidates.create")}</button>
        </div>
      </form>
    </div>
  );
}
