// Supabase OAuth/magic-link code exchange handler.
// Supabase redirects here after the user clicks the magic-link email.
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      // Check if the coach has completed onboarding.
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (user) {
        const { data: coach } = await supabase
          .from("coaches")
          .select("onboarded_at")
          .eq("id", user.id)
          .single();

        if (!coach?.onboarded_at) {
          return NextResponse.redirect(`${origin}/onboarding`);
        }
      }

      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/sign-in?error=auth_failed`);
}
