import { HomeChat } from "./HomeChat";
import { HomeFaq } from "./HomeFaq";
import { HomeHero } from "./HomeHero";
import { HomeProducts } from "./HomeProducts";
import { HomeResearch } from "./HomeResearch";
import { HomeResearchDetail } from "./HomeResearchDetail";
import { HomeResponsibility } from "./HomeResponsibility";
import { HomeSocial } from "./HomeSocial";
import { HomeTry } from "./HomeTry";
import { HomeWorkspace } from "./HomeWorkspace";

export function HomeBlocks() {
  return (
    <>
      <HomeHero />
      <HomeWorkspace />
      <HomeFaq />
      <HomeProducts />
      <HomeResearch />
      <HomeResearchDetail />
      <HomeChat />
      <HomeTry />
      <HomeSocial />
      <HomeResponsibility />
    </>
  );
}
