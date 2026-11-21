import { createRouter, createWebHistory } from "vue-router";

import { useUserStore } from "@/stores/user";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  linkActiveClass: "active",
  routes: [
    { path: "/", redirect: "/students" },
    { path: "/login", name: "login", component: () => import("@/views/LoginView.vue") },
    { path: "/departments", name: "departments", component: () => import("@/views/DepartmentsView.vue") },
    { path: "/teachers", name: "teachers", component: () => import("@/views/TeachersView.vue") },
    { path: "/courses", name: "courses", component: () => import("@/views/CoursesView.vue") },
    { path: "/students", name: "students", component: () => import("@/views/StudentsView.vue") },
    { path: "/enrollments", name: "enrollments", component: () => import("@/views/EnrollmentsView.vue") },
  ],
});

// без входа пускаем только на страницу логина
router.beforeEach(async (to) => {
  const user = useUserStore();
  if (!user.loaded) {
    await user.fetchInfo();
  }
  if (to.name !== "login" && !user.isAuthenticated) {
    return { name: "login" };
  }
  if (to.name === "login" && user.isAuthenticated) {
    return { path: "/" };
  }
});

export default router;
