// getCurrentCoach / requireCoach — shared helpers for RSC and Route Handlers.
// Throw a redirect (via next/navigation) if the user is not signed in.
// Return the Supabase User object; the caller fetches the coaches row if needed.
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export async function getCurrentCoach() {
  const supabase = await createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    redirect("/sign-in");
  }

  return user;
}

// Alias used by the Stripe/billing subagent files.
export const requireCoach = getCurrentCoach;
