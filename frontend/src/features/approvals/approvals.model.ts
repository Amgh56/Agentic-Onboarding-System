export type ApprovalKind = "approval" | "escalation" | "notice";

export type Approval = {
  id: number;
  candidate_id: number;
  candidate_name: string;
  job_id: number;
  kind: ApprovalKind;
  action: string;
  reason: string;
  status: "pending" | "approved" | "declined" | "done";
  decision_note: string;
  created_at: string;
  decided_at: string | null;
};
