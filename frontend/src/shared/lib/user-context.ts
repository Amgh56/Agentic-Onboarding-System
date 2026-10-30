"use client";

import { createContext, useContext } from "react";

type CurrentUser = { full_name: string; email: string };

export const UserContext = createContext<CurrentUser | null>(null);

export function useUser() {
  const user = useContext(UserContext);
  if (!user) throw new Error("useUser must be used inside the app layout");
  return user;
}
