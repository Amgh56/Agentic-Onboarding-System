import { api } from "@/shared/lib/api-client";
import type { Candidate, CandidateEvent, CandidateForm, JobCounts } from "./candidates.model";

export const listCandidates = (jobId: number) => api<Candidate[]>(`/jobs/${jobId}/candidates`);

export const addCandidate = (jobId: number, values: CandidateForm) =>
  api<Candidate>(`/jobs/${jobId}/candidates`, { method: "POST", body: values });

export function importCsv(jobId: number, file: File) {
  const body = new FormData();
  body.append("file", file);
  return api<Candidate[]>(`/jobs/${jobId}/candidates/import`, { method: "POST", body });
}

export const getCandidate = (id: number) => api<Candidate>(`/candidates/${id}`);

export const listEvents = (id: number) => api<CandidateEvent[]>(`/candidates/${id}/events`);

export const moveStage = (candidateId: number, stage: string) =>
  api<Candidate>(`/candidates/${candidateId}/stage`, { method: "PUT", body: { stage } });

export const getCounts = () => api<JobCounts[]>("/candidates/counts");
