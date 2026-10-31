"use client";

import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { BellIcon, ChevronDownIcon, GearIcon } from "@/shared/components/icons";

type Props = {
  name: string;
  email: string;
  onLogout: () => void;
};

export function TopBar({ name, email, onLogout }: Props) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function closeOnOutsideClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, []);

  return (
    <header className="topbar">
      <h1 className="topbar-title">{t("app.title")}</h1>
      <div className="topbar-actions">
        {/* Design only for now: these do nothing yet. */}
        <button className="icon-tile" aria-label="Settings"><GearIcon /></button>
        <button className="icon-tile" aria-label="Notifications"><BellIcon /></button>
        <span className="topbar-divider" />
        <div className="menu" ref={menuRef}>
          <button className="profile-button" onClick={() => setOpen(!open)}>
            <img className="profile-photo" src="/avatars/hr.jpg" alt="" />
            <span className="profile-text">
              <span className="profile-name">{name}</span>
              <span className="profile-email">{email}</span>
            </span>
            <ChevronDownIcon />
          </button>
          {open && (
            <div className="menu-list">
              <button className="menu-item" onClick={onLogout}>
                {t("profile.logout")}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
