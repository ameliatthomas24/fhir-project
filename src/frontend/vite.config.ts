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
      "/patients": {
        // Change 'localhost' to the service name in your docker-compose
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
    },
  },
});

