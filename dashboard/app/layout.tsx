import type { Metadata } from "next";
import { Archivo_Black, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const archivo = Archivo_Black({ subsets: ["latin"], weight: "400", variable: "--font-archivo" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-plex" });

export const metadata: Metadata = {
  title: "Signal Ledger | Financial Analysis",
  description: "Structured multi-agent financial analysis workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${archivo.variable} ${plexMono.variable}`}>{children}</body>
    </html>
  );
}
