"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Bot,
  FileText,
  Calculator,
  Users,
  BarChart3,
  MessageSquare,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  TrendingUp,
  Clock,
  Shield,
} from "lucide-react";
import Button from "@/components/ui/Button";

// ---------------------------------------------------------------------------
// Animation Variants
// ---------------------------------------------------------------------------
const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1],
    },
  }),
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: (i: number = 0) => ({
    opacity: 1,
    scale: 1,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: "easeOut",
    },
  }),
};

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------
const features = [
  {
    icon: Bot,
    title: "AI Tax Advisor",
    description:
      "Get instant, accurate answers to your tax questions powered by advanced AI trained on Indian tax law.",
    color: "from-blue-500 to-primary",
    href: "/chat",
  },
  {
    icon: FileText,
    title: "Invoice Generator",
    description:
      "Create professional, GST-compliant invoices in seconds with automatic tax calculations.",
    color: "from-emerald-500 to-secondary",
    href: "/tools/invoice",
  },
  {
    icon: Calculator,
    title: "Tax Calculator",
    description:
      "Compare old and new tax regimes side by side. Optimise your tax liability with smart suggestions.",
    color: "from-amber-500 to-accent",
    href: "/tools/tax-calculator",
  },
  {
    icon: Users,
    title: "Payroll System",
    description:
      "Automate salary processing, PF, ESI deductions and generate payslips with one click.",
    color: "from-purple-500 to-violet-600",
    href: "/tools/payroll",
  },
  {
    icon: BarChart3,
    title: "GSTR-1 Export",
    description:
      "Export your sales data in government-compliant GSTR-1 format ready for filing.",
    color: "from-rose-500 to-pink-600",
    href: "/tools/gstr",
  },
  {
    icon: MessageSquare,
    title: "Expert Advisory",
    description:
      "Connect with certified tax professionals for complex queries and personalised guidance.",
    color: "from-cyan-500 to-teal-600",
    href: "/services",
  },
];

const stats = [
  { value: "10K+", label: "Users", icon: Users },
  { value: "50K+", label: "Invoices", icon: FileText },
  { value: "99.9%", label: "Uptime", icon: Clock },
  { value: "100K+", label: "Queries", icon: MessageSquare },
];

const benefits = [
  "GST-compliant invoicing in seconds",
  "AI-powered tax advisory 24/7",
  "Compare old vs new tax regime instantly",
  "Automated payroll with statutory compliance",
  "GSTR-1 ready export for seamless filing",
  "Bank-grade encryption for your data",
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------
export default function HomePage() {
  return (
    <div className="overflow-hidden">
      {/* ================================================================= */}
      {/* HERO SECTION */}
      {/* ================================================================= */}
      <section className="relative min-h-screen flex items-center pt-20">
        {/* Background decoration */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-secondary/5 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-accent/3 blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left: Copy */}
            <motion.div
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
            >
              <motion.div
                variants={fadeInUp}
                custom={0}
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6"
              >
                <Sparkles className="h-4 w-4" />
                AI-Powered Tax Platform
              </motion.div>

              <motion.h1
                variants={fadeInUp}
                custom={1}
                className="heading-primary text-gray-900 mb-6"
              >
                Smart Tax Solutions for{" "}
                <span className="text-gradient">Modern Businesses</span>
              </motion.h1>

              <motion.p
                variants={fadeInUp}
                custom={2}
                className="text-lg md:text-xl text-gray-600 leading-relaxed mb-8 max-w-xl"
              >
                From GST compliance and invoicing to AI-powered tax advisory,
                Aypa TaxAI streamlines every aspect of your business tax
                operations with intelligence and precision.
              </motion.p>

              <motion.div
                variants={fadeInUp}
                custom={3}
                className="flex flex-col sm:flex-row gap-4 mb-10"
              >
                <Link href="/auth/register">
                  <Button
                    variant="primary"
                    size="xl"
                    rightIcon={<ArrowRight className="h-5 w-5" />}
                  >
                    Start Free Trial
                  </Button>
                </Link>
                <Link href="/chat">
                  <Button
                    variant="outline"
                    size="xl"
                    leftIcon={<Bot className="h-5 w-5" />}
                  >
                    Try AI Advisor
                  </Button>
                </Link>
              </motion.div>

              <motion.div
                variants={fadeInUp}
                custom={4}
                className="flex flex-wrap gap-x-6 gap-y-2"
              >
                {["No credit card required", "14-day free trial", "Cancel anytime"].map(
                  (text) => (
                    <span
                      key={text}
                      className="flex items-center gap-1.5 text-sm text-gray-500"
                    >
                      <CheckCircle2 className="h-4 w-4 text-secondary" />
                      {text}
                    </span>
                  )
                )}
              </motion.div>
            </motion.div>

            {/* Right: Decorative Card Illustration */}
            <motion.div
              initial={{ opacity: 0, x: 60 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="relative hidden lg:block"
            >
              <div className="relative">
                {/* Main Card */}
                <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">
                        AI Tax Advisor
                      </p>
                      <p className="text-xs text-gray-500">Online now</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-2xl rounded-tl-sm p-4 max-w-[85%]">
                      <p className="text-sm text-gray-700">
                        What is the GST rate for software services under SAC
                        998314?
                      </p>
                    </div>
                    <div className="bg-primary/5 rounded-2xl rounded-tr-sm p-4 ml-auto max-w-[85%]">
                      <p className="text-sm text-gray-700">
                        Software services under SAC 998314 attract{" "}
                        <span className="font-semibold text-primary">
                          18% GST
                        </span>{" "}
                        (9% CGST + 9% SGST for intra-state, or 18% IGST for
                        inter-state transactions).
                      </p>
                    </div>
                  </div>

                  <div className="mt-6 flex items-center gap-2 p-3 rounded-xl border border-gray-200 bg-gray-50">
                    <span className="text-sm text-gray-400 flex-1">
                      Ask a tax question...
                    </span>
                    <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                      <ArrowRight className="h-4 w-4 text-white" />
                    </div>
                  </div>
                </div>

                {/* Floating Badge: Tax Saved */}
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute -top-4 -right-4 bg-white rounded-2xl shadow-lg border border-gray-100 p-4"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center">
                      <TrendingUp className="h-4 w-4 text-secondary" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Tax Saved</p>
                      <p className="text-sm font-bold text-gray-900">
                        Rs. 2.4L
                      </p>
                    </div>
                  </div>
                </motion.div>

                {/* Floating Badge: Compliance */}
                <motion.div
                  animate={{ y: [0, 8, 0] }}
                  transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute -bottom-4 -left-4 bg-white rounded-2xl shadow-lg border border-gray-100 p-4"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                      <Shield className="h-4 w-4 text-accent" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">GST Compliance</p>
                      <p className="text-sm font-bold text-green-600">
                        100% Verified
                      </p>
                    </div>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* FEATURES GRID */}
      {/* ================================================================= */}
      <section className="section-padding bg-gray-50/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center mb-16"
          >
            <motion.span
              variants={fadeInUp}
              custom={0}
              className="inline-block px-4 py-1.5 rounded-full bg-secondary/10 text-secondary text-sm font-medium mb-4"
            >
              Our Features
            </motion.span>
            <motion.h2
              variants={fadeInUp}
              custom={1}
              className="heading-secondary text-gray-900 mb-4"
            >
              Everything You Need to Manage Taxes
            </motion.h2>
            <motion.p
              variants={fadeInUp}
              custom={2}
              className="text-gray-600 text-lg max-w-2xl mx-auto"
            >
              Powerful tools designed to simplify tax compliance, automate
              invoicing, and provide expert-level guidance at your fingertips.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
            variants={staggerContainer}
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div key={feature.title} variants={scaleIn} custom={index}>
                  <Link href={feature.href} className="block group">
                    <div className="card h-full hover:-translate-y-1">
                      <div
                        className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}
                      >
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {feature.description}
                      </p>
                      <div className="mt-4 flex items-center gap-1.5 text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        Learn more
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* STATS SECTION */}
      {/* ================================================================= */}
      <section className="section-padding">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="relative rounded-3xl bg-gradient-to-br from-primary via-primary-800 to-primary-950 p-10 md:p-16 overflow-hidden"
          >
            {/* Background orbs */}
            <div className="absolute top-0 right-0 w-72 h-72 bg-secondary/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-56 h-56 bg-accent/10 rounded-full blur-3xl" />

            <motion.div
              variants={fadeInUp}
              custom={0}
              className="text-center mb-12 relative z-10"
            >
              <h2 className="heading-secondary text-white mb-4">
                Trusted by Businesses Across India
              </h2>
              <p className="text-blue-200 text-lg max-w-xl mx-auto">
                Join thousands of businesses that rely on Aypa TaxAI for their
                tax compliance and financial operations.
              </p>
            </motion.div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 relative z-10">
              {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <motion.div
                    key={stat.label}
                    variants={scaleIn}
                    custom={index}
                    className="text-center"
                  >
                    <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-3">
                      <Icon className="h-6 w-6 text-secondary" />
                    </div>
                    <p className="text-3xl md:text-4xl font-bold text-white mb-1">
                      {stat.value}
                    </p>
                    <p className="text-sm text-blue-200">{stat.label}</p>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* BENEFITS / WHY US */}
      {/* ================================================================= */}
      <section className="section-padding bg-gray-50/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left: Benefits list */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              variants={staggerContainer}
            >
              <motion.span
                variants={fadeInUp}
                custom={0}
                className="inline-block px-4 py-1.5 rounded-full bg-accent/10 text-accent-700 text-sm font-medium mb-4"
              >
                Why Aypa TaxAI
              </motion.span>
              <motion.h2
                variants={fadeInUp}
                custom={1}
                className="heading-secondary text-gray-900 mb-6"
              >
                Built for the Way You Work
              </motion.h2>
              <motion.p
                variants={fadeInUp}
                custom={2}
                className="text-gray-600 text-lg mb-8"
              >
                We combine cutting-edge AI with deep tax domain expertise to
                deliver a platform that truly understands your business needs.
              </motion.p>

              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <motion.div
                    key={benefit}
                    variants={fadeInUp}
                    custom={index + 3}
                    className="flex items-center gap-3"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-secondary/10 flex items-center justify-center">
                      <CheckCircle2 className="h-4 w-4 text-secondary" />
                    </div>
                    <span className="text-gray-700">{benefit}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Right: Decorative metrics */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              className="grid grid-cols-2 gap-4"
            >
              <div className="card bg-gradient-to-br from-primary/5 to-primary/10 border-primary/10">
                <Calculator className="h-8 w-8 text-primary mb-3" />
                <p className="text-2xl font-bold text-gray-900">Rs. 12Cr+</p>
                <p className="text-sm text-gray-500 mt-1">Tax Savings Identified</p>
              </div>
              <div className="card bg-gradient-to-br from-secondary/5 to-secondary/10 border-secondary/10 mt-8">
                <FileText className="h-8 w-8 text-secondary mb-3" />
                <p className="text-2xl font-bold text-gray-900">50K+</p>
                <p className="text-sm text-gray-500 mt-1">Invoices Generated</p>
              </div>
              <div className="card bg-gradient-to-br from-accent/5 to-accent/10 border-accent/10">
                <Shield className="h-8 w-8 text-accent mb-3" />
                <p className="text-2xl font-bold text-gray-900">100%</p>
                <p className="text-sm text-gray-500 mt-1">GST Compliant</p>
              </div>
              <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-100 mt-8">
                <Bot className="h-8 w-8 text-purple-600 mb-3" />
                <p className="text-2xl font-bold text-gray-900">24/7</p>
                <p className="text-sm text-gray-500 mt-1">AI Advisor Available</p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* CTA SECTION */}
      {/* ================================================================= */}
      <section className="section-padding">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="text-center max-w-3xl mx-auto"
          >
            <motion.h2
              variants={fadeInUp}
              custom={0}
              className="heading-secondary text-gray-900 mb-6"
            >
              Ready to Simplify Your Tax Operations?
            </motion.h2>
            <motion.p
              variants={fadeInUp}
              custom={1}
              className="text-gray-600 text-lg mb-10"
            >
              Join thousands of businesses using Aypa TaxAI to save time, reduce
              errors, and stay compliant. Get started in under 2 minutes.
            </motion.p>
            <motion.div
              variants={fadeInUp}
              custom={2}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Link href="/auth/register">
                <Button
                  variant="primary"
                  size="xl"
                  rightIcon={<ArrowRight className="h-5 w-5" />}
                >
                  Start Your Free Trial
                </Button>
              </Link>
              <Link href="/contact">
                <Button variant="outline" size="xl">
                  Talk to Sales
                </Button>
              </Link>
            </motion.div>
            <motion.p
              variants={fadeInUp}
              custom={3}
              className="mt-6 text-sm text-gray-500"
            >
              Free 14-day trial. No credit card required. Cancel anytime.
            </motion.p>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
