import { MuseShell } from "@/components/public/muse/MuseShell";
import { PricingCatalog } from "@/components/public/muse/pricing/PricingCatalog";
import { PricingHero } from "@/components/public/muse/pricing/PricingHero";
import { PricingNext } from "@/components/public/muse/pricing/PricingNext";

export function PricingPage() {
  return (
    <MuseShell>
      <PricingHero />
      <PricingCatalog />
      <PricingNext />
    </MuseShell>
  );
}
