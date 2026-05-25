import {
  Html,
  Head,
  Body,
  Container,
  Heading,
  Text,
  Link,
  Hr,
  Preview,
} from "@react-email/components";
import * as React from "react";

interface WelcomeEmailProps {
  coachName: string;
}

const baseUrl =
  process.env.NEXT_PUBLIC_APP_URL ?? "https://hccompiler.com";

export function WelcomeEmail({ coachName }: WelcomeEmailProps) {
  return (
    <Html lang="en">
      <Head />
      <Preview>Welcome to HCC Compiler — start with your first client</Preview>
      <Body style={bodyStyle}>
        <Container style={containerStyle}>
          <Heading style={h1Style}>Welcome, {coachName}</Heading>

          <Text style={textStyle}>
            You are in. HCC Compiler is in closed beta, so access is limited —
            but you have it.
          </Text>

          <Text style={textStyle}>Here is how to get your first plan out:</Text>

          <Text style={listItemStyle}>
            1. Open your{" "}
            <Link href={`${baseUrl}/dashboard`} style={linkStyle}>
              dashboard
            </Link>
            .
          </Text>
          <Text style={listItemStyle}>
            2. Click <strong>New client</strong> and fill the intake form. It
            takes about five minutes for a typical client.
          </Text>
          <Text style={listItemStyle}>
            3. Submit. The compiler runs and a 6-domain evidence-backed plan is
            ready to review.
          </Text>

          <Text style={textStyle}>
            Not sure what the plan looks like?{" "}
            <Link href={`${baseUrl}/api/sample/carl.md`} style={linkStyle}>
              Download the Carl sample plan
            </Link>{" "}
            — a strength-and-hypertrophy client with renal-flagged
            contraindications. It shows how safety preflight flags surface
            inline.
          </Text>

          <Hr style={hrStyle} />

          <Text style={mutedStyle}>
            HCC Compiler is a reference tool for qualified coaches. Plans are
            evidence references, not prescriptions. Apply professional judgment
            before acting on any recommendation.
          </Text>

          <Text style={mutedStyle}>
            Questions? Reply to this email or reach us at{" "}
            <Link href="mailto:hello@hccompiler.com" style={linkStyle}>
              hello@hccompiler.com
            </Link>
            .
          </Text>
        </Container>
      </Body>
    </Html>
  );
}

export default WelcomeEmail;

// ── Inline styles (react-email renders to HTML email clients, not browsers) ──

const bodyStyle: React.CSSProperties = {
  backgroundColor: "#09090b",
  fontFamily: "Inter, system-ui, -apple-system, sans-serif",
  margin: 0,
  padding: "40px 0",
};

const containerStyle: React.CSSProperties = {
  maxWidth: "520px",
  margin: "0 auto",
  padding: "0 24px",
};

const h1Style: React.CSSProperties = {
  color: "#ffffff",
  fontSize: "22px",
  fontWeight: 600,
  lineHeight: 1.3,
  margin: "0 0 20px",
};

const textStyle: React.CSSProperties = {
  color: "#a1a1aa",
  fontSize: "14px",
  lineHeight: 1.6,
  margin: "0 0 14px",
};

const listItemStyle: React.CSSProperties = {
  color: "#a1a1aa",
  fontSize: "14px",
  lineHeight: 1.6,
  margin: "0 0 8px 12px",
};

const linkStyle: React.CSSProperties = {
  color: "#10b981",
  textDecoration: "underline",
};

const hrStyle: React.CSSProperties = {
  borderColor: "rgba(255,255,255,0.08)",
  margin: "24px 0",
};

const mutedStyle: React.CSSProperties = {
  color: "#52525b",
  fontSize: "12px",
  lineHeight: 1.55,
  margin: "0 0 10px",
};
