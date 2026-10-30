import { listJobs } from "@/features/jobs/jobs.service";

export async function getOverview() {
  const jobs = await listJobs();
  return { jobCount: jobs.length };
}
