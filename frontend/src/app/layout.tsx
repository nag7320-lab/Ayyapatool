import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "Aypa TaxAI - Smart Tax Solutions for Modern Businesses",
    template: "%s | Aypa TaxAI",
  },
  description:
    "Empowering businesses with AI-driven tax solutions. GST compliance, invoice generation, tax calculation, payroll management, and intelligent tax advisory powered by artificial intelligence.",
  keywords: [
    "tax software",
    "GST compliance",
    "invoice generator",
    "tax calculator",
    "payroll management",
    "AI tax advisor",
    "GSTR-1",
    "Indian tax",
    "business accounting",
    "Aypa TaxAI",
  ],
  authors: [{ name: "Aypa TaxAI Team" }],
  creator: "Aypa TaxAI",
  publisher: "Aypa TaxAI",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://aypataxai.com",
    siteName: "Aypa TaxAI",
    title: "Aypa TaxAI - Smart Tax Solutions for Modern Businesses",
    description:
      "AI-driven tax solutions for GST compliance, invoicing, tax calculation, payroll, and expert advisory.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Aypa TaxAI",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Aypa TaxAI - Smart Tax Solutions for Modern Businesses",
    description:
      "AI-driven tax solutions for GST compliance, invoicing, tax calculation, payroll, and expert advisory.",
    images: ["/og-image.png"],
  },
};

export const viewport: Viewport = {
  themeColor: "#1E3A8A",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} antialiased`}>
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
