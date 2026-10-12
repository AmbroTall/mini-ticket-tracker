import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, /api/* is proxied to the Django server with the prefix stripped,
// mirroring what nginx does in the production image. No CORS configuration is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.API_URL || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
