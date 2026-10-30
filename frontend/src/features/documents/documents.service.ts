import { api, apiBlob } from "@/shared/lib/api-client";
import type { JobDocument } from "./documents.model";

export const listDocuments = (jobId: number) => api<JobDocument[]>(`/jobs/${jobId}/documents`);

export function uploadDocument(jobId: number, file: File) {
  const body = new FormData();
  body.append("file", file);
  return api<JobDocument>(`/jobs/${jobId}/documents`, { method: "POST", body });
}

export const deleteDocument = (id: number) => api<null>(`/documents/${id}`, { method: "DELETE" });

export async function downloadDocument(document: JobDocument) {
  const url = URL.createObjectURL(await apiBlob(`/documents/${document.id}/download`));
  const link = window.document.createElement("a");
  link.href = url;
  link.download = document.filename;
  link.click();
  URL.revokeObjectURL(url);
}
