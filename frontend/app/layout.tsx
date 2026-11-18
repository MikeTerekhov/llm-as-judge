import type { ReactNode } from "react";
import "./globals.css";
export const metadata = { title: "AI Regimen | Synthetic Research", description: "Research-only HIV evidence review prototype" };
export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
