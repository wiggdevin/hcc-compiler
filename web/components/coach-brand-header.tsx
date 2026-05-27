import type { CoachBrand } from "@/lib/data/share-loader";

function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

export function CoachBrandHeader({ coach }: { coach: CoachBrand }) {
  const initials = initialsOf(coach.display_name);
  const showImage =
    coach.headshot_url &&
    /^https?:\/\//.test(coach.headshot_url);

  return (
    <header className="flex items-center gap-3 px-5 pt-6 pb-4">
      <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-full border border-white/10 bg-gradient-to-br from-emerald-500/30 via-cyan-500/20 to-purple-500/20">
        {showImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={coach.headshot_url!}
            alt={coach.display_name}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="absolute inset-0 grid place-items-center text-sm font-semibold text-white/80">
            {initials || "?"}
          </span>
        )}
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-white">
          {coach.display_name}
        </p>
        {coach.practice_name ? (
          <p className="truncate text-xs text-white/50">
            {coach.practice_name}
          </p>
        ) : null}
      </div>
    </header>
  );
}
