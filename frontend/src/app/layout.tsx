import type { Metadata } from "next";
import { cookies } from "next/headers";
import { I18nProvider, type Locale } from "@/shared/lib/i18n";
import "./globals.css";

export const metadata: Metadata = { title: "Onboarding" };

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies();
  const locale: Locale = cookieStore.get("locale")?.value === "ar" ? "ar" : "en";

  return (
    <html lang={locale} dir={locale === "ar" ? "rtl" : "ltr"}>
      <body>
        <I18nProvider initialLocale={locale}>{children}</I18nProvider>
      </body>
    </html>
  );
}
