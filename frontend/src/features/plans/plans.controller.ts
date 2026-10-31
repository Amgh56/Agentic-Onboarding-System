"use client";

import { useEffect, useState } from "react";
import type { Plan } from "./plans.model";
import * as plansService from "./plans.service";

export function usePlan(jobId: number) {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [drafting, setDrafting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    plansService.getPlan(jobId).then(setPlan).finally(() => setLoading(false));
  }, [jobId]);

  async function draft() {
    setDrafting(true);
    setError("");
    try {
      setPlan(await plansService.draftPlan(jobId));
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Something went wrong");
    }
    setDrafting(false);
  }

  async function approve() {
    setPlan(await plansService.approvePlan(jobId));
  }

  return { plan, loading, drafting, error, draft, approve };
}
