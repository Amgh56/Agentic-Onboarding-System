"use client";

import { useEffect, useState } from "react";
import type { SystemContents } from "./systems.model";
import { getContents } from "./systems.service";

export function useSystems() {
  const [systems, setSystems] = useState<SystemContents[] | null>(null);

  useEffect(() => {
    getContents().then(setSystems);
  }, []);

  return { systems };
}
