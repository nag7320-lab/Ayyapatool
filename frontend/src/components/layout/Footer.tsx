"use client";

import React from "react";
import Link from "next/link";
import {
  Mail,
  Phone,
  MapPin,
  Twitter,
  Linkedin,
  Github,
  Youtube,
} from "lucide-react";

const quickLinks = [
  { label: "Home", href: "/" },
  { label: "Services", href: "/services" },
  { label: "Tax Calculator", href: "/tools/tax-calculator" },
  { label: "Invoice Generator", href: "/tools/invoice" },
  { label: "AI Tax Advisor", href: "/chat" },
  { label: "Payroll System", href: "/tools/payroll" },
];

const legalLinks = [
  { label: "Privacy Policy", href: "/legal/privacy" },
  { label: "Terms of Service", href: "/legal/terms" },
  { label: "Cookie Policy", href: "/legal/cookies" },
  { label: "Refund Policy", href: "/legal/refund" },
  { label: "Disclaimer", href: "/legal/disclaimer" },
];

const resourceLinks = [
  { label: "Blog", href: "/insights" },
  { label: "Community", href: "/community" },
  { label: "Help Center", href: "/help" },
  { label: "API Docs", href: "/docs" },
  { label: "Changelog", href: "/changelog" },
];

const socialLinks = [
  { label: "Twitter", href: "https://twitter.com/aypataxai", icon: Twitter },
  {
    label: "LinkedIn",
    href: "https://linkedin.com/company/aypataxai",
    icon: Linkedin,
  },
  { label: "GitHub", href: "https://github.com/aypataxai", icon: Github },
  { label: "YouTube", href: "https://youtube.com/@aypataxai", icon: Youtube },
];

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-950 text-gray-300">
      {/* Main Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 lg:gap-8">
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-white">
                Aypa <span className="text-secondary">TaxAI</span>
              </span>
            </Link>
            <p className="text-gray-400 text-sm leading-relaxed max-w-sm mb-6">
              Empowering businesses with AI-driven tax solutions. From GST
              compliance and invoice generation to intelligent tax advisory,
              Aypa TaxAI simplifies every aspect of your financial operations.
            </p>
            <div className="space-y-3">
              <a
                href="mailto:support@aypataxai.com"
                className="flex items-center gap-2.5 text-sm text-gray-400 hover:text-secondary transition-colors"
              >
                <Mail className="h-4 w-4 flex-shrink-0" />
                support@aypataxai.com
              </a>
              <a
                href="tel:+919876543210"
                className="flex items-center gap-2.5 text-sm text-gray-400 hover:text-secondary transition-colors"
              >
                <Phone className="h-4 w-4 flex-shrink-0" />
                +91 98765 43210
              </a>
              <div className="flex items-start gap-2.5 text-sm text-gray-400">
                <MapPin className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>Bengaluru, Karnataka, India</span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Quick Links
            </h4>
            <ul className="space-y-2.5">
              {quickLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Resources
            </h4>
            <ul className="space-y-2.5">
              {resourceLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Legal
            </h4>
            <ul className="space-y-2.5">
              {legalLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            &copy; {currentYear} Aypa TaxAI. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            {socialLinks.map((social) => {
              const Icon = social.icon;
              return (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-all duration-200"
                  aria-label={social.label}
                >
                  <Icon className="h-4 w-4" />
                </a>
              );
            })}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
