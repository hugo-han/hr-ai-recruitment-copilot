import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 后端 API 代理，本地开发避免跨域
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
