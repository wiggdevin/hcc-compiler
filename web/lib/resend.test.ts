import { describe, expect, it } from "vitest";
import { normalizeFromAddress } from "./resend";

const FALLBACK = "HCC Compiler <noreply@hccompiler.com>";

describe("normalizeFromAddress", () => {
  it("wraps a bare email with the default sender name", () => {
    expect(normalizeFromAddress("noreply@example.com")).toBe(
      "HCC Compiler <noreply@example.com>"
    );
  });

  it("passes through 'Name <addr>' format unchanged", () => {
    expect(normalizeFromAddress("Coach <c@example.com>")).toBe(
      "Coach <c@example.com>"
    );
  });

  it("trims trailing whitespace and newlines (Vercel env quirk)", () => {
    expect(normalizeFromAddress("noreply@example.com\n")).toBe(
      "HCC Compiler <noreply@example.com>"
    );
    expect(normalizeFromAddress("  Coach <c@x.com>  ")).toBe("Coach <c@x.com>");
  });

  it("falls back to default when no input and no env var", () => {
    delete process.env.RESEND_FROM;
    delete process.env.RESEND_FROM_ADDRESS;
    expect(normalizeFromAddress()).toBe(FALLBACK);
  });

  it("explicit empty string falls back to default", () => {
    expect(normalizeFromAddress("")).toBe(FALLBACK);
  });
});
