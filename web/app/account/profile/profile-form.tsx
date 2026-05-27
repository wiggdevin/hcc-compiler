"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface Initial {
  display_name: string | null;
  practice_name: string | null;
  specialty: string | null;
  headshot_url: string | null;
  contact_label: string | null;
  contact_url: string | null;
}

const inputClass =
  "mt-1 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-white/30 focus:outline-none";
const labelClass =
  "block text-xs font-medium uppercase tracking-wider text-white/60";
const helperClass = "mt-1 text-xs text-white/40";
const primaryButtonClass =
  "inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-40";

export function ProfileForm({ initial }: { initial: Initial }) {
  const [displayName, setDisplayName] = useState(initial.display_name ?? "");
  const [practiceName, setPracticeName] = useState(initial.practice_name ?? "");
  const [specialty, setSpecialty] = useState(initial.specialty ?? "");
  const [headshotUrl, setHeadshotUrl] = useState(initial.headshot_url ?? "");
  const [contactLabel, setContactLabel] = useState(initial.contact_label ?? "");
  const [contactUrl, setContactUrl] = useState(initial.contact_url ?? "");
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim()) return;
    setStatus("saving");
    setError(null);

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      setStatus("error");
      setError("Session expired. Refresh and sign in again.");
      return;
    }

    const { error: updateError } = await supabase
      .from("coaches")
      .update({
        display_name: displayName.trim(),
        practice_name: practiceName.trim() || null,
        specialty: specialty.trim() || null,
        headshot_url: headshotUrl.trim() || null,
        contact_label: contactLabel.trim() || null,
        contact_url: contactUrl.trim() || null,
      })
      .eq("id", user.id);

    if (updateError) {
      setStatus("error");
      setError(updateError.message);
      return;
    }
    setStatus("saved");
    setTimeout(() => setStatus("idle"), 2500);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm"
    >
      <div>
        <label className={labelClass}>Your name *</label>
        <input
          type="text"
          required
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

      <div className="pt-2 border-t border-white/5">
        <p className="text-xs font-medium uppercase tracking-wider text-emerald-300/70">
          Client-facing brand
        </p>
        <p className={helperClass}>
          Shows at the top of every plan you send to a client.
        </p>
      </div>

      <div>
        <label className={labelClass}>Headshot URL</label>
        <input
          type="url"
          value={headshotUrl}
          onChange={(e) => setHeadshotUrl(e.target.value)}
          placeholder="https://…/me.jpg"
          className={inputClass}
        />
        <p className={helperClass}>Square image, ideally ≥256×256.</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={labelClass}>Contact label</label>
          <input
            type="text"
            value={contactLabel}
            onChange={(e) => setContactLabel(e.target.value)}
            placeholder="Text me"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Contact URL</label>
          <input
            type="text"
            value={contactUrl}
            onChange={(e) => setContactUrl(e.target.value)}
            placeholder="sms:+15551234567"
            className={inputClass}
          />
        </div>
      </div>
      <p className={helperClass}>
        Examples: <code>sms:+15551234567</code>,{" "}
        <code>https://cal.com/jane</code>, <code>mailto:jane@example.com</code>,{" "}
        <code>https://wa.me/15551234567</code>.
      </p>

      {error && <p className="text-xs text-red-400">{error}</p>}
      {status === "saved" && (
        <p className="text-xs text-emerald-300">Saved.</p>
      )}

      <button
        type="submit"
        disabled={status === "saving" || !displayName.trim()}
        className={primaryButtonClass}
      >
        {status === "saving" ? "Saving…" : "Save profile"}
      </button>
    </form>
  );
}
