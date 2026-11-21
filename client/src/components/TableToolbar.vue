<script setup>
import { useUserStore } from "@/stores/user";

// v-model — фильтр по владельцу (виден только суперпользователю)
const owner = defineModel("owner");

defineProps({
  count: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  exportUrl: { type: Function, required: true },
});
defineEmits(["reset"]);

const user = useUserStore();
</script>

<template>
  <div class="d-flex flex-wrap gap-2 align-items-center mb-2">
    <select v-if="user.isSuperuser" v-model="owner" class="form-select form-select-sm w-auto">
      <option value="">All users</option>
      <option v-for="u in user.users" :key="u.id" :value="u.id">{{ u.username }}</option>
    </select>
    <button class="btn btn-sm btn-outline-secondary" @click="$emit('reset')">
      <i class="bi bi-funnel"></i> Clear filters
    </button>
    <div class="btn-group btn-group-sm">
      <!-- файл собирает Django, браузер просто скачивает его по ссылке -->
      <a class="btn btn-outline-success" :href="exportUrl('xlsx')">
        <i class="bi bi-file-earmark-excel"></i> Excel
      </a>
      <a class="btn btn-outline-primary" :href="exportUrl('docx')">
        <i class="bi bi-file-earmark-word"></i> Word
      </a>
    </div>
    <span v-if="loading" class="spinner-border spinner-border-sm text-secondary"></span>
    <span class="text-muted ms-auto small">{{ count }} records</span>
  </div>
</template>
