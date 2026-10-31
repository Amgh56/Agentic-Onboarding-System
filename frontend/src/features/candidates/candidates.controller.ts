"use client";

import { useCallback, useEffect, useState } from "react";
import { decideApproval, listApprovals } from "@/features/approvals/approvals.service";
import type { Approval } from "@/features/approvals/approvals.model";
import { getSettings } from "@/features/email/email.service";
import { getJob } from "@/features/jobs/jobs.service";
import type { Job } from "@/features/jobs/jobs.model";
import { getPlan } from "@/features/plans/plans.service";
import type { Plan } from "@/features/plans/plans.model";
import type { Candidate, CandidateAccounts, CandidateDocument, CandidateEvent, CandidateForm } from "./candidates.model";
import * as candidatesService from "./candidates.service";
import { usePolling } from "@/shared/lib/use-polling";

const message = (failure: unknown) => (failure instanceof Error ? failure.message : "Something went wrong");

export function useCandidates(jobId: number) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    candidatesService.listCandidates(jobId).then(setCandidates).catch(() => {}); // the next poll tries again
  }, [jobId]);

  useEffect(() => {
    load();
  }, [load]);
  usePolling(load, 5000);

  async function addMany(values: CandidateForm[]) {
    const created = await candidatesService.addCandidates(jobId, values);
    setCandidates((current) => [...current, ...created]);
  }

  async function importCsv(file: File) {
    try {
      const created = await candidatesService.importCsv(jobId, file);
      setCandidates((current) => [...current, ...created]);
      setError("");
    } catch (failure) {
      setError(message(failure));
    }
  }

  return { candidates, error, addMany, importCsv };
}

type Profile = {
  candidate: Candidate;
  job: Job;
  plan: Plan | null;
  events: CandidateEvent[];
  documents: CandidateDocument[];
  accounts: CandidateAccounts;
  approvals: Approval[];
  testMode: boolean;
};

export function useCandidateProfile(candidateId: number) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");

  const load = useCallback(async () => {
    try {
      const candidate = await candidatesService.getCandidate(candidateId);
      const [job, plan, events, documents, accounts, approvals, email] = await Promise.all([
        getJob(candidate.job_id),
        getPlan(candidate.job_id),
        candidatesService.listEvents(candidateId),
        candidatesService.listDocuments(candidateId),
        candidatesService.listAccounts(candidateId),
        listApprovals({ candidate_id: candidateId, status: "pending" }),
        getSettings(),
      ]);
      setProfile({ candidate, job, plan, events, documents, accounts, approvals, testMode: email?.provider === "mock" });
      setLoadError("");
    } catch (failure) {
      setLoadError(message(failure));
    }
  }, [candidateId]);

  useEffect(() => {
    load();
  }, [load]);
  usePolling(load, busy ? 2000 : 5000); // refresh faster while the agent runs, so each step shows as it happens

  /** The agent runs while the request is open, so this can take a while. */
  async function work(action: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(message(failure));
    }
    await load();
    setBusy(false);
  }

  return {
    profile,
    busy,
    error: error || (profile ? "" : loadError), // a failed refresh is ignored once the page has data
    decide: (approval: Approval, approve: boolean, note: string) => work(() => decideApproval(approval.id, approve, note)),
    simulateReply: (files: File[]) => work(() => candidatesService.simulateReply(profile!.candidate, files)),
    download: candidatesService.downloadDocument,
  };
}
