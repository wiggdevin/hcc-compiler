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

interface PlanReadyEmailProps {
  coachName: string;
  clientName: string;
  packUrl: string;
}

export function PlanReadyEmail({
  coachName,
  clientName,
  packUrl,
}: PlanReadyEmailProps) {
  return (
    <Html lang="en">
      <Head />
      <Preview>
        Your plan for {clientName} is ready — review and export
      </Preview>
      <Body style={bodyStyle}>
        <Container style={containerStyle}>
          <Heading style={h1Style}>
            Your plan for {clientName} is ready
          </Heading>

          <Text style={textStyle}>Hi {coachName},</Text>

          <Text style={textStyle}>
            The evidence pack for <strong>{clientName}</strong> has finished
            compiling. The plan covers all six domains — nutrition, training,
            sleep, supplementation, recovery, and lifestyle — with citations on
            every recommendation.
          </Text>

          <Text style={textStyle}>
            <Link href={packUrl} style={ctaLinkStyle}>
              Open the plan
            </Link>
          </Text>

          <Text style={textStyle}>From the plan viewer you can:</Text>
          <Text style={listItemStyle}>
            — Review domain confidence scores and the atoms behind them
          </Text>
          <Text style={listItemStyle}>
            — Check any safety preflight flags surfaced for this client
          </Text>
          <Text style={listItemStyle}>
            — Export as PDF or Markdown for your notes or for the client
          </Text>

          <Hr style={hrStyle} />

          <Text style={mutedStyle}>
            Plans are evidence references, not prescriptions. Apply professional
            judgment before acting on any recommendation.
          </Text>

          <Text style={mutedStyle}>
            Questions?{" "}
            <Link href="mailto:hello@hccompiler.com" style={linkStyle}>
              hello@hccompiler.com
            </Link>
          </Text>
        </Container>
      </Body>
    </Html>
  );
}

export default PlanReadyEmail;

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
  margin: "0 0 6px 12px",
};

const ctaLinkStyle: React.CSSProperties = {
  color: "#10b981",
  fontSize: "14px",
  fontWeight: 600,
  textDecoration: "underline",
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
