// Server Supabase client — for use in Server Components and Route Handlers.
// Reads/writes cookies to carry the session across requests.
//
// Exports:
//   createClient()           — canonical name
//   getSupabaseServerClient() — alias used by billing subagent files
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Throws when called from a Server Component — safe to ignore.
            // The middleware will refresh the session on the next request.
          }
        },
      },
    },
  );
}

// Alias used by the Stripe/billing subagent files.
export const getSupabaseServerClient = createClient;
