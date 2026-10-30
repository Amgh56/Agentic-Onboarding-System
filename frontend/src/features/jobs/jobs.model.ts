export type JobStatus = "draft" | "onboarding" | "closed";

export type Job = {
  id: number;
  template_id: number | null;
  title: string;
  overview: string;
  description: string;
  status: JobStatus;
  procedure: string;
  stages: string[];
  created_at: string;
};

export type JobForm = {
  title: string;
  overview: string;
  description: string;
  status: JobStatus;
};

export type JobUpdate = Omit<Job, "id" | "created_at">;

export type JobSetup = Pick<Job, "description" | "procedure">;
