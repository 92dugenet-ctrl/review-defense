import { MuseShell } from "@/components/public/muse/MuseShell";
import { ContactHero } from "@/components/public/muse/contact/ContactHero";
import { ContactLinks } from "@/components/public/muse/contact/ContactLinks";
import { ContactNext } from "@/components/public/muse/contact/ContactNext";

export function ContactPage() {
  return (
    <MuseShell>
      <ContactHero />
      <ContactLinks />
      <ContactNext />
    </MuseShell>
  );
}
