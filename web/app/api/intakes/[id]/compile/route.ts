// POST /api/intakes/[id]/compile — triggers the compiler-api sidecar.
// Marks the intake as 'compiling', forwards to COMPILER_API_URL/compile,
// then updates the row (and creates a packs row) on success.
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { canCompile, consumeCredit } from "@/lib/billing";

export async function POST(
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

  // Fetch intake — verifies ownership via RLS.
  const { data: intake, error: fetchError } = await supabase
    .from("intakes")
    .select("id, coach_id, client_id, library_version, payload, status")
    .eq("id", id)
    .eq("coach_id", user.id)
    .single();

  if (fetchError || !intake) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  if (intake.status === "compiling") {
    return NextResponse.json({ error: "Already compiling" }, { status: 409 });
  }

  const billing = await canCompile(user.id);
  if (!billing.ok) {
    return NextResponse.json({ error: billing.reason }, { status: 402 });
  }

  // Mark as compiling (use admin to bypass any partial RLS on status updates).
  const admin = createAdminClient();
  await admin.from("intakes").update({ status: "compiling" }).eq("id", id);

  const compilerUrl = process.env.COMPILER_API_URL;
  const compilerToken = process.env.COMPILER_API_TOKEN;

  if (!compilerUrl) {
    await admin
      .from("intakes")
      .update({ status: "failed", error: "COMPILER_API_URL not configured" })
      .eq("id", id);
    return NextResponse.json(
      { error: "Compiler not configured" },
      { status: 503 },
    );
  }

  // Fly compiler-api is stateless — it returns inline {json, md}.
  // We write the output to Supabase Storage and record the paths.
  let compileResult: { json: Record<string, unknown>; md: string };

  try {
    const resp = await fetch(`${compilerUrl}/compile`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(compilerToken ? { Authorization: `Bearer ${compilerToken}` } : {}),
      },
      body: JSON.stringify({ intake: intake.payload }),
    });

    if (!resp.ok) {
      const detail = await resp.text();
      throw new Error(`Compiler returned ${resp.status}: ${detail}`);
    }

    compileResult = await resp.json();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    await admin
      .from("intakes")
      .update({ status: "failed", error: msg })
      .eq("id", id);
    return NextResponse.json({ error: msg }, { status: 502 });
  }

  // Upload artifacts to the `packs` storage bucket.
  const jsonPath = `${intake.coach_id}/${intake.id}.json`;
  const mdPath = `${intake.coach_id}/${intake.id}.md`;

  const [{ error: jsonUpErr }, { error: mdUpErr }] = await Promise.all([
    admin.storage.from("packs").upload(
      jsonPath,
      new Blob([JSON.stringify(compileResult.json, null, 2)], {
        type: "application/json",
      }),
      { upsert: true, contentType: "application/json" },
    ),
    admin.storage.from("packs").upload(
      mdPath,
      new Blob([compileResult.md], { type: "text/markdown" }),
      { upsert: true, contentType: "text/markdown" },
    ),
  ]);

  if (jsonUpErr || mdUpErr) {
    const msg = jsonUpErr?.message ?? mdUpErr?.message ?? "storage upload failed";
    await admin
      .from("intakes")
      .update({ status: "failed", error: msg })
      .eq("id", id);
    return NextResponse.json({ error: msg }, { status: 500 });
  }

  // Sum per-domain pattern/atom/warning counts. The compile JSON shape is
  // { domain_recommendations: { <domain>: { patterns, atoms, gaps } } }.
  // overall_confidence is computed client-side from per-atom + per-pattern
  // scores via web/lib/scoring.ts, so we leave it null at insert time.
  const dr = (compileResult.json?.domain_recommendations ?? {}) as Record<
    string,
    { patterns?: unknown[]; atoms?: unknown[]; warnings?: unknown[] }
  >;
  let patternCount = 0;
  let atomCount = 0;
  let warningsCount = 0;
  for (const d of Object.values(dr)) {
    if (Array.isArray(d.patterns)) patternCount += d.patterns.length;
    if (Array.isArray(d.atoms)) atomCount += d.atoms.length;
    if (Array.isArray(d.warnings)) warningsCount += d.warnings.length;
  }

  const { error: packError } = await admin.from("packs").insert({
    intake_id: intake.id,
    coach_id: intake.coach_id,
    library_version: intake.library_version,
    json_path: jsonPath,
    md_path: mdPath,
    pdf_path: null,
    overall_confidence: null,
    pattern_count: patternCount,
    atom_count: atomCount,
    warnings_count: warningsCount,
  });

  if (packError) {
    await admin
      .from("intakes")
      .update({ status: "failed", error: packError.message })
      .eq("id", id);
    return NextResponse.json({ error: packError.message }, { status: 500 });
  }

  await admin
    .from("intakes")
    .update({ status: "compiled", compiled_at: new Date().toISOString() })
    .eq("id", id);

  if (billing.remaining !== undefined) {
    await consumeCredit(user.id);
  }

  return NextResponse.json({ ok: true, intake_id: id });
}
