"use client";

import { useState, type FormEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { DateSelect } from "@/shared/components/DateSelect";
import { TextField } from "@/shared/components/TextField";
import type { CandidateForm } from "../candidates.model";
import { validateCandidate } from "../candidates.schema";

const empty: CandidateForm = { full_name_en: "", full_name_ar: "", phone: "", email: "", date_of_birth: "", role: "" };

type Props = {
  onCreate: (values: CandidateForm[]) => Promise<void>;
  onClose: () => void;
};

/** Add one or more applicants. A finished applicant folds into one line so the next one can be added. */
export function CandidateDialog({ onCreate, onClose }: Props) {
  const { t } = useI18n();
  const [applicants, setApplicants] = useState<CandidateForm[]>([empty]);
  const [open, setOpen] = useState(0);
  const [errors, setErrors] = useState<ReturnType<typeof validateCandidate>>({});
  const [saving, setSaving] = useState(false);
  const [serverError, setServerError] = useState("");

  const values = applicants[open];
  const set = (field: keyof CandidateForm) => (value: string) =>
    setApplicants(applicants.map((applicant, i) => (i === open ? { ...applicant, [field]: value } : applicant)));

  /** Check the open applicant before leaving it. */
  function openIsValid() {
    const found = validateCandidate(values);
    setErrors(found);
    return Object.keys(found).length === 0;
  }

  function addAnother() {
    if (!openIsValid()) return;
    setApplicants([...applicants, empty]);
    setOpen(applicants.length);
  }

  function edit(index: number) {
    if (index === open || !openIsValid()) return;
    setOpen(index);
  }

  function remove(index: number) {
    setApplicants(applicants.filter((_, i) => i !== index));
    setOpen(index < open ? open - 1 : Math.min(open, applicants.length - 2));
    setErrors({});
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const invalid = applicants.findIndex((applicant) => Object.keys(validateCandidate(applicant)).length > 0);
    if (invalid !== -1) {
      setOpen(invalid);
      setErrors(validateCandidate(applicants[invalid]));
      return;
    }
    setSaving(true);
    try {
      await onCreate(applicants);
      onClose();
    } catch (failure) {
      setServerError(failure instanceof Error ? failure.message : "Something went wrong");
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={onClose}>
      <form className="modal" onMouseDown={(e) => e.stopPropagation()} onSubmit={onSubmit} noValidate>
        <h2>{t("candidates.newMany")}</h2>

        {applicants.map((applicant, index) =>
          index === open ? (
            <div key={index} className="applicant-form">
              {applicants.length > 1 && <span className="field-label">{t("candidates.applicant")} {index + 1}</span>}
              <TextField label="candidates.nameEn" value={values.full_name_en} error={errors.full_name_en} onChange={set("full_name_en")} />
              <TextField label="candidates.nameAr" value={values.full_name_ar} error={errors.full_name_ar} onChange={set("full_name_ar")} />
              <TextField label="candidates.email" type="email" value={values.email} error={errors.email} onChange={set("email")} />
              <TextField label="candidates.phone" type="tel" value={values.phone} error={errors.phone} onChange={set("phone")} />
              <DateSelect key={`dob-${index}`} label="candidates.dob" value={values.date_of_birth} error={errors.date_of_birth} onChange={set("date_of_birth")} />
              <TextField label="candidates.role" value={values.role} error={errors.role} onChange={set("role")} />
            </div>
          ) : (
            <div key={index} className="applicant-summary">
              <div>
                <strong>{applicant.full_name_en}</strong>
                <div className="muted">{applicant.email}</div>
              </div>
              <div className="applicant-summary-actions">
                <button type="button" className="link-button" onClick={() => edit(index)}>{t("candidates.edit")}</button>
                <button type="button" className="icon-button" onClick={() => remove(index)} aria-label={t("candidates.remove")}>×</button>
              </div>
            </div>
          ),
        )}

        <button type="button" className="button button-light button-small" onClick={addAnother}>
          + {t("candidates.addAnother")}
        </button>
        {serverError && <p className="field-error">{serverError}</p>}
        <div className="modal-actions">
          <button type="button" className="button button-light" onClick={onClose}>{t("common.cancel")}</button>
          <button className="button" disabled={saving}>
            {t("candidates.addN")}
          </button>
        </div>
      </form>
    </div>
  );
}
