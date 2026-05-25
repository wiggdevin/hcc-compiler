/**
 * GET /api/packs/[id]/pdf
 *
 * Renders the pack overview page to PDF using puppeteer-core.
 * Requires a signed-in coach. Verifies the pack belongs to the requesting
 * coach via Supabase before rendering.
 *
 * In production (Lambda/Vercel): uses @sparticuz/chromium.
 * In local dev: falls back to the system Chromium found on PATH.
 */
import puppeteer from "puppeteer-core";
import chromium from "@sparticuz/chromium";
import { headers } from "next/headers";
import { createClient as createServerClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";

// Attempt to stub getCurrentCoach from subagent A's file if it exists,
// otherwise fall back to inline Supabase session check.
async function resolveCoachId(): Promise<string | null> {
  try {
    // Dynamically import so the build doesn't fail if the file isn't created yet.
    // Subagent A creates web/lib/auth.ts with getCurrentCoach().
    const { getCurrentCoach } = await import("@/lib/auth");
    const coach = await getCurrentCoach();
    return coach?.id ?? null;
  } catch {
    // auth.ts not yet created by subagent A — fall back to session check.
    const supabase = await createServerClient();
    const { data } = await supabase.auth.getUser();
    return data.user?.id ?? null;
  }
}

function getOrigin(): string {
  // The canonical app URL for rendering the page via Puppeteer.
  // In Vercel preview/production, NEXT_PUBLIC_APP_URL or VERCEL_URL is set.
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (appUrl) return appUrl;

  const vercelUrl = process.env.VERCEL_URL;
  if (vercelUrl) return `https://${vercelUrl}`;

  return "http://localhost:3000";
}

async function resolveChromiumExecutable(): Promise<string> {
  // On Lambda/Vercel (linux) @sparticuz/chromium will download and unpack.
  // In local dev the env var SPARTICUZ_CHROMIUM_PATH can point at a local build,
  // or we fall back to system Chromium.
  if (process.env.SPARTICUZ_CHROMIUM_PATH) {
    return process.env.SPARTICUZ_CHROMIUM_PATH;
  }

  try {
    return await chromium.executablePath();
  } catch {
    // The sparticuz binary can't run on macOS/Windows dev machines.
    // Fall through to system Chromium.
  }

  // Common system Chromium locations for local dev.
  const candidates = [
    process.env.CHROMIUM_PATH,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
  ].filter(Boolean) as string[];

  const { promises: fs } = await import("node:fs");
  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      // not found, try next
    }
  }

  throw new Error(
    "No Chromium binary found. Set CHROMIUM_PATH or SPARTICUZ_CHROMIUM_PATH env var.",
  );
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;

  // ── Auth check ──
  const coachId = await resolveCoachId();
  if (!coachId) {
    return new Response("Unauthorized", { status: 401 });
  }

  // ── Ownership check via admin client (bypasses RLS to read pack row) ──
  const admin = createAdminClient();
  const { data: pack, error } = await admin
    .from("packs")
    .select("id, coach_id, client_id")
    .eq("id", id)
    .single();

  if (error || !pack) {
    return new Response("Pack not found", { status: 404 });
  }

  if (pack.coach_id !== coachId) {
    return new Response("Forbidden", { status: 403 });
  }

  // ── Render to PDF ──
  const pageUrl = `${getOrigin()}/clients/${pack.client_id}/overview`;

  let executablePath: string;
  try {
    executablePath = await resolveChromiumExecutable();
  } catch (err) {
    console.error("[pdf] chromium resolution failed:", err);
    return new Response("PDF generation unavailable — no Chromium binary", {
      status: 503,
    });
  }

  // headless: 'new' is the modern headless mode (no chrome UI remnants)
  const browser = await puppeteer.launch({
    executablePath,
    headless: "new" as Parameters<typeof puppeteer.launch>[0] extends { headless: infer H } ? H : never,
    args: [
      ...chromium.args,
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-gpu",
      // Carry the session cookie so the page renders for the authenticated user.
      // We pass a cookie per the current request headers instead of sharing credentials.
    ],
  });

  let pdfBuffer: Buffer;
  try {
    const page = await browser.newPage();

    // Forward the session cookie so the page can render authenticated content.
    const requestHeaders = await headers();
    const cookieHeader = requestHeaders.get("cookie") ?? "";
    if (cookieHeader) {
      const origin = getOrigin();
      const url = new URL(origin);
      const cookies = cookieHeader.split(";").map((part) => {
        const [name, ...rest] = part.trim().split("=");
        return {
          name: name.trim(),
          value: rest.join("=").trim(),
          domain: url.hostname,
          path: "/",
        };
      });
      await page.setCookie(...cookies);
    }

    await page.goto(pageUrl, {
      waitUntil: "networkidle0",
      timeout: 30_000,
    });

    // Trigger the print media query so the print stylesheet kicks in.
    await page.emulateMediaType("print");

    const pdf = await page.pdf({
      format: "A4",
      printBackground: true,
      margin: { top: "18mm", bottom: "18mm", left: "14mm", right: "14mm" },
    });

    pdfBuffer = Buffer.from(pdf);
  } finally {
    await browser.close();
  }

  const filename = `hcc-plan-${pack.client_id ?? id}.pdf`;

  return new Response(new Uint8Array(pdfBuffer), {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${filename}"`,
      // No caching — plans may be recompiled.
      "Cache-Control": "no-store",
    },
  });
}
