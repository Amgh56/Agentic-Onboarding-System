"use client";

import { useState } from "react";
import { useI18n, type MessageKey } from "@/shared/lib/i18n";

type Props = {
  label: MessageKey;
  value: string; // YYYY-MM-DD, or "" until day, month and year are all chosen
  error?: MessageKey;
  onChange: (value: string) => void;
};

const thisYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => thisYear - 14 - i);

function parts(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return value ? { day, month, year } : { day: 0, month: 0, year: 0 };
}

/** Day, month and year dropdowns: quicker than a calendar for a date of birth. */
export function DateSelect({ label, value, error, onChange }: Props) {
  const { t, locale } = useI18n();
  const [date, setDate] = useState(parts(value));
  const monthName = (month: number) => new Date(2000, month - 1, 1).toLocaleDateString(locale, { month: "long" });
  const daysInMonth = date.month && date.year ? new Date(date.year, date.month, 0).getDate() : 31;

  function pick(field: "day" | "month" | "year", number: number) {
    const next = { ...date, [field]: number };
    if (next.month && next.year) next.day = Math.min(next.day, new Date(next.year, next.month, 0).getDate());
    setDate(next);
    const pad = (n: number) => String(n).padStart(2, "0");
    onChange(next.day && next.month && next.year ? `${next.year}-${pad(next.month)}-${pad(next.day)}` : "");
  }

  return (
    <div className="field">
      <span className="field-label">{t(label)}</span>
      <div className="date-select">
        <select value={date.day} onChange={(e) => pick("day", Number(e.target.value))} aria-label={t("date.day")}>
          <option value={0}>{t("date.day")}</option>
          {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => (
            <option key={day} value={day}>{day}</option>
          ))}
        </select>
        <select value={date.month} onChange={(e) => pick("month", Number(e.target.value))} aria-label={t("date.month")}>
          <option value={0}>{t("date.month")}</option>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
            <option key={month} value={month}>{monthName(month)}</option>
          ))}
        </select>
        <select value={date.year} onChange={(e) => pick("year", Number(e.target.value))} aria-label={t("date.year")}>
          <option value={0}>{t("date.year")}</option>
          {years.map((year) => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
      </div>
      {error && <span className="field-error">{t(error)}</span>}
    </div>
  );
}
