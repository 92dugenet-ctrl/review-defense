import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  server: {
    port: 5173,
    strictPort: true
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      input: {
        legacy: fileURLToPath(new URL("./index.html", import.meta.url)),
        react: fileURLToPath(new URL("./src/main.tsx", import.meta.url))
      }
    }
  }
});
