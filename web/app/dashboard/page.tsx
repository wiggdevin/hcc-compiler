// Coach dashboard — server component.
// Lists all intakes + their packs for the currently signed-in coach.
import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

// packs.intake_id is unique (one pack per intake) so PostgREST returns
// the embedded `packs` resource as a single object, not an array.
type IntakeRow = {
  id: string;
  client_id: string;
  library_version: string;
  status: string;
  created_at: string;
  compiled_at: string | null;
  packs: { id: string; overall_confidence: number | null } | null;
};

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ compiled?: string }>;
}) {
  const { compiled } = await searchParams;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/sign-in");

  const { data: coach } = await supabase
    .from("coaches")
    .select("display_name, practice_name")
    .eq("id", user.id)
    .single();

  const { data: intakes } = await supabase
    .from("intakes")
    .select(
      "id, client_id, library_version, status, created_at, compiled_at, packs(id, overall_confidence)",
    )
    .eq("coach_id", user.id)
    .order("created_at", { ascending: false })
    .returns<IntakeRow[]>();

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending:
        "inline-flex items-center rounded-full border border-white/15 bg-white/[0.04] px-2 py-0.5 text-xs text-white/60",
      compiling:
        "inline-flex items-center rounded-full border border-amber-400/30 bg-amber-500/10 px-2 py-0.5 text-xs text-amber-200",
      compiled:
        "inline-flex items-center rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-200",
      failed:
        "inline-flex items-center rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-xs text-red-300",
    };
    return map[status] ?? map.pending;
  };

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-12 md:px-8">
      <header className="mb-10 flex items-end justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
            Dashboard
          </p>
          <h1 className="mt-3 text-3xl font-light tracking-tight text-white">
            {coach?.practice_name ?? coach?.display_name ?? "Your clients"}
          </h1>
          <p className="mt-1 text-sm text-white/50">
            {intakes?.length ?? 0} intake
            {intakes?.length !== 1 ? "s" : ""} on record
          </p>
        </div>
        <Link
          href="/new-client"
          className="inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30"
        >
          + New client
        </Link>
      </header>

      {compiled && (
        <div className="mb-6 rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
          Intake submitted — compile job queued. Refresh in a moment to see the
          result.
        </div>
      )}

      {!intakes || intakes.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-12 text-center">
          <p className="text-sm text-white/50">No clients yet.</p>
          <Link
            href="/new-client"
            className="mt-4 inline-flex items-center justify-center rounded-lg border border-white/15 bg-white/[0.06] px-4 py-2 text-sm text-white transition hover:bg-white/[0.12]"
          >
            Create your first intake
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/[0.02]">
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-white/50">
                  Client ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-white/50">
                  Library
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-white/50">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-white/50">
                  Confidence
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-white/50">
                  Created
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06]">
              {intakes.map((intake) => {
                const pack = intake.packs ?? null;
                const confidence =
                  pack?.overall_confidence != null
                    ? `${Math.round(pack.overall_confidence * 100)}%`
                    : "—";
                const date = new Date(intake.created_at).toLocaleDateString(
                  undefined,
                  { month: "short", day: "numeric", year: "numeric" },
                );
                return (
                  <tr
                    key={intake.id}
                    className="bg-white/[0.01] transition hover:bg-white/[0.04]"
                  >
                    <td className="px-4 py-3 font-mono text-white/90">
                      {intake.client_id}
                    </td>
                    <td className="px-4 py-3 text-white/60">
                      {intake.library_version}
                    </td>
                    <td className="px-4 py-3">
                      <span className={statusBadge(intake.status)}>
                        {intake.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 tabular text-white/70">
                      {confidence}
                    </td>
                    <td className="px-4 py-3 text-white/50">{date}</td>
                    <td className="px-4 py-3 text-right">
                      {intake.status === "compiled" && pack ? (
                        <Link
                          href={`/clients/${pack.id}/overview`}
                          className="text-xs text-emerald-300/80 hover:text-emerald-200"
                        >
                          View pack
                        </Link>
                      ) : intake.status === "pending" ? (
                        <form action={`/api/intakes/${intake.id}/compile`} method="POST">
                          <button
                            type="submit"
                            className="text-xs text-white/50 hover:text-white/80"
                          >
                            Compile
                          </button>
                        </form>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
