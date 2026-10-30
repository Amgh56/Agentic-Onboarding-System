import type { MessageKey } from "@/shared/lib/i18n";
import type { JobForm } from "./jobs.model";

export function validateJob(values: JobForm): Partial<Record<keyof JobForm, MessageKey>> {
  return values.title.trim() ? {} : { title: "error.required" };
}
