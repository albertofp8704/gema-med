import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "GEMA-MED — USMLE Tutor",
  description:
    "Tutor IA para USMLE Step 1/2/3, ECFMG y reválida de título médico. Banco MedQA + Claude.",
  icons: { icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'><text y='32' font-size='32'>🩺</text></svg>" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="es">
        <body className="antialiased">{children}</body>
      </html>
    </ClerkProvider>
  );
}
