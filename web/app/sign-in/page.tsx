"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

const inputClass =
  "w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm text-white placeholder-white/30 focus:border-white/30 focus:outline-none";
const primaryButtonClass =
  "w-full inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-40";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const appUrl =
      process.env.NEXT_PUBLIC_APP_URL ?? window.location.origin;

    const { error: authError } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${appUrl}/auth/callback`,
        shouldCreateUser: true,
      },
    });

    setLoading(false);
    if (authError) {
      setError(authError.message);
    } else {
      setSent(true);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <header className="mb-8 text-center">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
            HCC Compiler
          </p>
          <h1 className="mt-3 text-2xl font-light tracking-tight text-white">
            Sign in
          </h1>
          <p className="mt-2 text-sm text-white/50">
            Enter your email — we&apos;ll send a magic link.
          </p>
        </header>

        {sent ? (
          <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-6 text-center">
            <p className="text-sm font-medium text-emerald-100">
              Check your inbox
            </p>
            <p className="mt-1 text-xs text-white/50">
              A sign-in link was sent to{" "}
              <span className="font-mono text-white/70">{email}</span>.
            </p>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm"
          >
            <label className="block text-xs font-medium uppercase tracking-wider text-white/60">
              Email address
            </label>
            <input
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className={`mt-2 ${inputClass}`}
            />

            {error && (
              <p className="mt-3 text-xs text-red-400">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading || !email}
              className={`mt-4 ${primaryButtonClass}`}
            >
              {loading ? "Sending…" : "Send magic link"}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
