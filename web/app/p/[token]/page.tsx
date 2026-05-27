import { loadShare } from "@/lib/data/share-loader";
import { CoachBrandHeader } from "@/components/coach-brand-header";

export const metadata = {
  title: "Your plan",
  // Prevent indexing of private client plans.
  robots: { index: false, follow: false },
};

export default async function ClientPlanPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const { coach, clientLabel } = await loadShare(token);

  return (
    <main className="mx-auto min-h-screen w-full max-w-md bg-gradient-to-b from-[#070708] via-[#0b0b0d] to-[#070708] text-white">
      <CoachBrandHeader coach={coach} />
      <section className="px-5 pb-24 pt-2">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
          Your plan
        </p>
        <h1 className="mt-2 text-2xl font-light tracking-tight">
          Hi {clientLabel.replace(/_/g, " ")}.
        </h1>
        <p className="mt-3 text-sm text-white/60">
          {coach.display_name} has put together a plan for you. Your day-by-day
          guide is being prepared — check back in a moment, or your coach will
          share it directly.
        </p>
        <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-5 backdrop-blur-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-white/40">
            Coming next
          </p>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>• Today — your 3-5 things to do right now</li>
            <li>• This week — a 7-day glance</li>
            <li>• Why — the science backing every recommendation</li>
            <li>• Talk to {coach.display_name.split(" ")[0]}</li>
          </ul>
        </div>
      </section>
    </main>
  );
}
