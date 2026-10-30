import { api } from "@/shared/lib/api-client";
import type { Job, JobForm, JobUpdate } from "./jobs.model";

export const listJobs = () => api<Job[]>("/jobs");

export const getJob = (id: number) => api<Job>(`/jobs/${id}`);

export const createJob = (values: JobForm) => api<Job>("/jobs", { method: "POST", body: values });

// PUT replaces the whole job, so every field is sent.
export function updateJob(job: Job, changes: Partial<JobUpdate>) {
  const { id, created_at, ...current } = job;
  return api<Job>(`/jobs/${id}`, { method: "PUT", body: { ...current, ...changes } });
}
