export type PlanStep = {
  id: string;
  title: string;
  details: string;
};

export type PlanDepartment = {
  name: string;
  email: string | null;
  handles: string;
};

export type Plan = {
  id: number;
  job_id: number;
  steps: PlanStep[];
  departments: PlanDepartment[];
  approved: boolean;
  created_at: string;
};
