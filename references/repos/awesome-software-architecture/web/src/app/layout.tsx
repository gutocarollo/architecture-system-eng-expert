import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Awesome Architecture | Software Architecture Resources",
  description:
    "A curated atlas of software architecture patterns, systems, AI engineering, and practical resources.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
