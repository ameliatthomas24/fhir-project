import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    allowedHosts: [
      'healthybean.me',
      'www.healthybean.me'
    ],
    proxy: {
      "/auth": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/patients": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/observations": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/medications": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/predict": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/recommendations": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/chat": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/conditions": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/notes": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/appointments": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
      "/messages": {
        target: "http://hapi-backend:8000",
        changeOrigin: true,
      },
    },
  },
});