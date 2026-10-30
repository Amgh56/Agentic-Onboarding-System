"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import { en } from "@/shared/locales/en";
import { ar } from "@/shared/locales/ar";

export type Locale = "en" | "ar";
export type MessageKey = keyof typeof en;

const messages: Record<Locale, Record<MessageKey, string>> = { en, ar };

type I18n = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: MessageKey) => string;
};

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ initialLocale, children }: { initialLocale: Locale; children: ReactNode }) {
  const [locale, setLocaleState] = useState(initialLocale);

  function setLocale(next: Locale) {
    document.cookie = `locale=${next}; path=/; max-age=31536000`;
    document.documentElement.lang = next;
    document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
    setLocaleState(next);
  }

  const t = (key: MessageKey) => messages[locale][key];

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}
