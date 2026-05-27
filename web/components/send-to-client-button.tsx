"use client";

import { useState } from "react";
import { Send, X, Copy, Check } from "lucide-react";

type Status = "idle" | "sending" | "success" | "error" | "partial";

interface Props {
  packId: string;
  clientLabel: string;
}

const inputClass =
  "mt-1 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-white/30 focus:outline-none";
const labelClass =
  "block text-xs font-medium uppercase tracking-wider text-white/60";

function firstNameOf(label: string): string {
  return label.split(/[_\s-]/)[0] ?? label;
}

export function SendToClientButton({ packId, clientLabel }: Props) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState(firstNameOf(clientLabel));
  const [message, setMessage] = useState(
    `Hi ${firstNameOf(clientLabel)} — I've put together a 7-day plan for you. Open it on your phone, it's designed for that.`,
  );
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [packUrl, setPackUrl] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("sending");
    setError(null);
    setWarning(null);

    const res = await fetch(`/api/packs/${packId}/share`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        clientEmail: email.trim(),
        clientFirstName: firstName.trim() || undefined,
        customMessage: message.trim() || undefined,
      }),
    });
    const data = (await res.json().catch(() => ({}))) as {
      packUrl?: string;
      error?: string;
      warning?: string;
      redirect?: string;
    };

    if (res.status === 412 && data.redirect) {
      setStatus("error");
      setError(`Set up your profile first.`);
      return;
    }
    if (!res.ok && res.status !== 207) {
      setStatus("error");
      setError(data.error ?? `Failed (${res.status})`);
      return;
    }
    setPackUrl(data.packUrl ?? null);
    if (res.status === 207) {
      setStatus("partial");
      setWarning(data.warning ?? "Email failed; link still valid.");
    } else {
      setStatus("success");
    }
  }

  async function copyLink() {
    if (!packUrl) return;
    await navigator.clipboard.writeText(packUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function reset() {
    setStatus("idle");
    setError(null);
    setWarning(null);
    setPackUrl(null);
    setCopied(false);
  }

  return (
    <>
      <button
        onClick={() => {
          reset();
          setOpen(true);
        }}
        className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/40 bg-emerald-500/15 px-4 py-2 text-sm font-medium text-emerald-100 transition hover:bg-emerald-500/25"
      >
        <Send className="h-4 w-4" />
        Send to client
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
        >
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0b0b0d] p-6 shadow-2xl">
            <header className="mb-5 flex items-start justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
                  Share
                </p>
                <h2 className="mt-2 text-lg font-light tracking-tight text-white">
                  Send {firstNameOf(clientLabel)} their plan
                </h2>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="rounded-md p-1 text-white/40 hover:bg-white/5 hover:text-white/80"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </header>

            {status === "success" || status === "partial" ? (
              <div className="space-y-4">
                <div className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 p-3">
                  <p className="text-sm font-medium text-emerald-100">
                    {status === "success"
                      ? `Sent to ${email}.`
                      : "Token created."}
                  </p>
                  {warning ? (
                    <p className="mt-1 text-xs text-amber-200/80">{warning}</p>
                  ) : null}
                </div>
                {packUrl ? (
                  <div>
                    <label className={labelClass}>Share link</label>
                    <div className="mt-1 flex gap-2">
                      <input
                        readOnly
                        value={packUrl}
                        className={inputClass}
                        onFocus={(e) => e.currentTarget.select()}
                      />
                      <button
                        onClick={copyLink}
                        className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/15 bg-white/[0.04] px-3 text-xs font-medium text-white/80 hover:bg-white/10"
                      >
                        {copied ? (
                          <Check className="h-3.5 w-3.5 text-emerald-300" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>
                ) : null}
                <button
                  onClick={() => setOpen(false)}
                  className="w-full rounded-lg border border-white/15 bg-white/[0.04] py-2.5 text-sm font-medium text-white/80 hover:bg-white/10"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className={labelClass}>Client email</label>
                  <input
                    type="email"
                    required
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="client@example.com"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>First name</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Personal note</label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows={3}
                    className={inputClass + " resize-none"}
                  />
                </div>

                {error ? (
                  <p className="text-xs text-red-400">{error}</p>
                ) : null}

                <p className="text-[11px] text-white/40">
                  Generating the personalized schedule takes ~30 seconds before
                  the email sends.
                </p>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setOpen(false)}
                    className="flex-1 rounded-lg border border-white/10 bg-white/[0.02] py-2.5 text-sm font-medium text-white/70 hover:bg-white/[0.06]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={status === "sending" || !email.trim()}
                    className="flex-1 rounded-lg border border-emerald-400/40 bg-emerald-500/20 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {status === "sending" ? "Sending…" : "Send"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
