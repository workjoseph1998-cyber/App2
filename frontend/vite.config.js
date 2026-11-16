import { defineConfig } from "vite";
import { resolve } from "node:path";
export default defineConfig({
  base: "./",
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: "../cirrus/static/experience",
    emptyOutDir: true,
    assetsInlineLimit: 0,
    rollupOptions: {
      input: resolve(import.meta.dirname, "src/main.jsx"),
      output: {
        entryFileNames: "experience.js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: (asset) =>
          asset.name?.endsWith(".css")
            ? "experience.css"
            : "assets/[name]-[hash][extname]",
      },
      onwarn(warning, warn) {
        if (warning.code !== "MODULE_LEVEL_DIRECTIVE") warn(warning);
      },
    },
    sourcemap: false,
  },
});
