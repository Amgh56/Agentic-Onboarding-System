import type { MessageKey } from "@/shared/lib/i18n";
import type { CandidateForm } from "./candidates.model";

export function validateCandidate(values: CandidateForm): Partial<Record<keyof CandidateForm, MessageKey>> {
  const errors: Partial<Record<keyof CandidateForm, MessageKey>> = {};
  for (const field of Object.keys(values) as (keyof CandidateForm)[]) {
    if (!values[field].trim()) errors[field] = "error.required";
  }
  return errors;
}
