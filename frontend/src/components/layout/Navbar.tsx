"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu,
  X,
  ChevronDown,
  Calculator,
  FileText,
  Bot,
  Users,
  BarChart3,
  Shield,
} from "lucide-react";
import Button from "@/components/ui/Button";

interface NavLink {
  label: string;
  href: string;
  children?: { label: string; href: string; icon: React.ReactNode; description: string }[];
}

const navLinks: NavLink[] = [
  { label: "Home", href: "/" },
  { label: "Services", href: "/services" },
  {
    label: "Tools",
    href: "/tools",
    children: [
      {
        label: "Tax Calculator",
        href: "/tools/tax-calculator",
        icon: <Calculator className="h-5 w-5" />,
        description: "Calculate income tax for old and new regime",
      },
      {
        label: "Invoice Generator",
        href: "/tools/invoice",
        icon: <FileText className="h-5 w-5" />,
        description: "Create GST-compliant invoices",
      },
      {
        label: "AI Tax Advisor",
        href: "/chat",
        icon: <Bot className="h-5 w-5" />,
        description: "Get instant answers to tax questions",
      },
      {
        label: "Payroll System",
        href: "/tools/payroll",
        icon: <Users className="h-5 w-5" />,
        description: "Manage employee salaries and payslips",
      },
      {
        label: "GSTR-1 Export",
        href: "/tools/gstr",
        icon: <BarChart3 className="h-5 w-5" />,
        description: "Export GST returns in compliant format",
      },
      {
        label: "Compliance Check",
        href: "/tools/compliance",
        icon: <Shield className="h-5 w-5" />,
        description: "Verify tax compliance status",
      },
    ],
  },
  { label: "Insights", href: "/insights" },
  { label: "Community", href: "/community" },
  { label: "Contact", href: "/contact" },
];

const Navbar: React.FC = () => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileOpen(false);
    setActiveDropdown(null);
  }, [pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMobileOpen]);

  const isActiveLink = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-white/95 backdrop-blur-md shadow-md"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2 flex-shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <span className="text-xl font-bold text-gray-900">
              Aypa <span className="text-primary">TaxAI</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => (
              <div
                key={link.label}
                className="relative"
                onMouseEnter={() =>
                  link.children ? setActiveDropdown(link.label) : null
                }
                onMouseLeave={() => setActiveDropdown(null)}
              >
                <Link
                  href={link.href}
                  className={`flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    isActiveLink(link.href)
                      ? "text-primary bg-primary/5"
                      : "text-gray-700 hover:text-primary hover:bg-gray-50"
                  }`}
                >
                  {link.label}
                  {link.children && (
                    <ChevronDown
                      className={`h-4 w-4 transition-transform duration-200 ${
                        activeDropdown === link.label ? "rotate-180" : ""
                      }`}
                    />
                  )}
                </Link>

                {/* Dropdown Menu */}
                <AnimatePresence>
                  {link.children && activeDropdown === link.label && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 8 }}
                      transition={{ duration: 0.2 }}
                      className="absolute top-full left-1/2 -translate-x-1/2 pt-2"
                    >
                      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-3 min-w-[320px]">
                        {link.children.map((child) => (
                          <Link
                            key={child.label}
                            href={child.href}
                            className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors duration-150 group"
                          >
                            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-colors duration-200">
                              {child.icon}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-gray-900">
                                {child.label}
                              </p>
                              <p className="text-xs text-gray-500 mt-0.5">
                                {child.description}
                              </p>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden lg:flex items-center gap-3">
            <Link href="/auth/login">
              <Button variant="ghost" size="md">
                Login
              </Button>
            </Link>
            <Link href="/auth/register">
              <Button variant="primary" size="md">
                Get Started
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            className="lg:hidden p-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label="Toggle navigation menu"
          >
            {isMobileOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="lg:hidden bg-white border-t border-gray-100 overflow-hidden"
          >
            <div className="max-h-[calc(100vh-4rem)] overflow-y-auto px-4 py-4 space-y-1">
              {navLinks.map((link) => (
                <div key={link.label}>
                  {link.children ? (
                    <>
                      <button
                        onClick={() =>
                          setActiveDropdown(
                            activeDropdown === link.label ? null : link.label
                          )
                        }
                        className="flex items-center justify-between w-full px-4 py-3 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        {link.label}
                        <ChevronDown
                          className={`h-4 w-4 transition-transform duration-200 ${
                            activeDropdown === link.label ? "rotate-180" : ""
                          }`}
                        />
                      </button>
                      <AnimatePresence>
                        {activeDropdown === link.label && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="pl-4 space-y-1 py-1">
                              {link.children.map((child) => (
                                <Link
                                  key={child.label}
                                  href={child.href}
                                  className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-50 hover:text-primary"
                                >
                                  <span className="text-primary">
                                    {child.icon}
                                  </span>
                                  {child.label}
                                </Link>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </>
                  ) : (
                    <Link
                      href={link.href}
                      className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                        isActiveLink(link.href)
                          ? "text-primary bg-primary/5"
                          : "text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      {link.label}
                    </Link>
                  )}
                </div>
              ))}

              <div className="pt-4 border-t border-gray-100 space-y-2">
                <Link href="/auth/login" className="block">
                  <Button variant="outline" size="lg" fullWidth>
                    Login
                  </Button>
                </Link>
                <Link href="/auth/register" className="block">
                  <Button variant="primary" size="lg" fullWidth>
                    Get Started
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
