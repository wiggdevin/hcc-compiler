/**
 * Server-only Resend client + transactional email helpers.
 * Never import this in Client Components.
 */
import { Resend } from "resend";
import { render } from "@react-email/render";
import { WelcomeEmail } from "./email-templates/welcome";
import { PlanReadyEmail } from "./email-templates/plan-ready";

// Lazily instantiated so the module can be imported without RESEND_API_KEY
// in environments where it's not needed (e.g., during static build passes).
let _client: Resend | null = null;

function getClient(): Resend {
  if (!_client) {
    const key = process.env.RESEND_API_KEY;
    if (!key) {
      throw new Error(
        "RESEND_API_KEY is not set. Add it to your .env.local or Vercel environment.",
      );
    }
    _client = new Resend(key);
  }
  return _client;
}

const FROM_ADDRESS =
  process.env.RESEND_FROM_ADDRESS ?? "HCC Compiler <noreply@hccompiler.com>";

export interface SendResult {
  id: string | null;
  error: string | null;
}

/**
 * Send a welcome email on first sign-in.
 * Returns the Resend message ID on success, or an error string on failure.
 */
export async function sendWelcomeEmail(params: {
  to: string;
  coachName: string;
}): Promise<SendResult> {
  const { to, coachName } = params;

  const html = await render(WelcomeEmail({ coachName }));

  const { data, error } = await getClient().emails.send({
    from: FROM_ADDRESS,
    to,
    subject: "Welcome to HCC Compiler",
    html,
  });

  if (error) {
    console.error("[resend] sendWelcomeEmail failed:", error);
    return { id: null, error: error.message };
  }

  return { id: data?.id ?? null, error: null };
}

/**
 * Notify a coach that a compiled plan is ready for a client.
 */
export async function sendPlanReadyEmail(params: {
  to: string;
  coachName: string;
  clientName: string;
  packUrl: string;
}): Promise<SendResult> {
  const { to, coachName, clientName, packUrl } = params;

  const html = await render(PlanReadyEmail({ coachName, clientName, packUrl }));

  const { data, error } = await getClient().emails.send({
    from: FROM_ADDRESS,
    to,
    subject: `Your plan for ${clientName} is ready`,
    html,
  });

  if (error) {
    console.error("[resend] sendPlanReadyEmail failed:", error);
    return { id: null, error: error.message };
  }

  return { id: data?.id ?? null, error: null };
}
