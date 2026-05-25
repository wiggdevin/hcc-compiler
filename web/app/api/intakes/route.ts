// POST /api/intakes — create an intake row + upload YAML to storage.
// GET  /api/intakes — list intakes for the current coach.
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { intakeToYaml, type ClientIntake } from "@/lib/intake-yaml";

export async function POST(request: Request) {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let payload: ClientIntake;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!payload.client_id || !payload.library_version) {
    return NextResponse.json(
      { error: "client_id and library_version are required" },
      { status: 400 },
    );
  }

  // Upload YAML to storage: intakes/<coach_id>/<client_id>.yaml
  const yamlText = intakeToYaml(payload);
  const yamlPath = `${user.id}/intake_${payload.client_id}.yaml`;
  const { error: storageError } = await supabase.storage
    .from("intakes")
    .upload(yamlPath, new Blob([yamlText], { type: "text/yaml" }), {
      upsert: true,
    });

  if (storageError) {
    console.error("Storage upload error:", storageError);
    // Non-fatal: proceed without yaml_path if storage fails.
  }

  // Insert intake row.
  const { data: intake, error: insertError } = await supabase
    .from("intakes")
    .insert({
      coach_id: user.id,
      client_id: payload.client_id,
      library_version: payload.library_version,
      payload,
      yaml_path: storageError ? null : yamlPath,
      status: "pending",
    })
    .select()
    .single();

  if (insertError) {
    return NextResponse.json({ error: insertError.message }, { status: 400 });
  }

  return NextResponse.json({ intake }, { status: 201 });
}

export async function GET() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: intakes, error } = await supabase
    .from("intakes")
    .select("id, client_id, library_version, status, created_at, compiled_at")
    .eq("coach_id", user.id)
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ intakes });
}
