export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-[#070708] px-6 text-center text-white">
      <div className="max-w-sm">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-white/40">
          Link unavailable
        </p>
        <h1 className="mt-3 text-2xl font-light tracking-tight">
          This plan can&apos;t be opened.
        </h1>
        <p className="mt-4 text-sm text-white/50">
          The link may have expired or been revoked. Ask your coach to send a
          new one.
        </p>
      </div>
    </main>
  );
}
