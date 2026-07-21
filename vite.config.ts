import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

function manualChunks(id: string): string | undefined {
  if (!id.includes("node_modules")) return undefined;

  // Keep these in dedicated chunks to avoid a single ~1.4MB vendor bundle.
  if (id.includes("pdfjs-dist")) return "pdf";
  if (id.includes("recharts")) return "charts";
  if (id.includes("@supabase")) return "supabase";
  if (id.includes("@radix-ui")) return "radix";

  // General vendor split by top-level package to improve caching.
  const parts = id.split("node_modules/")[1]?.split("/");
  const pkg = parts?.[0]?.startsWith("@") ? `${parts?.[0]}/${parts?.[1]}` : parts?.[0];
  return pkg ? `vendor-${pkg.replace(/[@/]/g, "-")}` : "vendor";
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
  server: {
    host: "::",
    port: 8080,
    // Proxy API calls to the FastAPI backend so the browser talks to it
    // same-origin (no CORS needed in dev). The server-side spreadsheet parser
    // (POST /api/parse-file) lives there — see backend/api/app.py.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    // Keep the warning as a signal, but vendor splitting should bring chunk sizes down.
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
