import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AmbientBg } from "@/components/ambient-bg";
import { TopNav } from "@/components/top-nav";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Aura Clinic · HCC Compiler",
  description: "Per-client evidence-graded plan navigator.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full bg-[var(--bg)] text-[var(--text-primary)]">
        <AmbientBg />
        <div className="relative z-10 flex min-h-screen flex-col">
          <TopNav />
          {children}
        </div>
      </body>
    </html>
  );
}
