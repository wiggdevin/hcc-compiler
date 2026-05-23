import { notFound } from "next/navigation";
import { getPersona } from "@/lib/data/personas";
import { loadEvidencePack } from "@/lib/data/loader";
import { DOMAIN_META } from "@/lib/data/domains";
import { SectionHeader } from "@/components/section-header";
import { DomainSection } from "@/components/domain-section";

export default async function DietPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!getPersona(id)) notFound();
  const pack = await loadEvidencePack(id);
  const block = pack.domain_recommendations.nutrition;
  const meta = DOMAIN_META.nutrition;

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow="Prescribed plan"
        title="Diet / Matrix"
        subtitle="Patterns are evidence-graded multi-atom prescriptions. Standalone atoms are individual claims, each retained as a citable unit."
      />
      <DomainSection icon={meta.icon} label="Nutrition" block={block} />
    </div>
  );
}
