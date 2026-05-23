import Link from "next/link";
import { type Persona } from "@/lib/data/personas";
import { BrandMark } from "./brand-mark";
import { NavTabs } from "./nav-tabs";
import { PersonaSwitcher } from "./persona-switcher";

interface Props {
  persona: Persona;
  section: string;
}

export function Header({ persona, section }: Props) {
  return (
    <header className="fixed left-0 top-0 z-40 w-full border-b border-white/[0.06] bg-[#09090b]/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link
          href={`/clients/${persona.slug}/overview`}
          className="flex items-center gap-2.5 text-white"
        >
          <span className="grid h-6 w-6 place-items-center rounded bg-white text-[#09090b]">
            <BrandMark size={14} />
          </span>
          <span className="text-[0.7rem] font-semibold uppercase tracking-[0.2em]">
            Aura Clinic
          </span>
          <span className="hidden text-[0.65rem] font-medium uppercase tracking-[0.18em] text-zinc-500 md:inline">
            · HCC Compiler
          </span>
        </Link>

        <NavTabs personaSlug={persona.slug} />

        <PersonaSwitcher active={persona} section={section} />
      </div>
    </header>
  );
}
