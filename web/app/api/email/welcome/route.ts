/**
 * Internal POST endpoint — called from the Supabase auth callback after a
 * coach's first sign-in.
 *
 * Body: { email: string; coachName: string }
 *
 * Requires the request to carry the INTERNAL_API_SECRET header so this
 * endpoint can't be triggered from the public web.
 */
import { sendWelcomeEmail } from "@/lib/resend";

export async function POST(request: Request): Promise<Response> {
  // Guard: only allow calls from trusted internal callers (auth callback, etc.)
  const secret = request.headers.get("x-internal-secret");
  const expectedSecret = process.env.INTERNAL_API_SECRET;

  if (!expectedSecret) {
    // In dev without the secret set, allow the call so local testing isn't blocked.
    // In production this must be set — warn loudly.
    if (process.env.NODE_ENV === "production") {
      return new Response("INTERNAL_API_SECRET is not configured", {
        status: 500,
      });
    }
  } else if (secret !== expectedSecret) {
    return new Response("Unauthorized", { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return new Response("Invalid JSON body", { status: 400 });
  }

  if (
    typeof body !== "object" ||
    body === null ||
    typeof (body as Record<string, unknown>).email !== "string" ||
    typeof (body as Record<string, unknown>).coachName !== "string"
  ) {
    return new Response(
      "Body must include { email: string; coachName: string }",
      { status: 400 },
    );
  }

  const { email, coachName } = body as { email: string; coachName: string };

  const result = await sendWelcomeEmail({ to: email, coachName });

  if (result.error) {
    return new Response(JSON.stringify({ error: result.error }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(JSON.stringify({ id: result.id }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
