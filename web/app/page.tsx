import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import LandingPage from "./(marketing)/page";

/**
 * Root page:
 * - Signed-in coaches → /dashboard
 * - Unauthenticated visitors → renders the marketing landing page inline
 *   (the (marketing)/page.tsx is the same "/" URL; importing directly avoids
 *   a redirect loop while still keeping the marketing page in its own route group)
 */
export default async function RootPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect("/dashboard");
  }

  return <LandingPage />;
}
