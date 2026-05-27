import { loadShare } from "@/lib/data/share-loader";
import { loadCachedSchedule } from "@/lib/schedule/load";
import { CoachBrandHeader } from "@/components/coach-brand-header";
import { PlanViewer } from "./_components/plan-viewer";

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
  const share = await loadShare(token);
  const { coach, clientLabel, packId } = share;
  const schedule = await loadCachedSchedule(packId).catch(() => null);

  return (
    <main className="mx-auto min-h-screen w-full max-w-md bg-gradient-to-b from-[#070708] via-[#0b0b0d] to-[#070708] text-white">
      <CoachBrandHeader coach={coach} />
      {schedule ? (
        <PlanViewer schedule={schedule} coach={coach} />
      ) : (
        <PendingPlaceholder clientLabel={clientLabel} coachName={coach.display_name} />
      )}
    </main>
  );
}

function PendingPlaceholder({
  clientLabel,
  coachName,
}: {
  clientLabel: string;
  coachName: string;
}) {
  return (
    <section className="px-5 pb-24 pt-2">
      <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
        Your plan
      </p>
      <h1 className="mt-2 text-2xl font-light tracking-tight">
        Hi {clientLabel.replace(/_/g, " ")}.
      </h1>
      <p className="mt-3 text-sm text-white/60">
        {coachName} is preparing your day-by-day guide. Check back in a moment.
      </p>
    </section>
  );
}
