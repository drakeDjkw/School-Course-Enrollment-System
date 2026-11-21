<script setup>
import { ref } from "vue";
import { useOptions, useResource } from "@/composables/useResource";
import { useUserStore } from "@/stores/user";
import { toFormData } from "@/utils/formData";
import ImageModal from "@/components/ImageModal.vue";
import StatsPanel from "@/components/StatsPanel.vue";
import TableToolbar from "@/components/TableToolbar.vue";

const user = useUserStore();
const {
  items: teachers, stats, loading, filters, create, update, remove, exportUrl, resetFilters,
} = useResource("/api/teachers/", { last_name: "", first_name: "", email: "", department: "" });
const { options: departments } = useOptions("/api/departments/");

// --- добавление ---
const emptyTeacher = () => ({ first_name: "", last_name: "", email: "", department_id: "" });
const teacherToAdd = ref(emptyTeacher());
const addPhotoRef = ref(); // <input type="file"> формы добавления
const addPhotoPreview = ref("");

function onAddPhotoChange() {
  const file = addPhotoRef.value.files[0];
  addPhotoPreview.value = file ? URL.createObjectURL(file) : "";
}

async function onTeacherAdd() {
  await create(toFormData(teacherToAdd.value, { photo: addPhotoRef.value.files[0] }));
  teacherToAdd.value = emptyTeacher();
  addPhotoRef.value.value = "";
  addPhotoPreview.value = "";
}

// --- редактирование ---
const teacherToEdit = ref({});
const editPhotoRef = ref();
const editPhotoPreview = ref("");

function onTeacherEditClick(teacher) {
  teacherToEdit.value = {
    id: teacher.id,
    first_name: teacher.first_name,
    last_name: teacher.last_name,
    email: teacher.email,
    department_id: teacher.department.id,
  };
  editPhotoPreview.value = teacher.photo ?? "";
  editPhotoRef.value.value = "";
}

function onEditPhotoChange() {
  const file = editPhotoRef.value.files[0];
  if (file) editPhotoPreview.value = URL.createObjectURL(file);
}

async function onUpdateTeacher() {
  const { id, ...data } = teacherToEdit.value;
  await update(id, toFormData(data, { photo: editPhotoRef.value.files[0] }));
}

async function onRemoveClick(teacher) {
  if (!confirm(`Delete teacher ${teacher.last_name} ${teacher.first_name}?`)) return;
  await remove(teacher.id);
}

// --- просмотр фото ---
const photoToShow = ref({ src: "", title: "" });
function onPhotoClick(teacher) {
  photoToShow.value = { src: teacher.photo, title: `${teacher.last_name} ${teacher.first_name}` };
}
</script>

<template>
  <div class="row g-4">
    <div class="col-xl-9">
      <h2 class="mb-3">Teachers</h2>

      <form class="card card-body shadow-sm mb-3" @submit.prevent.stop="onTeacherAdd">
        <div class="row g-2 align-items-center">
          <div class="col-md-2">
            <div class="form-floating">
              <input v-model="teacherToAdd.last_name" type="text" class="form-control" placeholder="Last name" required />
              <label>Last name</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <input v-model="teacherToAdd.first_name" type="text" class="form-control" placeholder="First name" required />
              <label>First name</label>
            </div>
          </div>
          <div class="col-md-3">
            <div class="form-floating">
              <input v-model="teacherToAdd.email" type="email" class="form-control" placeholder="E-mail" required />
              <label>E-mail</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <select v-model="teacherToAdd.department_id" class="form-select" required>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
              <label>Department</label>
            </div>
          </div>
          <div class="col-md-2">
            <input ref="addPhotoRef" type="file" accept="image/*" class="form-control" @change="onAddPhotoChange" />
          </div>
          <div v-if="addPhotoPreview" class="col-auto">
            <img :src="addPhotoPreview" class="thumb" alt="preview" />
          </div>
          <div class="col-auto">
            <button class="btn btn-primary"><i class="bi bi-plus-lg"></i> Add</button>
          </div>
        </div>
      </form>

      <TableToolbar
        v-model:owner="filters.user"
        :count="teachers.length"
        :loading="loading"
        :export-url="exportUrl"
        @reset="resetFilters"
      />

      <div class="card shadow-sm table-scroll">
        <table class="table table-hover align-middle mb-0 data-table">
          <thead class="table-light">
            <tr>
              <th>Photo</th>
              <th>Last name</th>
              <th>First name</th>
              <th>E-mail</th>
              <th>Department</th>
              <th v-if="user.isSuperuser">Owner</th>
              <th></th>
            </tr>
            <tr class="filters">
              <th></th>
              <th><input v-model="filters.last_name" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.first_name" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.email" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th>
                <select v-model="filters.department" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </th>
              <th v-if="user.isSuperuser"></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in teachers" :key="item.id">
              <td>
                <img
                  v-if="item.photo"
                  :src="item.photo"
                  class="thumb"
                  alt="photo"
                  data-bs-toggle="modal"
                  data-bs-target="#teacherPhotoModal"
                  @click="onPhotoClick(item)"
                />
                <span v-else class="thumb-placeholder"><i class="bi bi-person"></i></span>
              </td>
              <td>{{ item.last_name }}</td>
              <td>{{ item.first_name }}</td>
              <td>{{ item.email }}</td>
              <td>{{ item.department.name }}</td>
              <td v-if="user.isSuperuser"><span class="badge text-bg-light">{{ item.user ?? "—" }}</span></td>
              <td class="actions">
                <button
                  class="btn btn-sm btn-success me-1"
                  data-bs-toggle="modal"
                  data-bs-target="#editTeacherModal"
                  @click="onTeacherEditClick(item)"
                >
                  <i class="bi bi-pen-fill"></i>
                </button>
                <button class="btn btn-sm btn-danger" @click="onRemoveClick(item)">
                  <i class="bi bi-x-lg"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!teachers.length && !loading">
              <td colspan="7" class="text-center text-muted py-4">No teachers</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="col-xl-3">
      <StatsPanel :stats="stats" />
    </div>
  </div>

  <div id="editTeacherModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Edit teacher</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row g-2">
            <div class="col-6">
              <div class="form-floating">
                <input v-model="teacherToEdit.last_name" type="text" class="form-control" placeholder="Last name" />
                <label>Last name</label>
              </div>
            </div>
            <div class="col-6">
              <div class="form-floating">
                <input v-model="teacherToEdit.first_name" type="text" class="form-control" placeholder="First name" />
                <label>First name</label>
              </div>
            </div>
            <div class="col-12">
              <div class="form-floating">
                <input v-model="teacherToEdit.email" type="email" class="form-control" placeholder="E-mail" />
                <label>E-mail</label>
              </div>
            </div>
            <div class="col-12">
              <div class="form-floating">
                <select v-model="teacherToEdit.department_id" class="form-select">
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
                <label>Department</label>
              </div>
            </div>
            <div class="col-12">
              <label class="form-label">Photo (choose a file to replace it)</label>
              <input ref="editPhotoRef" type="file" accept="image/*" class="form-control" @change="onEditPhotoChange" />
            </div>
            <div v-if="editPhotoPreview" class="col-12 text-center">
              <img :src="editPhotoPreview" class="preview-img" alt="preview" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateTeacher">Save</button>
        </div>
      </div>
    </div>
  </div>

  <ImageModal id="teacherPhotoModal" :src="photoToShow.src" :title="photoToShow.title" />
</template>
