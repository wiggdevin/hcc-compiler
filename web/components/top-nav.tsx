"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export function TopNav() {
  const pathname = usePathname();
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      setSignedIn(!!user);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSignedIn(!!session?.user);
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  if (pathname?.startsWith("/p/")) return null;

  return (
    <nav className="sticky top-0 z-20 flex items-center justify-between border-b border-white/[0.06] bg-[var(--bg)]/80 px-4 py-3 backdrop-blur-sm md:px-8">
      <Link
        href={signedIn ? "/dashboard" : "/sign-in"}
        className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70 hover:text-emerald-300"
      >
        HCC Compiler
      </Link>
      <div className="flex items-center gap-4">
        {signedIn === null ? (
          // Prevent layout shift while hydrating.
          <span className="h-4 w-16 animate-pulse rounded bg-white/10" />
        ) : signedIn ? (
          <>
            <Link
              href="/dashboard"
              className="text-xs text-white/60 hover:text-white/90"
            >
              Dashboard
            </Link>
            <form action="/auth/sign-out" method="POST">
              <button
                type="submit"
                className="text-xs text-white/40 hover:text-white/70"
              >
                Sign out
              </button>
            </form>
          </>
        ) : (
          <Link
            href="/sign-in"
            className="text-xs text-white/60 hover:text-white/90"
          >
            Sign in
          </Link>
        )}
      </div>
    </nav>
  );
}
