"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2, Mail, User } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { AuthBrandPanel } from "@/components/brand/auth-brand-panel";
import { Field, PasswordField } from "@/components/brand/auth-fields";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.register(email, fullName, password);
      await api.login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not reach the server. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-view">
      <AuthBrandPanel />

      <div className="auth-panel">
        <div className="auth-card">
          <Link href="/" className="mini-logo">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.jpg" alt="No Gree AI" />
            <b>No Gree AI</b>
          </Link>

          <h2>Create your account</h2>
          <p className="sub">Start protecting yourself from fraud in seconds. Free for individuals.</p>

          <form onSubmit={onSubmit}>
            <Field
              id="name"
              label="Full name"
              icon={<User />}
              autoComplete="name"
              required
              value={fullName}
              onChange={setFullName}
              placeholder="Ada Okeke"
            />
            <Field
              id="email"
              label="Email"
              icon={<Mail />}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
            />
            <PasswordField
              value={password}
              onChange={setPassword}
              autoComplete="new-password"
              minLength={8}
              placeholder="At least 8 characters"
            />

            {error && (
              <p
                style={{
                  marginTop: 14,
                  borderRadius: 10,
                  background: "var(--crit-t)",
                  color: "var(--crit)",
                  padding: "9px 12px",
                  fontSize: 12.5,
                  fontWeight: 500,
                }}
              >
                {error}
              </p>
            )}

            <button type="submit" className="btn primary block" disabled={loading}>
              {loading && <Loader2 className="animate-spin" style={{ width: 17, height: 17 }} />}
              Create account
            </button>
          </form>

          <p style={{ marginTop: 22, textAlign: "center", fontSize: 13, color: "var(--muted-hex)" }}>
            Already have an account?{" "}
            <Link href="/login" className="link-green">
              Sign in
            </Link>
          </p>

          <p style={{ marginTop: 18, textAlign: "center", fontSize: 11, lineHeight: 1.6, color: "var(--muted-hex)" }}>
            By creating an account you agree to our fair-use policy. We never ask for your BVN, OTP or PIN.
          </p>
        </div>
      </div>
    </main>
  );
}
