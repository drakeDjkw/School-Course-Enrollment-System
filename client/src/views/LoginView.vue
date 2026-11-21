<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const user = useUserStore();
const router = useRouter();

const username = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);

async function onLogin() {
  error.value = "";
  busy.value = true;
  try {
    await user.login(username.value, password.value);
    router.push("/");
  } catch (e) {
    error.value = e.response?.data?.detail ?? "Login failed";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="row justify-content-center mt-5">
    <div class="col-sm-8 col-md-5 col-lg-4">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h1 class="h4 mb-4 text-center">
            <i class="bi bi-mortarboard-fill text-primary"></i> Course Enrollment
          </h1>
          <form @submit.prevent.stop="onLogin">
            <div class="form-floating mb-3">
              <input id="login" v-model="username" type="text" class="form-control" placeholder="Login" required autofocus />
              <label for="login">Login</label>
            </div>
            <div class="form-floating mb-3">
              <input id="password" v-model="password" type="password" class="form-control" placeholder="Password" required />
              <label for="password">Password</label>
            </div>
            <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
            <button class="btn btn-primary w-100" :disabled="busy">
              <span v-if="busy" class="spinner-border spinner-border-sm"></span>
              Log in
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
