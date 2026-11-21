<script setup>
defineProps({
  stats: { type: Array, default: () => [] },
});

function show(value) {
  return value === null || value === undefined ? "—" : value;
}
</script>

<template>
  <div class="card shadow-sm">
    <div class="card-header"><i class="bi bi-bar-chart-line"></i> Statistics</div>
    <ul class="list-group list-group-flush">
      <li
        v-for="item in stats"
        :key="item.label"
        class="list-group-item d-flex justify-content-between align-items-center"
      >
        <span>{{ item.label }}</span>
        <strong>{{ show(item.value) }}</strong>
      </li>
    </ul>
    <div class="card-footer text-muted small">Statistics follow the table filters</div>
  </div>
</template>
