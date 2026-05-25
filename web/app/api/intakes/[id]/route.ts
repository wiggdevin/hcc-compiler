// GET /api/intakes/[id] — fetch a single intake + its pack for the current coach.
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: intake, error } = await supabase
    .from("intakes")
    .select(
      "id, client_id, library_version, status, payload, created_at, compiled_at, error, packs(id, overall_confidence, pattern_count, atom_count, warnings_count, json_path, md_path, pdf_path, created_at)",
    )
    .eq("id", id)
    .eq("coach_id", user.id)
    .single();

  if (error || !intake) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  return NextResponse.json({ intake });
}
