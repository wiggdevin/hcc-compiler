import { promises as fs } from "node:fs";
import path from "node:path";
import { getPersona } from "@/lib/data/personas";

/**
 * Serve the coach-grade `.md` plan that lives next to the compiled `.json`.
 * Persona slugs do not always match the on-disk basename — `persona.packFile`
 * (e.g. `test_v2_tori_shaw.json`) is the canonical mapping; we swap `.json`
 * for `.md` to find the sibling.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const persona = getPersona(id);
  if (!persona) {
    return new Response("Persona not found", { status: 404 });
  }

  const basename = persona.packFile.replace(/\.json$/, "");
  const mdPath = path.resolve(
    process.cwd(),
    "..",
    "docs",
    "examples",
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
