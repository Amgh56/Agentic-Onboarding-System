"use client";

import { useEffect, useState } from "react";
import { getCounts } from "@/features/candidates/candidates.service";
import type { JobCounts } from "@/features/candidates/candidates.model";
import type { Job, JobForm, JobSetup } from "./jobs.model";
import * as jobsService from "./jobs.service";

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [counts, setCounts] = useState<Record<number, JobCounts>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([jobsService.listJobs(), getCounts()])
      .then(([jobList, countList]) => {
        setJobs(jobList);
        setCounts(Object.fromEntries(countList.map((count) => [count.job_id, count])));
      })
      .finally(() => setLoading(false));
  }, []);

  async function createJob(values: JobForm) {
    const job = await jobsService.createJob(values);
    setJobs([...jobs, job]);
  }

  return { jobs, counts, loading, createJob };
}

export function useJob(id: number) {
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    jobsService.getJob(id).then(setJob);
  }, [id]);

  async function saveSetup(setup: JobSetup) {
    if (job) setJob(await jobsService.updateJob(job, setup));
  }

  return { job, saveSetup };
}
