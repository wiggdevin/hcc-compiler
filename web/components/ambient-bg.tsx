export function AmbientBg() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      {/* Soft radial wash — top */}
      <div
        className="absolute -top-1/3 left-1/2 h-[80vh] w-[140vw] -translate-x-1/2 rounded-full opacity-60"
        style={{
          background:
            "radial-gradient(closest-side, rgba(59,130,246,0.10), rgba(124,63,252,0.05) 45%, transparent 70%)",
          filter: "blur(60px)",
        }}
      />
      {/* Lower right warm tertiary glow */}
      <div
        className="absolute bottom-[-20vh] right-[-10vw] h-[60vh] w-[60vw] rounded-full opacity-40"
        style={{
          background:
            "radial-gradient(closest-side, rgba(124,63,252,0.10), transparent 70%)",
          filter: "blur(80px)",
        }}
      />
      {/* Grain / overlay vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_30%,_rgba(0,0,0,0.55)_100%)]" />
    </div>
  );
}
