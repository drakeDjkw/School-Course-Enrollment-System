import { defineStore } from "pinia";
import axios from "axios";

// Хранилище с информацией о текущем пользователе
export const useUserStore = defineStore("user", {
  state: () => ({
    loaded: false,
    isAuthenticated: false,
    id: null,
    username: "",
    isSuperuser: false,
    isStaff: false,
    users: [], // список всех пользователей (нужен суперпользователю для фильтра)
  }),

  actions: {
    setInfo(data) {
      this.isAuthenticated = data.is_authenticated;
      this.id = data.id ?? null;
      this.username = data.username ?? "";
      this.isSuperuser = Boolean(data.is_superuser);
      this.isStaff = Boolean(data.is_staff);
      this.loaded = true;
      if (!this.isSuperuser) {
        this.users = [];
      }
    },

    async fetchInfo() {
      const r = await axios.get("/api/users/info/");
      this.setInfo(r.data);
      if (this.isSuperuser) {
        await this.fetchUsers();
      }
    },

    async fetchUsers() {
      const r = await axios.get("/api/users/");
      this.users = r.data;
    },

    async login(username, password) {
      const r = await axios.post(
        "/api/users/login/",
        { username, password },
        { skipErrorAlert: true }, // ошибку покажет сама страница входа
      );
      this.setInfo(r.data);
      if (this.isSuperuser) {
        await this.fetchUsers();
      }
    },

    async logout() {
      await axios.post("/api/users/logout/");
      this.setInfo({ is_authenticated: false });
    },
  },
});
