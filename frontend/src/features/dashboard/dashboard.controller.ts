"use client";

import { useEffect, useState } from "react";
import { getOverview } from "./dashboard.service";

export function useOverview() {
  const [jobCount, setJobCount] = useState(0);

  useEffect(() => {
    getOverview().then((overview) => setJobCount(overview.jobCount));
  }, []);

  return { jobCount };
}
