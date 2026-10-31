import { api, apiBlob } from "@/shared/lib/api-client";
import type { Candidate, CandidateAccounts, CandidateDocument, CandidateEvent, CandidateForm, JobCounts } from "./candidates.model";

export const listCandidates = (jobId: number) => api<Candidate[]>(`/jobs/${jobId}/candidates`);

export const addCandidate = (jobId: number, values: CandidateForm) =>
  api<Candidate>(`/jobs/${jobId}/candidates`, { method: "POST", body: values });

export const addCandidates = (jobId: number, values: CandidateForm[]) =>
  api<Candidate[]>(`/jobs/${jobId}/candidates/bulk`, { method: "POST", body: values });

export function importCsv(jobId: number, file: File) {
  const body = new FormData();
  body.append("file", file);
  return api<Candidate[]>(`/jobs/${jobId}/candidates/import`, { method: "POST", body });
}

export const getCandidate = (id: number) => api<Candidate>(`/candidates/${id}`);

export const listEvents = (id: number) => api<CandidateEvent[]>(`/candidates/${id}/events`);

export const listDocuments = (id: number) => api<CandidateDocument[]>(`/candidates/${id}/documents`);

export const listAccounts = (id: number) => api<CandidateAccounts>(`/candidates/${id}/accounts`);

export const getCounts = () => api<JobCounts[]>("/candidates/counts");

/** Test mode: send a file as if the candidate replied to the documents email. */
export function simulateReply(candidate: Candidate, files: File[]) {
  const body = new FormData();
  body.append("from_address", candidate.email);
  body.append("subject", `Re: documents [ONB-${candidate.id}]`);
  body.append("body", "Here are my documents.");
  files.forEach((file) => body.append("files", file));
  return api(`/mock-inbox`, { method: "POST", body });
}

export async function downloadDocument(document: CandidateDocument) {
  const url = URL.createObjectURL(await apiBlob(`/candidate-documents/${document.id}/download`));
  const link = window.document.createElement("a");
  link.href = url;
  link.download = document.filename;
  link.click();
  URL.revokeObjectURL(url);
}
