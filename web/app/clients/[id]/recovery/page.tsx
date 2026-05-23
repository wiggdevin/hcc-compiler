import { notFound } from "next/navigation";
import { getPersona } from "@/lib/data/personas";
import { loadEvidencePack } from "@/lib/data/loader";
import { DOMAIN_META } from "@/lib/data/domains";
import { SectionHeader } from "@/components/section-header";
import { DomainSection } from "@/components/domain-section";

export default async function RecoveryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!getPersona(id)) notFound();
  const pack = await loadEvidencePack(id);
  const recovery = pack.domain_recommendations.recovery;
  const supplements = pack.domain_recommendations.supplements;
  const behavioral = pack.domain_recommendations.behavioral;

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow="Prescribed plan"
        title="Recovery / Adjuncts"
        subtitle="Recovery prescriptions, supplement stack, and behavioral programming — three adjacent domains kept on one surface for daily-protocol scanning."
      />
      <div className="flex flex-col gap-16">
        <DomainSection
          icon={DOMAIN_META.recovery.icon}
          label="Recovery"
          block={recovery}
          id="recovery"
        />
        <DomainSection
          icon={DOMAIN_META.supplements.icon}
          label="Supplements"
          block={supplements}
          id="supplements"
        />
        <DomainSection
          icon={DOMAIN_META.behavioral.icon}
          label="Behavioral"
          block={behavioral}
          id="behavioral"
        />
      </div>
    </div>
  );
}
