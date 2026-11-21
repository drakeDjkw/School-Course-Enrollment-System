import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 127.0.0.1, а не localhost: runserver слушает только IPv4,
// а Node может сначала пробовать IPv6 (::1)
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    // все эти запросы Vite пересылает на Django
    proxy: {
      "/api": backend,
      "/admin": backend, // вход в админку прямо с фронтенда
      "/static": backend, // стили и скрипты админки
      "/media": backend, // загруженные картинки
    },
  },
});
