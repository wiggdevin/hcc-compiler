import { cn } from "@/lib/utils";
import { citationHref, citationKind } from "@/lib/format";
import type {
  Citation,
  ExistenceVerdict,
  FaithfulnessVerdict,
} from "@/lib/data/types";

const EXISTENCE_DOT: Record<ExistenceVerdict, string> = {
  VERIFIED: "bg-emerald-400",
  PLAUSIBLE: "bg-amber-300",
  UNVERIFIABLE: "bg-zinc-500",
  DOI_MISMATCH: "bg-rose-400",
  FABRICATED: "bg-rose-500",
};

const FAITHFULNESS_DOT: Record<FaithfulnessVerdict, string> = {
  VERIFIED: "bg-emerald-400",
  MINOR_DISTORTION: "bg-amber-300",
  MAJOR_DISTORTION: "bg-orange-400",
  UNSUPPORTED: "bg-rose-400",
  ACCESS_LIMITED: "bg-zinc-500",
};

interface Props {
  citation: Citation;
  className?: string;
}

export function CitationChip({ citation, className }: Props) {
  const kind = citationKind(citation.id);
  const href = citationHref(citation.id);
  const verified =
    citation.existence === "VERIFIED" && citation.faithfulness === "VERIFIED";

  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={cn(
        "group inline-flex items-center gap-2 rounded-md border px-2 py-1 text-[0.65rem] font-mono transition-colors",
        verified
          ? "border-emerald-400/30 bg-emerald-400/[0.04] text-emerald-100 hover:bg-emerald-400/[0.08]"
          : "border-white/10 bg-white/[0.03] text-zinc-300 hover:bg-white/[0.06] hover:text-white",
        className,
      )}
      title={
        citation.cited_title
          ? `${citation.cited_title}\n\n${citation.locator_quote}`
          : citation.locator_quote
      }
    >
      <span className="text-[0.55rem] uppercase tracking-wider text-zinc-500">
        {kind}
      </span>
      <span className="max-w-[18ch] truncate">{citation.id}</span>
      <span
        className={cn(
          "inline-block h-1.5 w-1.5 rounded-full",
          EXISTENCE_DOT[citation.existence],
        )}
        aria-label={`Existence ${citation.existence}`}
      />
      <span
        className={cn(
          "inline-block h-1.5 w-1.5 rounded-full",
          FAITHFULNESS_DOT[citation.faithfulness],
        )}
        aria-label={`Faithfulness ${citation.faithfulness}`}
      />
    </a>
  );
}
