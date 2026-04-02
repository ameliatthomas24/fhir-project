import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/patients": "http://localhost:8000",
      "/observations": "http://localhost:8000",
      "/medications": "http://localhost:8000",
    },
  },
});
