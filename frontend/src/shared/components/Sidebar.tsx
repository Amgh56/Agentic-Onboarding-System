"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/shared/lib/i18n";
import { JobsIcon, OverviewIcon } from "@/shared/components/icons";

const items = [
  { href: "/overview", label: "nav.overview", icon: <OverviewIcon /> },
  { href: "/jobs", label: "nav.jobs", icon: <JobsIcon /> },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <aside className="sidebar">
      <nav>
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname.startsWith(item.href) ? "active" : ""}`}
          >
            {item.icon}
            {t(item.label)}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
