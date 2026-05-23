import { notFound } from "next/navigation";
import { getPersona } from "@/lib/data/personas";
import { loadEvidencePack } from "@/lib/data/loader";
import { DOMAIN_META } from "@/lib/data/domains";
import { SectionHeader } from "@/components/section-header";
import { DomainSection } from "@/components/domain-section";

export default async function WorkoutPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!getPersona(id)) notFound();
  const pack = await loadEvidencePack(id);
  const training = pack.domain_recommendations.training;
  const conditioning = pack.domain_recommendations.conditioning;

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow="Prescribed plan"
        title="Movement / Protocol"
        subtitle="Resistance training programming and conditioning prescriptions, each backed by retrieval-graded evidence."
      />
      <div className="flex flex-col gap-16">
        <DomainSection
          icon={DOMAIN_META.training.icon}
          label="Training"
          block={training}
          id="training"
        />
        <DomainSection
          icon={DOMAIN_META.conditioning.icon}
          label="Conditioning"
          block={conditioning}
          id="conditioning"
        />
      </div>
    </div>
  );
}
