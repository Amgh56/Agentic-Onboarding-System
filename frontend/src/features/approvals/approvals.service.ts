import { api } from "@/shared/lib/api-client";
import type { Approval } from "./approvals.model";

export function listApprovals(filters: { candidate_id?: number; status?: string } = {}) {
  const query = new URLSearchParams();
  if (filters.candidate_id !== undefined) query.set("candidate_id", String(filters.candidate_id));
  if (filters.status) query.set("status", filters.status);
  return api<Approval[]>(`/approvals?${query}`);
}

export const decideApproval = (id: number, approve: boolean, note: string) =>
  api<Approval>(`/approvals/${id}/decide`, { method: "POST", body: { approve, note } });
