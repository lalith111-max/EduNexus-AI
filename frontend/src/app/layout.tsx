import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EduNexus AI - Personalized Tutoring & Adaptive Learning",
  description: "Multimodal source-grounded learning workspace with verifiable citations, Bayesian Knowledge Tracing mastery, adaptive assessments, and RAG benchmarking.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className="min-h-full bg-[#090d16] text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}
