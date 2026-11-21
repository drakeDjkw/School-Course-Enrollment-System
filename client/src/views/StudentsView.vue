<script setup>
import { ref } from "vue";
import { useResource } from "@/composables/useResource";
import { useUserStore } from "@/stores/user";
import { toFormData } from "@/utils/formData";
import ImageModal from "@/components/ImageModal.vue";
import StatsPanel from "@/components/StatsPanel.vue";
import TableToolbar from "@/components/TableToolbar.vue";

const user = useUserStore();
const {
  items: students, stats, loading, filters, create, update, remove, exportUrl, resetFilters,
} = useResource("/api/students/", {
  last_name: "",
  first_name: "",
  email: "",
  birth_year: "",
  year_of_study: "",
});

// --- добавление ---
const emptyStudent = () => ({ first_name: "", last_name: "", email: "", birth_date: "", year_of_study: 1 });
const studentToAdd = ref(emptyStudent());
const studentsPictureRef = ref(); // <input type="file"> формы добавления
const addPicturePreview = ref("");

function onAddPictureChange() {
  const file = studentsPictureRef.value.files[0];
  addPicturePreview.value = file ? URL.createObjectURL(file) : "";
}

async function onStudentAdd() {
  await create(toFormData(studentToAdd.value, { picture: studentsPictureRef.value.files[0] }));
  studentToAdd.value = emptyStudent();
  studentsPictureRef.value.value = "";
  addPicturePreview.value = "";
}

// --- редактирование ---
const studentToEdit = ref({});
const editPictureRef = ref();
const editPicturePreview = ref("");

function onStudentEditClick(student) {
  studentToEdit.value = {
    id: student.id,
    first_name: student.first_name,
    last_name: student.last_name,
    email: student.email,
    birth_date: student.birth_date ?? "",
    year_of_study: student.year_of_study,
  };
  editPicturePreview.value = student.picture ?? "";
  editPictureRef.value.value = "";
}

function onEditPictureChange() {
  const file = editPictureRef.value.files[0];
  if (file) editPicturePreview.value = URL.createObjectURL(file);
}

async function onUpdateStudent() {
  const { id, ...data } = studentToEdit.value;
  await update(id, toFormData(data, { picture: editPictureRef.value.files[0] }));
}

async function onRemoveClick(student) {
  if (!confirm(`Delete student ${student.last_name} ${student.first_name}?`)) return;
  await remove(student.id);
}

// --- просмотр фото ---
const pictureToShow = ref({ src: "", title: "" });
function onPictureClick(student) {
  pictureToShow.value = { src: student.picture, title: `${student.last_name} ${student.first_name}` };
}
</script>

<template>
  <div class="row g-4">
    <div class="col-xl-9">
      <h2 class="mb-3">Students</h2>

      <form class="card card-body shadow-sm mb-3" @submit.prevent.stop="onStudentAdd">
        <div class="row g-2 align-items-center">
          <div class="col-md-2">
            <div class="form-floating">
              <input v-model="studentToAdd.last_name" type="text" class="form-control" placeholder="Last name" required />
              <label>Last name</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <input v-model="studentToAdd.first_name" type="text" class="form-control" placeholder="First name" required />
              <label>First name</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <input v-model="studentToAdd.email" type="email" class="form-control" placeholder="E-mail" required />
              <label>E-mail</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <input v-model="studentToAdd.birth_date" type="date" class="form-control" placeholder="Birth date" />
              <label>Birth date</label>
            </div>
          </div>
          <div class="col-md-1">
            <div class="form-floating">
              <input v-model.number="studentToAdd.year_of_study" type="number" min="1" max="6" class="form-control" placeholder="Year" />
              <label>Year</label>
            </div>
          </div>
          <div class="col-md-2">
            <input ref="studentsPictureRef" type="file" accept="image/*" class="form-control" @change="onAddPictureChange" />
          </div>
          <div v-if="addPicturePreview" class="col-auto">
            <img :src="addPicturePreview" class="thumb" alt="preview" />
          </div>
          <div class="col-auto">
            <button class="btn btn-primary"><i class="bi bi-plus-lg"></i> Add</button>
          </div>
        </div>
      </form>

      <TableToolbar
        v-model:owner="filters.user"
        :count="students.length"
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
              <th>Birth date</th>
              <th>Year</th>
              <th v-if="user.isSuperuser">Owner</th>
              <th></th>
            </tr>
            <tr class="filters">
              <th></th>
              <th><input v-model="filters.last_name" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.first_name" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.email" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.birth_year" type="number" class="form-control form-control-sm" placeholder="Year…" /></th>
              <th>
                <select v-model="filters.year_of_study" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="y in 6" :key="y" :value="y">{{ y }}</option>
                </select>
              </th>
              <th v-if="user.isSuperuser"></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in students" :key="item.id">
              <td>
                <img
                  v-if="item.picture"
                  :src="item.picture"
                  class="thumb"
                  alt="photo"
                  data-bs-toggle="modal"
                  data-bs-target="#studentPictureModal"
                  @click="onPictureClick(item)"
                />
                <span v-else class="thumb-placeholder"><i class="bi bi-person"></i></span>
              </td>
              <td>{{ item.last_name }}</td>
              <td>{{ item.first_name }}</td>
              <td>{{ item.email }}</td>
              <td>{{ item.birth_date ?? "—" }}</td>
              <td>{{ item.year_of_study }}</td>
              <td v-if="user.isSuperuser"><span class="badge text-bg-light">{{ item.user ?? "—" }}</span></td>
              <td class="actions">
                <button
                  class="btn btn-sm btn-success me-1"
                  data-bs-toggle="modal"
                  data-bs-target="#editStudentModal"
                  @click="onStudentEditClick(item)"
                >
                  <i class="bi bi-pen-fill"></i>
                </button>
                <button class="btn btn-sm btn-danger" @click="onRemoveClick(item)">
                  <i class="bi bi-x-lg"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!students.length && !loading">
              <td colspan="8" class="text-center text-muted py-4">No students</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="col-xl-3">
      <StatsPanel :stats="stats" />
    </div>
  </div>

  <div id="editStudentModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Edit student</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row g-2">
            <div class="col-6">
              <div class="form-floating">
                <input v-model="studentToEdit.last_name" type="text" class="form-control" placeholder="Last name" />
                <label>Last name</label>
              </div>
            </div>
            <div class="col-6">
              <div class="form-floating">
                <input v-model="studentToEdit.first_name" type="text" class="form-control" placeholder="First name" />
                <label>First name</label>
              </div>
            </div>
            <div class="col-12">
              <div class="form-floating">
                <input v-model="studentToEdit.email" type="email" class="form-control" placeholder="E-mail" />
                <label>E-mail</label>
              </div>
            </div>
            <div class="col-8">
              <div class="form-floating">
                <input v-model="studentToEdit.birth_date" type="date" class="form-control" placeholder="Birth date" />
                <label>Birth date</label>
              </div>
            </div>
            <div class="col-4">
              <div class="form-floating">
                <input v-model.number="studentToEdit.year_of_study" type="number" min="1" max="6" class="form-control" placeholder="Year" />
                <label>Year</label>
              </div>
            </div>
            <div class="col-12">
              <label class="form-label">Photo (choose a file to replace it)</label>
              <input ref="editPictureRef" type="file" accept="image/*" class="form-control" @change="onEditPictureChange" />
            </div>
            <div v-if="editPicturePreview" class="col-12 text-center">
              <img :src="editPicturePreview" class="preview-img" alt="preview" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateStudent">Save</button>
        </div>
      </div>
    </div>
  </div>

  <ImageModal id="studentPictureModal" :src="pictureToShow.src" :title="pictureToShow.title" />
</template>
