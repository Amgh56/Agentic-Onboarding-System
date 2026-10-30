"use client";

import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { ChevronDownIcon } from "@/shared/components/icons";

type Props = {
  name: string;
  email: string;
  onLogout: () => void;
};

export function TopBar({ name, email, onLogout }: Props) {
  const { t, locale, setLocale } = useI18n();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function closeOnOutsideClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, []);

  function switchLanguage() {
    setLocale(locale === "en" ? "ar" : "en");
    setOpen(false);
  }

  return (
    <header className="topbar">
      <h1 className="topbar-title">{t("app.title")}</h1>
      <div className="menu" ref={menuRef}>
        <button className="profile-button" onClick={() => setOpen(!open)}>
          <span className="profile-text">
            <span className="profile-name">{name}</span>
            <span className="profile-email">{email}</span>
          </span>
          <ChevronDownIcon />
        </button>
        {open && (
          <div className="menu-list">
            <button className="menu-item" onClick={switchLanguage}>
              <span>{t("profile.language")}</span>
              <span className="menu-value">{t("profile.otherLanguage")}</span>
            </button>
            <button className="menu-item" onClick={onLogout}>
              {t("profile.logout")}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
