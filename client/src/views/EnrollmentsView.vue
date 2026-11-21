<script setup>
import { ref } from "vue";
import { useOptions, useResource } from "@/composables/useResource";
import { useUserStore } from "@/stores/user";
import StatsPanel from "@/components/StatsPanel.vue";
import TableToolbar from "@/components/TableToolbar.vue";

const user = useUserStore();
const {
  items: enrollments, stats, loading, filters, create, update, remove, exportUrl, resetFilters,
} = useResource("/api/enrollments/", {
  student: "",
  course: "",
  status: "",
  grade: "",
  enrolled_on: "",
});
const { options: students } = useOptions("/api/students/");
const { options: courses } = useOptions("/api/courses/");

const statuses = [
  { value: "active", title: "Active", badge: "text-bg-primary" },
  { value: "completed", title: "Completed", badge: "text-bg-success" },
  { value: "dropped", title: "Dropped", badge: "text-bg-secondary" },
];
const statusById = Object.fromEntries(statuses.map((s) => [s.value, s]));

// --- добавление ---
const emptyEnrollment = () => ({ student_id: "", course_id: "", status: "active", grade: null });
const enrollmentToAdd = ref(emptyEnrollment());

async function onEnrollmentAdd() {
  await create({ ...enrollmentToAdd.value });
  enrollmentToAdd.value = emptyEnrollment();
}

// --- редактирование ---
const enrollmentToEdit = ref({});

function onEnrollmentEditClick(enrollment) {
  enrollmentToEdit.value = {
    id: enrollment.id,
    student_id: enrollment.student.id,
    course_id: enrollment.course.id,
    status: enrollment.status,
    grade: enrollment.grade,
  };
}

async function onUpdateEnrollment() {
  const { id, ...data } = enrollmentToEdit.value;
  if (data.grade === "") data.grade = null;
  await update(id, data);
}

async function onRemoveClick(enrollment) {
  if (!confirm(`Remove ${enrollment.student.last_name} from ${enrollment.course.code}?`)) return;
  await remove(enrollment.id);
}
</script>

<template>
  <div class="row g-4">
    <div class="col-xl-9">
      <h2 class="mb-3">Enrollments</h2>

      <form class="card card-body shadow-sm mb-3" @submit.prevent.stop="onEnrollmentAdd">
        <div class="row g-2 align-items-center">
          <div class="col-md-4">
            <div class="form-floating">
              <select v-model="enrollmentToAdd.student_id" class="form-select" required>
                <option v-for="s in students" :key="s.id" :value="s.id">{{ s.last_name }} {{ s.first_name }}</option>
              </select>
              <label>Student</label>
            </div>
          </div>
          <div class="col-md-4">
            <div class="form-floating">
              <select v-model="enrollmentToAdd.course_id" class="form-select" required>
                <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} — {{ c.title }}</option>
              </select>
              <label>Course</label>
            </div>
          </div>
          <div class="col-md-2">
            <div class="form-floating">
              <select v-model="enrollmentToAdd.status" class="form-select">
                <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.title }}</option>
              </select>
              <label>Status</label>
            </div>
          </div>
          <div class="col-auto">
            <button class="btn btn-primary"><i class="bi bi-plus-lg"></i> Enroll</button>
          </div>
        </div>
      </form>

      <TableToolbar
        v-model:owner="filters.user"
        :count="enrollments.length"
        :loading="loading"
        :export-url="exportUrl"
        @reset="resetFilters"
      />

      <div class="card shadow-sm table-scroll">
        <table class="table table-hover align-middle mb-0 data-table">
          <thead class="table-light">
            <tr>
              <th>Student</th>
              <th>Course</th>
              <th>Status</th>
              <th>Grade</th>
              <th>Enrolled on</th>
              <th v-if="user.isSuperuser">Owner</th>
              <th></th>
            </tr>
            <tr class="filters">
              <th><input v-model="filters.student" class="form-control form-control-sm" placeholder="Last name…" /></th>
              <th>
                <select v-model="filters.course" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} — {{ c.title }}</option>
                </select>
              </th>
              <th>
                <select v-model="filters.status" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.title }}</option>
                </select>
              </th>
              <th>
                <select v-model="filters.grade" class="form-select form-select-sm">
                  <option value="">All</option>
                  <option v-for="g in [2, 3, 4, 5]" :key="g" :value="g">{{ g }}</option>
                </select>
              </th>
              <th><input v-model="filters.enrolled_on" type="date" class="form-control form-control-sm" /></th>
              <th v-if="user.isSuperuser"></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in enrollments" :key="item.id">
              <td>{{ item.student.last_name }} {{ item.student.first_name }}</td>
              <td><span class="badge text-bg-light">{{ item.course.code }}</span> {{ item.course.title }}</td>
              <td>
                <span class="badge" :class="statusById[item.status]?.badge">{{ statusById[item.status]?.title }}</span>
              </td>
              <td>{{ item.grade ?? "—" }}</td>
              <td>{{ item.enrolled_on }}</td>
              <td v-if="user.isSuperuser"><span class="badge text-bg-light">{{ item.user ?? "—" }}</span></td>
              <td class="actions">
                <button
                  class="btn btn-sm btn-success me-1"
                  data-bs-toggle="modal"
                  data-bs-target="#editEnrollmentModal"
                  @click="onEnrollmentEditClick(item)"
                >
                  <i class="bi bi-pen-fill"></i>
                </button>
                <button class="btn btn-sm btn-danger" @click="onRemoveClick(item)">
                  <i class="bi bi-x-lg"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!enrollments.length && !loading">
              <td colspan="7" class="text-center text-muted py-4">No enrollments</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="col-xl-3">
      <StatsPanel :stats="stats" />
    </div>
  </div>

  <div id="editEnrollmentModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Edit enrollment</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row g-2">
            <div class="col-12">
              <div class="form-floating">
                <select v-model="enrollmentToEdit.student_id" class="form-select">
                  <option v-for="s in students" :key="s.id" :value="s.id">{{ s.last_name }} {{ s.first_name }}</option>
                </select>
                <label>Student</label>
              </div>
            </div>
            <div class="col-12">
              <div class="form-floating">
                <select v-model="enrollmentToEdit.course_id" class="form-select">
                  <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} — {{ c.title }}</option>
                </select>
                <label>Course</label>
              </div>
            </div>
            <div class="col-8">
              <div class="form-floating">
                <select v-model="enrollmentToEdit.status" class="form-select">
                  <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.title }}</option>
                </select>
                <label>Status</label>
              </div>
            </div>
            <div class="col-4">
              <div class="form-floating">
                <select v-model="enrollmentToEdit.grade" class="form-select">
                  <option :value="null">—</option>
                  <option v-for="g in [2, 3, 4, 5]" :key="g" :value="g">{{ g }}</option>
                </select>
                <label>Grade</label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateEnrollment">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
