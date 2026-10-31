import { ApiError, api } from "@/shared/lib/api-client";
import type { Plan } from "./plans.model";

export async function getPlan(jobId: number): Promise<Plan | null> {
  try {
    return await api<Plan>(`/jobs/${jobId}/plan`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export const draftPlan = (jobId: number) => api<Plan>(`/jobs/${jobId}/plan/draft`, { method: "POST" });

export const startJob = (jobId: number) => api<{ status: string }>(`/jobs/${jobId}/start`, { method: "POST" });

export const approvePlan = (jobId: number) => api<Plan>(`/jobs/${jobId}/plan/approve`, { method: "POST" });
