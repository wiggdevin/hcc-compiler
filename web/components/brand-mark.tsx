/** Inline DNA-style mark, replaces the iconify dependency in AURA. */
export function BrandMark({ size = 24 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M5 4c2 2.5 5 4 7 4s5-1.5 7-4" />
      <path d="M5 20c2-2.5 5-4 7-4s5 1.5 7 4" />
      <path d="M5 4c0 5 14 11 14 16" />
      <path d="M19 4c0 5-14 11-14 16" />
    </svg>
  );
}
