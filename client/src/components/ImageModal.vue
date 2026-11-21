<script setup>
// Модальное окно для просмотра картинки крупно
defineProps({
  id: { type: String, required: true },
  src: { type: String, default: "" },
  title: { type: String, default: "" },
});
</script>

<template>
  <div :id="id" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-lg modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ title }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body text-center">
          <img v-if="src" :src="src" :alt="title" class="img-fluid rounded" />
        </div>
      </div>
    </div>
  </div>
</template>
