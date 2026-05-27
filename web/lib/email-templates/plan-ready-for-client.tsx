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
  Img,
} from "@react-email/components";
import * as React from "react";

interface PlanReadyForClientEmailProps {
  coachName: string;
  coachHeadshotUrl?: string | null;
  clientFirstName: string;
  packUrl: string;
  customMessage?: string;
}

export function PlanReadyForClientEmail({
  coachName,
  coachHeadshotUrl,
  clientFirstName,
  packUrl,
  customMessage,
}: PlanReadyForClientEmailProps) {
  return (
    <Html lang="en">
      <Head />
      <Preview>{coachName} has put together a plan for you.</Preview>
      <Body style={bodyStyle}>
        <Container style={containerStyle}>
          {coachHeadshotUrl ? (
            <Img
              src={coachHeadshotUrl}
              alt={coachName}
              width={64}
              height={64}
              style={headshotStyle}
            />
          ) : null}

          <Heading style={h1Style}>
            {clientFirstName}, your plan is ready.
          </Heading>

          <Text style={textStyle}>
            {customMessage?.trim() ||
              `Hi ${clientFirstName} — I've put together a 7-day plan for you. Open it on your phone, it's designed for that.`}
          </Text>

          <Text style={textStyle}>
            <Link href={packUrl} style={ctaButtonStyle}>
              Open your plan
            </Link>
          </Text>

          <Text style={textStyle}>
            You&apos;ll see Today, This Week, Why (the science), and how to
            reach me.
          </Text>

          <Hr style={hrStyle} />

          <Text style={mutedStyle}>
            From {coachName}. This link is just for you — it&apos;s tied to
            your plan and shouldn&apos;t be shared.
          </Text>
        </Container>
      </Body>
    </Html>
  );
}

export default PlanReadyForClientEmail;

// ── Inline styles ──

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

const headshotStyle: React.CSSProperties = {
  borderRadius: "32px",
  marginBottom: "20px",
  border: "1px solid rgba(255,255,255,0.1)",
};

const h1Style: React.CSSProperties = {
  color: "#ffffff",
  fontSize: "24px",
  fontWeight: 300,
  lineHeight: 1.3,
  margin: "0 0 20px",
};

const textStyle: React.CSSProperties = {
  color: "#a1a1aa",
  fontSize: "15px",
  lineHeight: 1.6,
  margin: "0 0 18px",
};

const ctaButtonStyle: React.CSSProperties = {
  display: "inline-block",
  color: "#ecfdf5",
  backgroundColor: "rgba(16,185,129,0.2)",
  border: "1px solid rgba(52,211,153,0.4)",
  borderRadius: "12px",
  padding: "12px 24px",
  fontSize: "15px",
  fontWeight: 600,
  textDecoration: "none",
};

const hrStyle: React.CSSProperties = {
  borderColor: "rgba(255,255,255,0.08)",
  margin: "28px 0 18px",
};

const mutedStyle: React.CSSProperties = {
  color: "#52525b",
  fontSize: "12px",
  lineHeight: 1.55,
  margin: "0 0 10px",
};
