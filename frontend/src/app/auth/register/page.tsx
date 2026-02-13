"use client";

import React, { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import Button from "@/components/ui/Button";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import type { AuthResponse } from "@/types";

const passwordRequirements = [
  { label: "At least 8 characters", test: (p: string) => p.length >= 8 },
  { label: "One uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { label: "One lowercase letter", test: (p: string) => /[a-z]/.test(p) },
  { label: "One number", test: (p: string) => /\d/.test(p) },
];

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuthStore();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  const isPasswordValid = passwordRequirements.every((req) =>
    req.test(password)
  );

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});

    if (!isPasswordValid) {
      setError("Please meet all password requirements.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post<AuthResponse>("/auth/register", {
        name,
        email,
        password,
      });

      login(response.data.user, response.data.tokens);
      router.push("/dashboard");
    } catch (err: unknown) {
      const axiosError = err as {
        response?: { data?: { message?: string; errors?: Record<string, string[]> } };
      };
      if (axiosError.response?.data?.errors) {
        setFieldErrors(axiosError.response.data.errors);
      }
      setError(
        axiosError.response?.data?.message ||
          "Registration failed. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left: Decorative Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-secondary-700 via-secondary to-emerald-500 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-20 right-20 w-72 h-72 bg-white/5 rounded-full blur-3xl" />
          <div className="absolute bottom-20 left-20 w-56 h-56 bg-primary/10 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-16">
          <Link href="/" className="flex items-center gap-2 mb-12">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <span className="text-2xl font-bold text-white">Aypa TaxAI</span>
          </Link>

          <h2 className="text-3xl font-bold text-white mb-4">
            Start your journey to effortless tax management
          </h2>
          <p className="text-emerald-100 text-lg leading-relaxed max-w-md">
            Create your free account and unlock access to AI-powered tax tools
            built for Indian businesses.
          </p>

          <div className="mt-12 space-y-5">
            {[
              {
                title: "Free 14-day trial",
                desc: "Full access to all features, no credit card needed",
              },
              {
                title: "Setup in 2 minutes",
                desc: "Quick onboarding with guided walkthrough",
              },
              {
                title: "Enterprise-grade security",
                desc: "Bank-level encryption protects your data",
              },
            ].map((item) => (
              <div key={item.title} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mt-0.5">
                  <CheckCircle2 className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-white font-medium text-sm">
                    {item.title}
                  </p>
                  <p className="text-emerald-100 text-xs mt-0.5">
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Register Form */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Mobile brand */}
          <div className="lg:hidden mb-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-gray-900">
                Aypa <span className="text-primary">TaxAI</span>
              </span>
            </Link>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Create your account
          </h1>
          <p className="text-gray-500 mb-8">
            Already have an account?{" "}
            <Link
              href="/auth/login"
              className="text-primary font-medium hover:underline"
            >
              Sign in
            </Link>
          </p>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700"
            >
              {error}
            </motion.div>
          )}

          {/* Register Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="name" className="label-text">
                Full name
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="name"
                  type="text"
                  required
                  autoComplete="name"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={`input-field pl-10 ${
                    fieldErrors.name ? "border-red-400 focus:ring-red-300" : ""
                  }`}
                />
              </div>
              {fieldErrors.name && (
                <p className="mt-1 text-xs text-red-600">
                  {fieldErrors.name[0]}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="label-text">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`input-field pl-10 ${
                    fieldErrors.email ? "border-red-400 focus:ring-red-300" : ""
                  }`}
                />
              </div>
              {fieldErrors.email && (
                <p className="mt-1 text-xs text-red-600">
                  {fieldErrors.email[0]}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="label-text">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="new-password"
                  placeholder="Create a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`input-field pl-10 pr-10 ${
                    fieldErrors.password
                      ? "border-red-400 focus:ring-red-300"
                      : ""
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="mt-1 text-xs text-red-600">
                  {fieldErrors.password[0]}
                </p>
              )}

              {/* Password strength indicators */}
              {password.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mt-3 space-y-1.5"
                >
                  {passwordRequirements.map((req) => {
                    const met = req.test(password);
                    return (
                      <div
                        key={req.label}
                        className="flex items-center gap-2 text-xs"
                      >
                        <div
                          className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${
                            met ? "bg-secondary" : "bg-gray-200"
                          }`}
                        >
                          {met && (
                            <CheckCircle2 className="h-2.5 w-2.5 text-white" />
                          )}
                        </div>
                        <span
                          className={met ? "text-secondary-700" : "text-gray-400"}
                        >
                          {req.label}
                        </span>
                      </div>
                    );
                  })}
                </motion.div>
              )}
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isLoading}
              rightIcon={
                !isLoading ? <ArrowRight className="h-4 w-4" /> : undefined
              }
            >
              Create Account
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-gray-400">
            By creating an account, you agree to our{" "}
            <Link href="/legal/terms" className="underline hover:text-gray-600">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link
              href="/legal/privacy"
              className="underline hover:text-gray-600"
            >
              Privacy Policy
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
