<script setup>
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const user = useUserStore();
const router = useRouter();

const links = [
  { to: "/departments", title: "Departments", icon: "bi-building" },
  { to: "/teachers", title: "Teachers", icon: "bi-person-badge" },
  { to: "/courses", title: "Courses", icon: "bi-journal-text" },
  { to: "/students", title: "Students", icon: "bi-mortarboard" },
  { to: "/enrollments", title: "Enrollments", icon: "bi-card-checklist" },
];

async function onLogout() {
  await user.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <nav v-if="user.isAuthenticated" class="navbar navbar-expand bg-white border-bottom mb-4">
    <div class="container-fluid px-4 flex-wrap gap-2">
      <span class="navbar-brand"><i class="bi bi-mortarboard-fill text-primary"></i> Course Enrollment</span>
      <ul class="navbar-nav me-auto flex-wrap">
        <li v-for="link in links" :key="link.to" class="nav-item">
          <RouterLink class="nav-link" :to="link.to">
            <i class="bi" :class="link.icon"></i> {{ link.title }}
          </RouterLink>
        </li>
      </ul>
      <span class="navbar-text me-2">
        <i class="bi bi-person-circle"></i> {{ user.username }}
        <span v-if="user.isSuperuser" class="badge text-bg-warning">superuser</span>
      </span>
      <!-- /admin/ проксируется на Django (см. vite.config.js) -->
      <a v-if="user.isStaff" href="/admin/" target="_blank" class="btn btn-outline-secondary btn-sm">
        <i class="bi bi-gear"></i> Admin panel
      </a>
      <button class="btn btn-outline-danger btn-sm" @click="onLogout">
        <i class="bi bi-box-arrow-right"></i> Log out
      </button>
    </div>
  </nav>
  <main class="container-fluid px-4 pb-5">
    <RouterView />
  </main>
</template>
