# School Course Enrollment System

Coursework: a Django + Django REST Framework backend with a Vue 3 front end for enrolling students in school courses.

## Data model

| Model | Fields | Foreign keys |
|---|---|---|
| Department (Кафедра) | name, description | user |
| Teacher (Преподаватель) | first_name, last_name, email, **photo** | department → Department, user |
| Course (Курс) | code, title, credits, max_students | department → Department, teacher → Teacher, user |
| CoursePhoto (Фото курса) | **image**, caption, uploaded_at | course → Course, user |
| Student (Студент) | first_name, last_name, email, birth_date, year_of_study, **picture** | user |
| Enrollment (Запись на курс) | enrolled_on, status, grade | student → Student, course → Course, user |

- Enrollment links students and courses (many-to-many). A student can enroll in a course only once.
- CoursePhoto is the photo album: one course can have many photos.
- Every record has an owner (`user`). It is filled in automatically when the record is created.

## Access rules

- Without logging in, the API is closed.
- An ordinary user sees and edits only their own records.
- A superuser sees everyone's records and can filter by owner (`?user=<id>`).

## Run the backend

```bash
pip install -r requirements.txt
python manage.py makemigrations school
python manage.py migrate
python manage.py createsuperuser
python manage.py generate_data          # 1000+ random records, owned by the first superuser
python manage.py runserver
```

`generate_data` options: `--user <login>` (owner), `--students 1000`, `--courses 1000`, `--teachers 200`, `--departments 20`, `--enrollments 3000`, `--clear` (delete all existing data first).

Run the tests with `python -m pytest`.

## Run the front end

Needs Node.js 20.19+ or 22+.

```bash
cd client
npm install
npm run dev
```

Open http://localhost:5173. Vite forwards `/api`, `/admin`, `/static` and `/media` to Django on port 8000, so both servers must be running.

## API

Every model endpoint supports list, create, retrieve, update (PUT/PATCH) and delete, plus:

| Extra endpoint | What it does |
|---|---|
| `GET /api/<model>/stats/` | Aggregate statistics (Count, Avg, Min, Max, Sum), respecting the filters |
| `GET /api/<model>/export/?type=xlsx` | Download the table as Excel, respecting the filters |
| `GET /api/<model>/export/?type=docx` | Download the table as Word, respecting the filters |

Models: `departments`, `teachers`, `courses`, `course-photos`, `students`, `enrollments`.

Column filters are query parameters, for example:

```
/api/students/?last_name=иван&year_of_study=2
/api/teachers/?department=3
/api/enrollments/?status=completed&grade=5
/api/course-photos/?course=12
```

Users and login:

| Endpoint | What it does |
|---|---|
| `GET /api/users/info/` | Who is logged in (also sets the `csrftoken` cookie) |
| `POST /api/users/login/` | Log in with `username` and `password` |
| `POST /api/users/logout/` | Log out |
| `GET /api/users/` | List of users (superuser only), used for the owner filter |

When writing, related objects are sent by id with the `_id` suffix:

```json
POST /api/enrollments/
{"student_id": 2, "course_id": 1, "status": "active"}
```

Images are sent as `multipart/form-data` (fields `photo` for teachers, `picture` for students, `image` for course photos).

## Front end structure

| File | Purpose |
|---|---|
| `src/router/index.js` | One route per model, plus `/login`; redirects to login when not authenticated |
| `src/stores/user.js` | Pinia store with the current user |
| `src/views/*View.vue` | One component per model with add form, filters, edit modal, delete, stats, export |
| `src/composables/useResource.js` | Shared CRUD, filter, stats and export logic |
| `src/components/` | Statistics panel, table toolbar (owner filter, Excel/Word buttons), image modal |
