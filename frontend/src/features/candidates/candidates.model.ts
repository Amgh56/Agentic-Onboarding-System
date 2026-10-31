export type CandidateStatus = "draft" | "invited" | "in_progress" | "completed";

export type StepOutcome = { outcome: "done" | "skipped"; reason: string };

export type Candidate = {
  id: number;
  job_id: number;
  full_name_en: string;
  full_name_ar: string;
  phone: string;
  email: string;
  date_of_birth: string;
  role: string;
  avatar_url: string;
  status: CandidateStatus;
  stage: string;
  step_status: Record<string, StepOutcome>;
  created_at: string;
};

export type CandidateForm = {
  full_name_en: string;
  full_name_ar: string;
  phone: string;
  email: string;
  date_of_birth: string;
  role: string;
};

export type CandidateEvent = {
  id: number;
  actor: "agent" | "hr" | "system";
  title: string;
  detail: string;
  created_at: string;
};

export type CandidateDocument = {
  id: number;
  filename: string;
  content_type: string;
  status: "received" | "valid" | "rejected" | "disputed";
  reason: string;
  created_at: string;
};

export type Account = {
  id: number;
  system_key: string;
  display_name: string;
  address: string;
  groups: string[];
  status: string;
  created_at: string;
};

export type Ticket = {
  id: number;
  item: string;
  status: string;
  requester: string;
  created_at: string;
};

export type CandidateAccounts = { accounts: Account[]; tickets: Ticket[] };

export type JobCounts = {
  job_id: number;
  applicants: number;
  in_progress: number;
  completed: number;
};

export function stepsDone(candidate: Candidate, stepIds: string[]): number {
  return stepIds.filter((id) => candidate.step_status[id]).length;
}
