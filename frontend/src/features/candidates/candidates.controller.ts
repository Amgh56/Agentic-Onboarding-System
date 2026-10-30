"use client";

import { useEffect, useState } from "react";
import { getJob } from "@/features/jobs/jobs.service";
import type { Job } from "@/features/jobs/jobs.model";
import type { Candidate, CandidateEvent, CandidateForm } from "./candidates.model";
import * as candidatesService from "./candidates.service";

export function useCandidates(jobId: number) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [importError, setImportError] = useState("");

  useEffect(() => {
    candidatesService.listCandidates(jobId).then(setCandidates);
  }, [jobId]);

  async function add(values: CandidateForm) {
    const candidate = await candidatesService.addCandidate(jobId, values);
    setCandidates([...candidates, candidate]);
  }

  async function importCsv(file: File) {
    try {
      const created = await candidatesService.importCsv(jobId, file);
      setCandidates([...candidates, ...created]);
      setImportError("");
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "Something went wrong");
    }
  }

  return { candidates, importError, add, importCsv };
}

export function useCandidateProfile(candidateId: number) {
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [events, setEvents] = useState<CandidateEvent[]>([]);

  useEffect(() => {
    candidatesService.getCandidate(candidateId).then(async (found) => {
      setCandidate(found);
      setJob(await getJob(found.job_id));
    });
    candidatesService.listEvents(candidateId).then(setEvents);
  }, [candidateId]);

  async function move(stage: string) {
    setCandidate(await candidatesService.moveStage(candidateId, stage));
    setEvents(await candidatesService.listEvents(candidateId));
  }

  return { candidate, job, events, move };
}
