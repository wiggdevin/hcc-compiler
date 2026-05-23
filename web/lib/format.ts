/** Numeric + display formatters used throughout the UI. */

export function formatPercent(value: number, fractionDigits = 1): string {
  if (!Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(fractionDigits)}%`;
}

export function formatScore(value: number): string {
  return formatPercent(value, 0);
}

export function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

export function citationHref(id: string): string {
  // Heuristic: numeric → PMID, slash → DOI
  if (/^\d+$/.test(id)) return `https://pubmed.ncbi.nlm.nih.gov/${id}/`;
  if (id.includes("/")) return `https://doi.org/${id}`;
  return `https://doi.org/${id}`;
}

export function citationKind(id: string): "PMID" | "DOI" {
  return /^\d+$/.test(id) ? "PMID" : "DOI";
}

export function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max - 1).trimEnd() + "…";
}

/** Strips the leading ⚠ glyph + "(matches intake)" suffix from warning text. */
export function cleanWarning(w: string): string {
  return w.replace(/^[⚠⚠️]\s*/, "").replace(/\s*\(matches intake\)\s*$/, "");
}

/** Format an evidence-level label with a soft descriptor. */
export function evidenceDescriptor(level: string): string {
  switch (level) {
    case "L1":
      return "Meta-analysis";
    case "L2":
      return "Systematic review";
    case "L3":
      return "Cohort / RCT";
    case "L4":
      return "Mechanistic";
    default:
      return level;
  }
}
