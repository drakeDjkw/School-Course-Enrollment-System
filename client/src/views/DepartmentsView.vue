<script setup>
import { ref } from "vue";
import { useResource } from "@/composables/useResource";
import { useUserStore } from "@/stores/user";
import StatsPanel from "@/components/StatsPanel.vue";
import TableToolbar from "@/components/TableToolbar.vue";

const user = useUserStore();
const {
  items: departments, stats, loading, filters, create, update, remove, exportUrl, resetFilters,
} = useResource("/api/departments/", { name: "", description: "" });

const emptyDepartment = () => ({ name: "", description: "" });
const departmentToAdd = ref(emptyDepartment());
const departmentToEdit = ref({});

async function onDepartmentAdd() {
  await create({ ...departmentToAdd.value });
  departmentToAdd.value = emptyDepartment();
}

function onDepartmentEditClick(department) {
  departmentToEdit.value = {
    id: department.id,
    name: department.name,
    description: department.description,
  };
}

async function onUpdateDepartment() {
  const { id, ...data } = departmentToEdit.value;
  await update(id, data);
}

async function onRemoveClick(department) {
  if (!confirm(`Delete department "${department.name}"?`)) return;
  await remove(department.id);
}
</script>

<template>
  <div class="row g-4">
    <div class="col-xl-9">
      <h2 class="mb-3">Departments</h2>

      <form class="card card-body shadow-sm mb-3" @submit.prevent.stop="onDepartmentAdd">
        <div class="row g-2 align-items-center">
          <div class="col-md-4">
            <div class="form-floating">
              <input v-model="departmentToAdd.name" type="text" class="form-control" placeholder="Name" required />
              <label>Name</label>
            </div>
          </div>
          <div class="col">
            <div class="form-floating">
              <input v-model="departmentToAdd.description" type="text" class="form-control" placeholder="Description" />
              <label>Description</label>
            </div>
          </div>
          <div class="col-auto">
            <button class="btn btn-primary"><i class="bi bi-plus-lg"></i> Add</button>
          </div>
        </div>
      </form>

      <TableToolbar
        v-model:owner="filters.user"
        :count="departments.length"
        :loading="loading"
        :export-url="exportUrl"
        @reset="resetFilters"
      />

      <div class="card shadow-sm table-scroll">
        <table class="table table-hover align-middle mb-0 data-table">
          <thead class="table-light">
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th v-if="user.isSuperuser">Owner</th>
              <th></th>
            </tr>
            <tr class="filters">
              <th><input v-model="filters.name" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.description" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th v-if="user.isSuperuser"></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in departments" :key="item.id">
              <td>{{ item.name }}</td>
              <td class="text-muted">{{ item.description }}</td>
              <td v-if="user.isSuperuser"><span class="badge text-bg-light">{{ item.user ?? "—" }}</span></td>
              <td class="actions">
                <button
                  class="btn btn-sm btn-success me-1"
                  data-bs-toggle="modal"
                  data-bs-target="#editDepartmentModal"
                  @click="onDepartmentEditClick(item)"
                >
                  <i class="bi bi-pen-fill"></i>
                </button>
                <button class="btn btn-sm btn-danger" @click="onRemoveClick(item)">
                  <i class="bi bi-x-lg"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!departments.length && !loading">
              <td colspan="4" class="text-center text-muted py-4">No departments</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="col-xl-3">
      <StatsPanel :stats="stats" />
    </div>
  </div>

  <div id="editDepartmentModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Edit department</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="form-floating mb-2">
            <input v-model="departmentToEdit.name" type="text" class="form-control" placeholder="Name" />
            <label>Name</label>
          </div>
          <div class="form-floating">
            <textarea v-model="departmentToEdit.description" class="form-control" placeholder="Description" style="height: 100px"></textarea>
            <label>Description</label>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateDepartment">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
