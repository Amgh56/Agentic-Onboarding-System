export type JobStatus = "onboarding" | "closed";

export type StartMode = "auto" | "notify" | "ask_first";

export type Job = {
  id: number;
  title: string;
  overview: string;
  description: string;
  status: JobStatus;
  start_mode: StartMode;
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

export type JobSetup = Pick<Job, "procedure" | "start_mode">;
