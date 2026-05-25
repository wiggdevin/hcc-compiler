"use client";

import { useState } from "react";

const primaryBtn =
  "inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-40";
const secondaryBtn =
  "inline-flex items-center justify-center rounded-lg border border-white/15 bg-white/[0.06] px-4 py-2 text-sm font-medium text-white transition hover:bg-white/[0.12] disabled:cursor-not-allowed disabled:opacity-40";

interface Props {
  hasActiveSub: boolean;
}

export function BillingActions({ hasActiveSub }: Props) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function redirectToUrl(route: string, body?: object) {
    setError(null);
    setLoading(route);
    try {
      const res = await fetch(route, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      const json = (await res.json()) as { url?: string; error?: string };
      if (!res.ok || !json.url) {
        setError(json.error ?? "Something went wrong. Please try again.");
        return;
      }
      window.location.href = json.url;
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm">
      <h2 className="text-base font-medium text-white">Actions</h2>
      <div className="mt-4 flex flex-wrap gap-3">
        {hasActiveSub ? (
          <button
            onClick={() => redirectToUrl("/api/stripe/portal")}
            disabled={loading !== null}
            className={secondaryBtn}
          >
            {loading === "/api/stripe/portal" ? "Redirecting…" : "Manage subscription"}
          </button>
        ) : (
          <button
            onClick={() =>
              redirectToUrl("/api/stripe/checkout", { plan: "subscription" })
            }
            disabled={loading !== null}
            className={primaryBtn}
          >
            {loading === "/api/stripe/checkout" ? "Redirecting…" : "Subscribe — $79/mo"}
          </button>
        )}

        <button
          onClick={() =>
            redirectToUrl("/api/stripe/checkout", { plan: "credits", quantity: 1 })
          }
          disabled={loading !== null}
          className={secondaryBtn}
        >
          {loading === "/api/stripe/checkout" ? "Redirecting…" : "Buy a credit — $29"}
        </button>
      </div>

      {error && (
        <p className="mt-3 text-xs text-red-300">{error}</p>
      )}
    </section>
  );
}
