import { redirect } from "next/navigation";
import { requireCoach } from "@/lib/auth";
import { getSupabaseServerClient } from "@/lib/supabase/server";
import { BillingActions } from "./billing-actions";

export const metadata = { title: "Billing · Aura Clinic" };

interface SubscriptionRow {
  status: string;
  plan: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

interface CreditsRow {
  balance: number;
}

export default async function BillingPage() {
  // requireCoach() redirects to /sign-in if unauthenticated.
  const coach = await requireCoach();
  const supabase = await getSupabaseServerClient();

  const [{ data: sub }, { data: credits }] = await Promise.all([
    supabase
      .from("subscriptions")
      .select("status, plan, current_period_end, cancel_at_period_end")
      .eq("coach_id", coach.id)
      .maybeSingle<SubscriptionRow>(),
    supabase
      .from("credits")
      .select("balance")
      .eq("coach_id", coach.id)
      .maybeSingle<CreditsRow>(),
  ]);

  const hasActiveSub = sub !== null && (sub.status === "active" || sub.status === "trialing");
  const balance = credits?.balance ?? 0;

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-12 md:px-8">
      <header className="mb-10">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
          Account
        </p>
        <h1 className="mt-3 text-3xl font-light tracking-tight text-white">Billing</h1>
      </header>

      <div className="space-y-6">
        {/* Subscription card */}
        <section className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm">
          <h2 className="text-base font-medium text-white">Subscription</h2>

          {hasActiveSub ? (
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center rounded-full border border-emerald-400/40 bg-emerald-500/20 px-2.5 py-0.5 text-xs font-medium text-emerald-100">
                  {sub!.status === "trialing" ? "Trial" : "Active"}
                </span>
                <span className="text-sm text-white/70">Active Coach — $79 / month</span>
              </div>
              <p className="text-xs text-white/50">
                {sub!.cancel_at_period_end
                  ? `Cancels at end of billing period — ${formatDate(sub!.current_period_end)}`
                  : `Renews ${formatDate(sub!.current_period_end)}`}
              </p>
            </div>
          ) : sub && sub.status === "past_due" ? (
            <div className="mt-4">
              <span className="inline-flex items-center rounded-full border border-amber-400/40 bg-amber-500/20 px-2.5 py-0.5 text-xs font-medium text-amber-100">
                Past due
              </span>
              <p className="mt-2 text-xs text-white/50">
                Payment failed. Update your card to restore full access.
              </p>
            </div>
          ) : sub && sub.status === "canceled" ? (
            <div className="mt-4">
              <span className="inline-flex items-center rounded-full border border-red-400/30 bg-red-500/10 px-2.5 py-0.5 text-xs font-medium text-red-200">
                Canceled
              </span>
              <p className="mt-2 text-xs text-white/50">Subscription ended. Subscribe again to compile plans.</p>
            </div>
          ) : (
            <p className="mt-3 text-sm text-white/60">
              No active subscription. Subscribe for unlimited compiles at $79/mo.
            </p>
          )}
        </section>

        {/* Credits card */}
        <section className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm">
          <h2 className="text-base font-medium text-white">Plan credits</h2>
          <div className="mt-4 flex items-end gap-2">
            <span className="text-4xl font-light tabular-nums text-white">{balance}</span>
            <span className="mb-1 text-sm text-white/50">credit{balance !== 1 ? "s" : ""} remaining</span>
          </div>
          <p className="mt-2 text-xs text-white/40">
            Each credit compiles one evidence pack. Credits don&apos;t expire.
          </p>
        </section>

        {/* Action buttons — client component for fetch calls */}
        <BillingActions hasActiveSub={hasActiveSub} />
      </div>
    </main>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}
