import { MuseShell } from "@/components/public/muse/MuseShell";
import { MethodHero } from "@/components/public/muse/method/MethodHero";
import { MethodLogic } from "@/components/public/muse/method/MethodLogic";
import { MethodNext } from "@/components/public/muse/method/MethodNext";
import { MethodSteps } from "@/components/public/muse/method/MethodSteps";

export function MethodPage() {
  return (
    <MuseShell>
      <MethodHero />
      <MethodSteps />
      <MethodLogic />
      <MethodNext />
    </MuseShell>
  );
}
