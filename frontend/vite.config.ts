// Configuration du serveur de développement et du build frontend Vite.
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // Les ressources compilées de cette application React sont servies sous /react/.
  base: "/react/",

  // Active la transformation JSX/React pendant le développement et le build.
  plugins: [react()],

  resolve: {
    alias: {
      // Permet d'importer depuis src avec @/..., sans chemins relatifs répétitifs.
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },

  server: {
    // Port Vite local ; ce n'est pas le port Gunicorn de production (8080).
    port: 5173,
    strictPort: true,
  },

  build: {
    // Conserve les source maps pour relier les fichiers compilés aux sources.
    sourcemap: true,

    rollupOptions: {
      // Deux entrées HTML coexistent : l'entrée historique et le shell React.
      // Ne pas les fusionner sans modifier aussi le routage et le déploiement.
      input: {
        legacy: fileURLToPath(new URL("./index.html", import.meta.url)),
        react: fileURLToPath(new URL("./react.html", import.meta.url)),
      },
    },
  },
});
