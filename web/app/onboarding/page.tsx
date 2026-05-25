"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

const inputClass =
  "mt-1 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-white/30 focus:outline-none";
const labelClass =
  "block text-xs font-medium uppercase tracking-wider text-white/60";
const primaryButtonClass =
  "inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-40";

export default function OnboardingPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [practiceName, setPracticeName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim()) return;
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      router.push("/sign-in");
      return;
    }

    const { error: updateError } = await supabase
      .from("coaches")
      .update({
        display_name: displayName.trim(),
        practice_name: practiceName.trim() || null,
        specialty: specialty.trim() || null,
        onboarded_at: new Date().toISOString(),
      })
      .eq("id", user.id);

    setLoading(false);
    if (updateError) {
      setError(updateError.message);
    } else {
      router.push("/dashboard");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <header className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
            Welcome
          </p>
          <h1 className="mt-3 text-2xl font-light tracking-tight text-white">
            Set up your profile
          </h1>
          <p className="mt-2 text-sm text-white/50">
            This takes 30 seconds. You can update it later in account settings.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm"
        >
          <div>
            <label className={labelClass}>Your name *</label>
            <input
              type="text"
              required
              autoFocus
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Jane Smith"
              className={inputClass}
            />
          </div>

          <div>
            <label className={labelClass}>Practice / business name</label>
            <input
              type="text"
              value={practiceName}
              onChange={(e) => setPracticeName(e.target.value)}
              placeholder="Apex Performance Coaching"
              className={inputClass}
            />
          </div>

          <div>
            <label className={labelClass}>Specialty (optional)</label>
            <input
              type="text"
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              placeholder="e.g. Strength & body composition"
              className={inputClass}
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading || !displayName.trim()}
            className={primaryButtonClass}
          >
            {loading ? "Saving…" : "Go to dashboard"}
          </button>
        </form>
      </div>
    </main>
  );
}
