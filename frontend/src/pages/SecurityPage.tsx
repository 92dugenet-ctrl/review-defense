import { MuseShell } from "@/components/public/muse/MuseShell";
import { SecurityControls } from "@/components/public/muse/security/SecurityControls";
import { SecurityFaq } from "@/components/public/muse/security/SecurityFaq";
import { SecurityHero } from "@/components/public/muse/security/SecurityHero";
import { SecurityNext } from "@/components/public/muse/security/SecurityNext";
import { SecurityResponsibility } from "@/components/public/muse/security/SecurityResponsibility";

export function SecurityPage() {
  return (
    <MuseShell>
      <SecurityHero />
      <SecurityControls />
      <SecurityResponsibility />
      <SecurityFaq />
      <SecurityNext />
    </MuseShell>
  );
}
