import { promises as fs } from "node:fs";
import path from "node:path";
import { getPersona } from "@/lib/data/personas";
import { createClient as createServerClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Serve the coach-grade `.md` plan.
 *
 * - Persona slug → reads sibling `.md` from docs/examples/sp2/ (public demos)
 * - UUID         → downloads from Supabase Storage `packs` bucket after
 *                 verifying the signed-in coach owns the pack.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  if (UUID_RE.test(id)) {
    return serveCoachPackMarkdown(id);
  }
  return servePersonaMarkdown(id);
}

async function servePersonaMarkdown(slug: string): Promise<Response> {
  const persona = getPersona(slug);
  if (!persona) {
    return new Response("Persona not found", { status: 404 });
  }
  const basename = persona.packFile.replace(/\.json$/, "");
  // Demo persona .md files are bundled into web/public/sp2/ at build time
  // (see web/package.json `prebuild`). Use the public dir, not ../docs/.
  const mdPath = path.resolve(
    process.cwd(),
    "public",
    "sp2",
    `${basename}.md`,
  );

  let body: string;
  try {
    body = await fs.readFile(mdPath, "utf-8");
  } catch {
    return new Response("Plan markdown not found", { status: 404 });
  }

  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="${basename}-plan.md"`,
      "Cache-Control": "no-store",
    },
  });
}

async function serveCoachPackMarkdown(packId: string): Promise<Response> {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return new Response("Unauthorized", { status: 401 });

  const { data: pack } = await supabase
    .from("packs")
    .select("md_path, intake_id")
    .eq("id", packId)
    .eq("coach_id", user.id)
    .maybeSingle();

  if (!pack) return new Response("Not found", { status: 404 });

  const admin = createAdminClient();
  const { data: blob, error } = await admin.storage
    .from("packs")
    .download(pack.md_path);
  if (error || !blob) return new Response("Not found", { status: 404 });

  return new Response(await blob.text(), {
    status: 200,
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="${pack.intake_id}-plan.md"`,
      "Cache-Control": "no-store",
    },
  });
}
