"use client";

import { useState } from "react";

/** The note HR types before approving or declining one item. */
export function useDecisionNote() {
  const [note, setNote] = useState("");
  return { note, setNote };
}
