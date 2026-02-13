"use client";

import React, { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Eye, EyeOff, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import Button from "@/components/ui/Button";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import type { AuthResponse } from "@/types";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await api.post<AuthResponse>("/auth/login", {
        email,
        password,
      });

      login(response.data.user, response.data.tokens);
      router.push("/dashboard");
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(
        axiosError.response?.data?.message ||
          "Invalid credentials. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    window.location.href = `${apiUrl}/auth/google`;
  };

  return (
    <div className="min-h-screen flex">
      {/* Left: Decorative Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary via-primary-800 to-primary-950 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-72 h-72 bg-secondary/10 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-20 w-56 h-56 bg-accent/10 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-16">
          <Link href="/" className="flex items-center gap-2 mb-12">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <span className="text-2xl font-bold text-white">Aypa TaxAI</span>
          </Link>

          <h2 className="text-3xl font-bold text-white mb-4">
            Welcome back to smarter tax management
          </h2>
          <p className="text-blue-200 text-lg leading-relaxed max-w-md">
            Access your AI-powered tax tools, invoices, and compliance dashboard
            in one place.
          </p>

          <div className="mt-12 space-y-4">
            {[
              "Real-time GST compliance monitoring",
              "AI-powered tax saving recommendations",
              "Secure and encrypted data handling",
            ].map((text) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-secondary/20 flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-secondary" />
                </div>
                <span className="text-blue-100 text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Login Form */}
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
            Sign in to your account
          </h1>
          <p className="text-gray-500 mb-8">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/register"
              className="text-primary font-medium hover:underline"
            >
              Create one free
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

          {/* Google OAuth Button */}
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border-2 border-gray-200 bg-white text-gray-700 font-medium text-sm hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 mb-6"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </button>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-white text-gray-400">
                or sign in with email
              </span>
            </div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
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
                  className="input-field pl-10"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="label-text mb-0">
                  Password
                </label>
                <Link
                  href="/auth/forgot-password"
                  className="text-xs text-primary font-medium hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-10 pr-10"
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
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isLoading}
              rightIcon={!isLoading ? <ArrowRight className="h-4 w-4" /> : undefined}
            >
              Sign In
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-gray-400">
            By signing in, you agree to our{" "}
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
