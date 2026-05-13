// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - tanstackStart, viteReact, tailwindcss, tsConfigPaths, cloudflare (build-only),
//     componentTagger (dev-only), VITE_* env injection, @ path alias, React/TanStack dedupe,
//     error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... } }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

// Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
// @cloudflare/vite-plugin builds from this — wrangler.jsonc main alone is insufficient.
//
// Proxy /api/* to the TrustScan FastAPI backend during `vite dev`, so the
// React app and the Python API can run on different ports with no CORS pain.
// Override the target with TRUSTSCAN_API_URL at dev time if needed.
const API_TARGET = process.env.TRUSTSCAN_API_URL || "http://localhost:8000";

export default defineConfig({
  tanstackStart: {
    server: { entry: "server" },
  },
  vite: {
    server: {
      proxy: {
        "/api": {
          target: API_TARGET,
          changeOrigin: true,
        },
      },
    },
  },
});
