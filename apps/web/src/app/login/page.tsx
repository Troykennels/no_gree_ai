"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { BrainCircuit, Loader2, Mail, ShieldCheck } from "lucide-react";
import { api, ApiError, tokenStore } from "@/lib/api";
import { AuthBrandPanel } from "@/components/brand/auth-brand-panel";
import { Field, PasswordField } from "@/components/brand/auth-fields";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Already signed in? Skip the login screen and go straight to the dashboard.
  useEffect(() => {
    if (tokenStore.get()) router.replace("/dashboard");
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
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

          <h2>Welcome back</h2>
          <p className="sub">Sign in to your No Gree AI dashboard.</p>

          <form onSubmit={onSubmit}>
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
              autoComplete="current-password"
            />

            <div className="row-between">
              <label className="remember">
                <input type="checkbox" /> Remember me
              </label>
              <Link href="/help" className="link-green">
                Forgot password?
              </Link>
            </div>

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
              Sign in
            </button>
          </form>

          <div className="divider">New to No Gree AI?</div>

          <div className="tryfree-note" style={{ borderTop: 0, paddingTop: 0, marginTop: 0 }}>
            Create a free account and start scanning in seconds.
            <Link href="/register" className="btn tryfree">
              Create a free account
            </Link>
          </div>

          <div
            style={{
              marginTop: 24,
              display: "flex",
              justifyContent: "center",
              gap: 16,
              fontSize: 11,
              color: "var(--muted-hex)",
            }}
          >
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <ShieldCheck style={{ width: 14, height: 14 }} /> Bank-grade security
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <BrainCircuit style={{ width: 14, height: 14 }} /> AI-powered
            </span>
          </div>
        </div>
      </div>
    </main>
  );
}
