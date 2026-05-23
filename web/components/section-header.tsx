import { cn } from "@/lib/utils";

interface Props {
  eyebrow: string;
  title: string;
  /** Use a slash to split into a two-tone "Word / Word" layout. */
  subtitle?: string;
  className?: string;
}

/**
 * Two-tone section heading with the AURA masked-word entrance.
 * Each word slides up from below a hidden mask on initial paint.
 */
export function SectionHeader({ eyebrow, title, subtitle, className }: Props) {
  const [a, b] = title.split(" / ");
  return (
    <header className={cn("mb-10 flex flex-col gap-3", className)}>
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-zinc-500 animate-fade-up">
        {eyebrow}
      </p>
      <h1 className="flex flex-wrap items-baseline gap-x-3 text-3xl font-semibold tracking-tight md:text-4xl">
        <span className="overflow-hidden inline-flex">
          <span
            className="animate-masked-word text-white"
            style={{ animationDelay: "0.05s" }}
          >
            {a}
          </span>
        </span>
        {b ? (
          <span className="overflow-hidden inline-flex">
            <span
              className="animate-masked-word text-zinc-500"
              style={{ animationDelay: "0.18s" }}
            >
              / {b}
            </span>
          </span>
        ) : null}
      </h1>
      {subtitle ? (
        <p
          className="max-w-xl text-sm text-zinc-400 animate-fade-up"
          style={{ animationDelay: "0.3s" }}
        >
          {subtitle}
        </p>
      ) : null}
    </header>
  );
}
