import { redirect } from "next/navigation";
import { DEFAULT_PERSONA_SLUG } from "@/lib/data/personas";

export default function RootPage(): never {
  redirect(`/clients/${DEFAULT_PERSONA_SLUG}/overview`);
}
