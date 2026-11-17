import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://demo-citas.buestro.com",
  // never inline the bundled scripts: the Content-Security-Policy (vercel.json) allows only script-src 'self'
  vite: { build: { assetsInlineLimit: 0 } },
});
