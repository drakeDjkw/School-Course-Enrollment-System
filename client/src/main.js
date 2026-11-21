import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";
import axios from "axios";
import Cookies from "js-cookie";

import App from "./App.vue";
import router from "./router";
import { useUserStore } from "./stores/user";

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);
app.use(router);

// Django требует CSRF-токен для POST/PUT/PATCH/DELETE.
// Берём его из cookie перед каждым запросом: после входа Django выдаёт новый токен.
axios.interceptors.request.use((config) => {
  const token = Cookies.get("csrftoken");
  if (token) {
    config.headers["X-CSRFToken"] = token;
  }
  return config;
});

function formatError(error) {
  const data = error.response?.data;
  if (!data || typeof data === "string") {
    return error.response ? `Server error ${error.response.status}` : error.message;
  }
  if (data.detail) {
    return data.detail;
  }
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${[].concat(messages).join(" ")}`)
    .join("\n");
}

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url ?? "";
    if ((status === 401 || status === 403) && !url.startsWith("/api/users/")) {
      // сессия закончилась — отправляем на страницу входа
      useUserStore(pinia).setInfo({ is_authenticated: false });
      router.push({ name: "login" });
    } else if (!error.config?.skipErrorAlert) {
      alert(formatError(error));
    }
    return Promise.reject(error);
  },
);

app.mount("#app");
