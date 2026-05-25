/**
 * GET /api/sample/carl.md
 *
 * Serves the Carl sample plan Markdown file for the public "See a sample plan"
 * link on the marketing landing page. No auth required — this is intentionally
 * public so coaches can evaluate the output before signing up.
 */
import { promises as fs } from "node:fs";
import path from "node:path";

export async function GET(): Promise<Response> {
  // Resolve from CWD (web/) up one level to the repo root, then into docs/examples/sp2/
  const mdPath = path.resolve(
    process.cwd(),
    "..",
    "docs",
    "examples",
    "sp2",
    "carl.md",
  );

  let body: string;
  try {
    body = await fs.readFile(mdPath, "utf-8");
  } catch {
    return new Response("Sample plan not found", { status: 404 });
  }

  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": 'attachment; filename="carl-sample-plan.md"',
      // Allow public caching — content doesn't change without a deploy.
      "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
    },
  });
}
