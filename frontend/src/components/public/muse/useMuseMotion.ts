import { useEffect } from "react";

export function useMuseMotion() {
  useEffect(() => {
    const header = document.querySelector<HTMLElement>("#header");
    const progress = document.querySelector<HTMLElement>(".progress i");
    const scenes = Array.from(document.querySelectorAll<HTMLElement>(".scene"));
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const supportsIntersectionObserver = "IntersectionObserver" in window;

    let revealObserver: IntersectionObserver | undefined;
    let sceneObserver: IntersectionObserver | undefined;

    if (!prefersReducedMotion && supportsIntersectionObserver) {
      const revealTargets = Array.from(
        document.querySelectorAll<HTMLElement>(
          ".scene h1, .scene h2, .scene p, .scene .eyebrow, .product-card, .papers article, .chat-window, .phone, .social-main, .responsibility-image, .principles > div, .reveal",
        ),
      );

      revealTargets.forEach((element, index) => {
        element.classList.add("reveal");
        element.style.transitionDelay = `${Math.min((index % 5) * 70, 280)}ms`;
      });

      revealObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              revealObserver?.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.14 },
      );

      revealTargets.forEach((element) => revealObserver?.observe(element));

      sceneObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const scene = entry.target as HTMLElement;
              scene.classList.add("active");
              scene.style.setProperty("--scene-progress", "1");
              sceneObserver?.unobserve(scene);
            }
          });
        },
        { threshold: 0.45 },
      );

      scenes.forEach((scene) => sceneObserver?.observe(scene));
    } else {
      scenes.forEach((scene) => scene.classList.add("active"));
      document
        .querySelectorAll<HTMLElement>(".reveal")
        .forEach((element) => element.classList.add("is-visible"));
    }

    const updateScrollState = () => {
      const scrollY = window.scrollY;
      const scrollableHeight =
        document.documentElement.scrollHeight - window.innerHeight;

      header?.classList.toggle("scrolled", scrollY > 30);

      if (progress) {
        const percentage =
          scrollableHeight > 0 ? (scrollY / scrollableHeight) * 100 : 0;
        progress.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
      }

      if (!prefersReducedMotion) {
        scenes.forEach((scene) => {
          const bounds = scene.getBoundingClientRect();
          const visibility = Math.max(
            0,
            Math.min(
              1,
              (window.innerHeight - bounds.top) /
                (window.innerHeight + bounds.height),
            ),
          );

          if (scene.classList.contains("active")) {
            scene.style.setProperty("--p", visibility.toFixed(3));
          }
        });
      }
    };

    window.addEventListener("scroll", updateScrollState, { passive: true });
    window.addEventListener("resize", updateScrollState);
    updateScrollState();

    return () => {
      revealObserver?.disconnect();
      sceneObserver?.disconnect();
      window.removeEventListener("scroll", updateScrollState);
      window.removeEventListener("resize", updateScrollState);
      document
        .querySelectorAll<HTMLElement>(".reveal")
        .forEach((element) => {
          element.style.removeProperty("transition-delay");
          element.classList.remove("reveal", "is-visible");
        });
      document
        .querySelectorAll<HTMLElement>(".scene")
        .forEach((scene) => scene.style.removeProperty("--p"));
    };
  }, []);
}
