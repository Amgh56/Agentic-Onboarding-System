export type Candidate = {
  id: number;
  job_id: number;
  full_name_en: string;
  full_name_ar: string;
  phone: string;
  email: string;
  date_of_birth: string;
  stage: string;
  created_at: string;
};

export type CandidateForm = {
  full_name_en: string;
  full_name_ar: string;
  phone: string;
  email: string;
  date_of_birth: string;
};

export type CandidateEvent = {
  id: number;
  actor: "agent" | "hr" | "system";
  title: string;
  detail: string;
  created_at: string;
};

export type JobCounts = {
  job_id: number;
  applicants: number;
  in_progress: number;
  completed: number;
};

// The job's stages are the onboarding steps. The last one means onboarding is finished.
export function getProgress(stages: string[], stage: string) {
  const found = stages.indexOf(stage);
  const index = found === -1 ? 0 : found;
  const completed = index === stages.length - 1;
  return { index, completed, done: completed ? stages.length : index, total: stages.length };
}
