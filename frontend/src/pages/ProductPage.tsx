import { MuseShell } from "@/components/public/muse/MuseShell";
import { ProductHero } from "@/components/public/muse/product/ProductHero";
import { ProductMoments } from "@/components/public/muse/product/ProductMoments";
import { ProductNext } from "@/components/public/muse/product/ProductNext";
import { ProductWorkspace } from "@/components/public/muse/product/ProductWorkspace";

export function ProductPage() {
  return (
    <MuseShell>
      <ProductHero />
      <ProductMoments />
      <ProductWorkspace />
      <ProductNext />
    </MuseShell>
  );
}
