function parseUtc(iso: string): Date {
  // The backend sends UTC times without a zone marker.
  const hasZone = iso.endsWith("Z") || /[+-]\d\d:\d\d$/.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`);
}

export function relativeTime(iso: string, locale: string): string {
  const date = parseUtc(iso);
  const minutes = Math.round((Date.now() - date.getTime()) / 60000);
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });

  if (minutes < 60) return rtf.format(-Math.max(minutes, 0), "minute");
  if (minutes < 60 * 24) return rtf.format(-Math.round(minutes / 60), "hour");
  if (minutes < 60 * 24 * 7) return rtf.format(-Math.round(minutes / (60 * 24)), "day");
  return date.toLocaleDateString(locale, { day: "numeric", month: "short" });
}

export function formatDateTime(iso: string, locale: string): string {
  return parseUtc(iso).toLocaleString(locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
