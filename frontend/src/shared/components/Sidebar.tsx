"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/shared/lib/i18n";
import {
  ApplicationsIcon, DashboardIcon, EmployeesIcon, JobsIcon, MessagesIcon, OnboardingIcon,
} from "@/shared/components/icons";

// Only Onboarding is built. The other pages are placeholders for now.
const groups = [
  {
    items: [
      { href: "/dashboard", label: "nav.dashboard", icon: <DashboardIcon /> },
      { href: "/messages", label: "nav.messages", icon: <MessagesIcon /> },
    ],
  },
  {
    title: "nav.recruitment",
    items: [
      { href: "/job-openings", label: "nav.openings", icon: <JobsIcon /> },
      { href: "/applications", label: "nav.applications", icon: <ApplicationsIcon /> },
      { href: "/jobs", label: "nav.onboarding", icon: <OnboardingIcon /> },
      { href: "/employees", label: "nav.employees", icon: <EmployeesIcon /> },
    ],
  },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <aside className="sidebar">
      <nav>
        {groups.map((group, index) => (
          <div key={index} className="nav-group">
            {"title" in group && <div className="nav-title">{t(group.title)}</div>}
            {group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item ${pathname.startsWith(item.href) ? "active" : ""}`}
              >
                {item.icon}
                {t(item.label)}
              </Link>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
