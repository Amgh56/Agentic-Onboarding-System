"use client";

import { useEffect, useRef } from "react";

/** Calls the callback every few seconds while the page is open, so the agent's work shows up on its own. */
export function usePolling(callback: () => void, milliseconds: number) {
  const latest = useRef(callback);

  useEffect(() => {
    latest.current = callback;
  });

  useEffect(() => {
    const timer = setInterval(() => latest.current(), milliseconds);
    return () => clearInterval(timer);
  }, [milliseconds]);
}
