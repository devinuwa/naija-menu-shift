import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Naija MenuShift · Kitchen Intelligence Studio",
  description:
    "Research prototype: find a plant-based research formulation for a familiar Nigerian dish within your budget, protein target, time, equipment and stock. Demo data is synthetic.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
