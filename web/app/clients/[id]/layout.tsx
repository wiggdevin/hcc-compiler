import { notFound } from "next/navigation";
import { getPersona } from "@/lib/data/personas";
import { Header } from "@/components/header";

interface Props {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}

export default async function ClientShellLayout({ children, params }: Props) {
  const { id } = await params;
  const persona = getPersona(id);
  if (!persona) notFound();

  // The "section" key is used by the persona switcher to keep the user on
  // the same view when switching personas. We can't access pathname in a
  // Server Component, so we default to "overview" — the client switcher
  // will refine via usePathname downstream if needed.
  const section = "overview";

  return (
    <>
      <Header persona={persona} section={section} />
      <main className="relative z-10 pt-16">{children}</main>
    </>
  );
}
