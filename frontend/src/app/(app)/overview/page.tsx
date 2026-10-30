"use client";

import { OverviewPage } from "@/features/dashboard/dashboard.page";
import { useUser } from "@/shared/lib/user-context";

export default function Page() {
  const user = useUser();
  return <OverviewPage name={user.full_name} />;
}
