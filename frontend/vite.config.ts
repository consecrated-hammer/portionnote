import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const ReactPlugin = react();

const Config = defineConfig(({ mode }) => {
  const LoadedEnv = loadEnv(mode, process.cwd(), "");
  const ProxyTarget = LoadedEnv.VITE_API_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [ReactPlugin],
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target: ProxyTarget,
          changeOrigin: true,
          secure: false
        }
      }
    },
    preview: {
      host: true,
      port: 5173
    }
  };
});

export default Config;
