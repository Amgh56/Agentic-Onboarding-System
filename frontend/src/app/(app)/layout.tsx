"use client";

import { useCurrentUser } from "@/features/auth/auth.controller";
import { Sidebar } from "@/shared/components/Sidebar";
import { TopBar } from "@/shared/components/TopBar";
import { UserContext } from "@/shared/lib/user-context";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useCurrentUser();

  if (!user) return null;

  return (
    <UserContext.Provider value={user}>
      <div className="shell">
        <TopBar name={user.full_name} email={user.email} onLogout={logout} />
        <div className="shell-body">
          <Sidebar />
          <main className="content">{children}</main>
        </div>
      </div>
    </UserContext.Provider>
  );
}
