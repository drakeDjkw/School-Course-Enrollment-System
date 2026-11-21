<script setup>
import { ref } from "vue";
import axios from "axios";
import { useOptions, useResource } from "@/composables/useResource";
import { useUserStore } from "@/stores/user";
import { toFormData } from "@/utils/formData";
import StatsPanel from "@/components/StatsPanel.vue";
import TableToolbar from "@/components/TableToolbar.vue";

const user = useUserStore();
const {
  items: courses, stats, loading, filters, create, update, remove, exportUrl, resetFilters,
} = useResource("/api/courses/", {
  code: "",
  title: "",
  credits: "",
  max_students: "",
  department: "",
  teacher: "",
});
const { options: departments } = useOptions("/api/departments/");
const { options: teachers } = useOptions("/api/teachers/");

// --- добавление ---
const emptyCourse = () => ({
  code: "",
  title: "",
  credits: 3,
  max_students: 30,
  department_id: "",
  teacher_id: null,
});
const courseToAdd = ref(emptyCourse());

async function onCourseAdd() {
  await create({ ...courseToAdd.value });
  courseToAdd.value = emptyCourse();
}

// --- редактирование ---
const courseToEdit = ref({});

function onCourseEditClick(course) {
  courseToEdit.value = {
    id: course.id,
    code: course.code,
    title: course.title,
    credits: course.credits,
    max_students: course.max_students,
    department_id: course.department.id,
    teacher_id: course.teacher?.id ?? null,
  };
}

async function onUpdateCourse() {
  const { id, ...data } = courseToEdit.value;
  await update(id, data);
}

async function onRemoveClick(course) {
  if (!confirm(`Delete course ${course.code}? Its enrollments and photos will be deleted too.`)) return;
  await remove(course.id);
}

// --- фотоальбом курса ---
const albumCourse = ref(null);
const photos = ref([]);
const currentPhoto = ref(null);
const albumFilesRef = ref();
const albumCaption = ref("");
const uploading = ref(false);

async function fetchPhotos() {
  const r = await axios.get("/api/course-photos/", { params: { course: albumCourse.value.id } });
  photos.value = r.data;
  if (!photos.value.some((p) => p.id === currentPhoto.value?.id)) {
    currentPhoto.value = photos.value[0] ?? null;
  }
}

async function onAlbumClick(course) {
  albumCourse.value = course;
  photos.value = [];
  currentPhoto.value = null;
  await fetchPhotos();
}

async function onPhotosUpload() {
  const files = [...albumFilesRef.value.files];
  if (!files.length) return;
  uploading.value = true;
  try {
    // одна фотография — один POST; можно выбрать сразу несколько файлов
    for (const file of files) {
      await axios.post(
        "/api/course-photos/",
        toFormData({ course: albumCourse.value.id, caption: albumCaption.value }, { image: file }),
      );
    }
  } finally {
    uploading.value = false;
    albumFilesRef.value.value = "";
    albumCaption.value = "";
  }
  await fetchPhotos();
}

async function onPhotoRemove(photo) {
  if (!confirm("Delete this photo?")) return;
  await axios.delete(`/api/course-photos/${photo.id}/`);
  await fetchPhotos();
}

function showPhoto(step) {
  const index = photos.value.findIndex((p) => p.id === currentPhoto.value?.id);
  const next = (index + step + photos.value.length) % photos.value.length;
  currentPhoto.value = photos.value[next];
}
</script>

<template>
  <div class="row g-4">
    <div class="col-xl-9">
      <h2 class="mb-3">Courses</h2>

      <form class="card card-body shadow-sm mb-3" @submit.prevent.stop="onCourseAdd">
        <div class="row g-2 align-items-center">
          <div class="col-md-1">
            <div class="form-floating">
              <input v-model="courseToAdd.code" type="text" class="form-control" placeholder="Code" required />
              <label>Code</label>
            </div>
          </div>
          <div class="col-md-3">
            <div class="form-floating">
              <input v-model="courseToAdd.title" type="text" class="form-control" placeholder="Title" required />
              <label>Title</label>
            </div>
          </div>
          <div class="col-md-1">
            <div class="form-floating">
              <input v-model.number="courseToAdd.credits" type="number" min="1" class="form-control" placeholder="Credits" />
              <label>Credits</label>
            </div>
          </div>
          <div class="col-md-1">
            <div class="form-floating">
              <input v-model.number="courseToAdd.max_students" type="number" min="1" class="form-control" placeholder="Seats" />
              <label>Seats</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <select v-model="courseToAdd.department_id" class="form-select" required>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
              <label>Department</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <select v-model="courseToAdd.teacher_id" class="form-select">
                <option :value="null">— no teacher —</option>
                <option v-for="t in teachers" :key="t.id" :value="t.id">{{ t.last_name }} {{ t.first_name }}</option>
              </select>
              <label>Teacher</label>
            </div>
          </div>
          <div class="col-auto">
            <button class="btn btn-primary"><i class="bi bi-plus-lg"></i> Add</button>
          </div>
        </div>
      </form>

      <TableToolbar
        v-model:owner="filters.user"
        :count="courses.length"
        :loading="loading"
        :export-url="exportUrl"
        @reset="resetFilters"
      />

      <div class="card shadow-sm table-scroll">
        <table class="table table-hover align-middle mb-0 data-table">
          <thead class="table-light">
            <tr>
              <th>Code</th>
              <th>Title</th>
              <th>Credits</th>
              <th>Seats</th>
              <th>Department</th>
              <th>Teacher</th>
              <th v-if="user.isSuperuser">Owner</th>
              <th></th>
            </tr>
            <tr class="filters">
              <th><input v-model="filters.code" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.title" class="form-control form-control-sm" placeholder="Filter…" /></th>
              <th><input v-model="filters.credits" type="number" class="form-control form-control-sm" placeholder="=" /></th>
              <th><input v-model="filters.max_students" type="number" class="form-control form-control-sm" placeholder="=" /></th>
              <th>
                <select v-model="filters.department" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </th>
              <th>
                <select v-model="filters.teacher" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="t in teachers" :key="t.id" :value="t.id">{{ t.last_name }} {{ t.first_name }}</option>
                </select>
              </th>
              <th v-if="user.isSuperuser"></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in courses" :key="item.id">
              <td><span class="badge text-bg-primary">{{ item.code }}</span></td>
              <td>{{ item.title }}</td>
              <td>{{ item.credits }}</td>
              <td>{{ item.max_students }}</td>
              <td>{{ item.department.name }}</td>
              <td>
                <template v-if="item.teacher">{{ item.teacher.last_name }} {{ item.teacher.first_name }}</template>
                <span v-else class="text-muted">—</span>
              </td>
              <td v-if="user.isSuperuser"><span class="badge text-bg-light">{{ item.user ?? "—" }}</span></td>
              <td class="actions">
                <button
                  class="btn btn-sm btn-outline-primary me-1"
                  title="Photo album"
                  data-bs-toggle="modal"
                  data-bs-target="#albumModal"
                  @click="onAlbumClick(item)"
                >
                  <i class="bi bi-images"></i>
                </button>
                <button
                  class="btn btn-sm btn-success me-1"
                  data-bs-toggle="modal"
                  data-bs-target="#editCourseModal"
                  @click="onCourseEditClick(item)"
                >
                  <i class="bi bi-pen-fill"></i>
                </button>
                <button class="btn btn-sm btn-danger" @click="onRemoveClick(item)">
                  <i class="bi bi-x-lg"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!courses.length && !loading">
              <td colspan="8" class="text-center text-muted py-4">No courses</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="col-xl-3">
      <StatsPanel :stats="stats" />
    </div>
  </div>

  <div id="editCourseModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Edit course</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row g-2">
            <div class="col-4">
              <div class="form-floating">
                <input v-model="courseToEdit.code" type="text" class="form-control" placeholder="Code" />
                <label>Code</label>
              </div>
            </div>
            <div class="col-8">
              <div class="form-floating">
                <input v-model="courseToEdit.title" type="text" class="form-control" placeholder="Title" />
                <label>Title</label>
              </div>
            </div>
            <div class="col-6">
              <div class="form-floating">
                <input v-model.number="courseToEdit.credits" type="number" min="1" class="form-control" placeholder="Credits" />
                <label>Credits</label>
              </div>
            </div>
            <div class="col-6">
              <div class="form-floating">
                <input v-model.number="courseToEdit.max_students" type="number" min="1" class="form-control" placeholder="Seats" />
                <label>Seats</label>
              </div>
            </div>
            <div class="col-12">
              <div class="form-floating">
                <select v-model="courseToEdit.department_id" class="form-select">
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
                <label>Department</label>
              </div>
            </div>
            <div class="col-12">
              <div class="form-floating">
                <select v-model="courseToEdit.teacher_id" class="form-select">
                  <option :value="null">— no teacher —</option>
                  <option v-for="t in teachers" :key="t.id" :value="t.id">{{ t.last_name }} {{ t.first_name }}</option>
                </select>
                <label>Teacher</label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateCourse">Save</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Фотоальбом курса -->
  <div id="albumModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-xl modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">
            <i class="bi bi-images"></i>
            Photo album<template v-if="albumCourse">: {{ albumCourse.code }} — {{ albumCourse.title }}</template>
          </h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form class="row g-2 align-items-center mb-3" @submit.prevent.stop="onPhotosUpload">
            <div class="col-md-5">
              <input ref="albumFilesRef" type="file" accept="image/*" multiple class="form-control" required />
            </div>
            <div class="col-md-4">
              <input v-model="albumCaption" type="text" class="form-control" placeholder="Caption (optional)" />
            </div>
            <div class="col-auto">
              <button class="btn btn-primary" :disabled="uploading">
                <span v-if="uploading" class="spinner-border spinner-border-sm"></span>
                <i v-else class="bi bi-upload"></i> Upload
              </button>
            </div>
          </form>

          <div v-if="!photos.length" class="text-center text-muted py-5">
            <i class="bi bi-image fs-1"></i>
            <div>No photos yet</div>
          </div>

          <template v-else>
            <!-- крупный просмотр выбранной фотографии -->
            <div v-if="currentPhoto" class="text-center mb-3 position-relative">
              <img :src="currentPhoto.image" class="img-fluid album-main" :alt="currentPhoto.caption" />
              <div class="mt-2 d-flex justify-content-center align-items-center gap-2">
                <button class="btn btn-sm btn-outline-secondary" @click="showPhoto(-1)">
                  <i class="bi bi-chevron-left"></i>
                </button>
                <span class="text-muted">{{ currentPhoto.caption || "Untitled" }}</span>
                <button class="btn btn-sm btn-outline-secondary" @click="showPhoto(1)">
                  <i class="bi bi-chevron-right"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger ms-3" @click="onPhotoRemove(currentPhoto)">
                  <i class="bi bi-trash"></i> Delete
                </button>
              </div>
            </div>

            <div class="row g-2">
              <div v-for="photo in photos" :key="photo.id" class="col-3 col-md-2">
                <img
                  :src="photo.image"
                  class="album-thumb"
                  :class="{ selected: photo.id === currentPhoto?.id }"
                  :alt="photo.caption"
                  @click="currentPhoto = photo"
                />
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
