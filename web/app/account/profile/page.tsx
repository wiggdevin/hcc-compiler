import { redirect } from "next/navigation";
import { requireCoach } from "@/lib/auth";
import { getSupabaseServerClient } from "@/lib/supabase/server";
import { ProfileForm } from "./profile-form";

export const metadata = { title: "Profile · Aura Clinic" };

interface CoachRow {
  display_name: string | null;
  practice_name: string | null;
  specialty: string | null;
  headshot_url: string | null;
  contact_label: string | null;
  contact_url: string | null;
}

export default async function ProfilePage() {
  const coach = await requireCoach();
  const supabase = await getSupabaseServerClient();

  const { data: row } = await supabase
    .from("coaches")
    .select(
      "display_name, practice_name, specialty, headshot_url, contact_label, contact_url",
    )
    .eq("id", coach.id)
    .maybeSingle<CoachRow>();

  if (!row) {
    redirect("/onboarding");
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <header className="mb-8">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
          Account
        </p>
        <h1 className="mt-3 text-2xl font-light tracking-tight text-white">
          Your profile
        </h1>
        <p className="mt-2 text-sm text-white/50">
          What your clients see when you send them a plan.
        </p>
      </header>
      <ProfileForm initial={row} />
    </main>
  );
}
