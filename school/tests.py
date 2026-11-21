import shutil
import tempfile
from io import BytesIO, StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from model_bakery import baker
from PIL import Image
from rest_framework.test import APIClient, APITestCase

from .models import Course, CoursePhoto, Department, Enrollment, Student, Teacher

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()  # картинки из тестов не попадают в настоящую папку media


def make_image(name="photo.png"):
    buffer = BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def stat_value(stats, label):
    return next(s["value"] for s in stats if s["label"] == label)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class BaseAPITestCase(APITestCase):
    """Все запросы в тестах идут от залогиненного обычного пользователя."""

    def setUp(self):
        self.user = baker.make(User)
        self.client.force_authenticate(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


class DepartmentsViewsetTestCase(BaseAPITestCase):
    def test_get_list(self):
        departments = baker.make(Department, user=self.user, _quantity=3)

        r = self.client.get("/api/departments/")
        data = r.json()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 3)
        for department in departments:
            item = next(d for d in data if d["id"] == department.id)
            self.assertEqual(item["name"], department.name)
            self.assertEqual(item["user"], self.user.username)

    def test_create(self):
        r = self.client.post(
            "/api/departments/", {"name": "Физика", "description": "Общая физика"}
        )
        self.assertEqual(r.status_code, 201)

        department = Department.objects.get(id=r.json()["id"])
        self.assertEqual(department.name, "Физика")
        self.assertEqual(department.description, "Общая физика")
        # владелец подставился автоматически
        self.assertEqual(department.user, self.user)

    def test_delete(self):
        departments = baker.make(Department, user=self.user, _quantity=10)
        r = self.client.get("/api/departments/")
        self.assertEqual(len(r.json()), 10)

        department_id_to_delete = departments[3].id
        r = self.client.delete(f"/api/departments/{department_id_to_delete}/")
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/departments/")
        self.assertEqual(len(r.json()), 9)
        self.assertNotIn(department_id_to_delete, [d["id"] for d in r.json()])

    def test_update(self):
        department = baker.make(Department, user=self.user)

        r = self.client.put(
            f"/api/departments/{department.id}/",
            {"name": "Новая кафедра", "description": "Новое описание"},
        )
        self.assertEqual(r.status_code, 200)

        department.refresh_from_db()
        self.assertEqual(department.name, "Новая кафедра")
        self.assertEqual(department.description, "Новое описание")

    def test_filter_by_name(self):
        baker.make(Department, user=self.user, name="Математика")
        baker.make(Department, user=self.user, name="Физика")

        r = self.client.get("/api/departments/", {"name": "мат"})
        self.assertEqual([d["name"] for d in r.json()], ["Математика"])

    def test_stats(self):
        department = baker.make(Department, user=self.user)
        baker.make(Course, department=department, user=self.user, _quantity=4)
        baker.make(Department, user=self.user)

        r = self.client.get("/api/departments/stats/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(stat_value(r.json(), "Departments"), 2)
        self.assertEqual(stat_value(r.json(), "Avg courses per department"), 2)
        self.assertEqual(stat_value(r.json(), "Most courses in one department"), 4)


class TeachersViewsetTestCase(BaseAPITestCase):
    def test_get_list(self):
        teachers = baker.make(Teacher, user=self.user, _quantity=3)

        r = self.client.get("/api/teachers/")
        data = r.json()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 3)
        for teacher in teachers:
            item = next(t for t in data if t["id"] == teacher.id)
            self.assertEqual(item["last_name"], teacher.last_name)
            self.assertEqual(item["email"], teacher.email)
            # кафедра приходит вложенным объектом
            self.assertEqual(item["department"]["id"], teacher.department.id)
            self.assertEqual(item["department"]["name"], teacher.department.name)

    def test_create(self):
        department = baker.make(Department)

        r = self.client.post(
            "/api/teachers/",
            {
                "first_name": "Анна",
                "last_name": "Петрова",
                "email": "petrova@test.example",
                "department_id": department.id,
            },
        )
        self.assertEqual(r.status_code, 201)

        teacher = Teacher.objects.get(id=r.json()["id"])
        self.assertEqual(teacher.last_name, "Петрова")
        self.assertEqual(teacher.department, department)
        self.assertEqual(r.json()["department"]["name"], department.name)

    def test_create_with_photo(self):
        department = baker.make(Department)

        r = self.client.post(
            "/api/teachers/",
            {
                "first_name": "Игорь",
                "last_name": "Смирнов",
                "email": "smirnov@test.example",
                "department_id": department.id,
                "photo": make_image(),
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)

        teacher = Teacher.objects.get(id=r.json()["id"])
        self.assertTrue(teacher.photo.name.startswith("teachers/"))
        self.assertIn("/media/teachers/", r.json()["photo"])

    def test_delete(self):
        teachers = baker.make(Teacher, user=self.user, _quantity=10)
        r = self.client.get("/api/teachers/")
        self.assertEqual(len(r.json()), 10)

        teacher_id_to_delete = teachers[3].id
        r = self.client.delete(f"/api/teachers/{teacher_id_to_delete}/")
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/teachers/")
        self.assertEqual(len(r.json()), 9)
        self.assertNotIn(teacher_id_to_delete, [t["id"] for t in r.json()])

    def test_update(self):
        teacher = baker.make(Teacher, user=self.user)
        new_department = baker.make(Department)

        r = self.client.patch(
            f"/api/teachers/{teacher.id}/",
            {"last_name": "Иванов", "department_id": new_department.id},
        )
        self.assertEqual(r.status_code, 200)

        teacher.refresh_from_db()
        self.assertEqual(teacher.last_name, "Иванов")
        self.assertEqual(teacher.department, new_department)

    def test_update_photo(self):
        teacher = baker.make(Teacher, user=self.user)

        r = self.client.patch(
            f"/api/teachers/{teacher.id}/", {"photo": make_image("new.png")}, format="multipart"
        )
        self.assertEqual(r.status_code, 200)

        teacher.refresh_from_db()
        self.assertTrue(teacher.photo)

    def test_filter_by_department(self):
        department = baker.make(Department)
        baker.make(Teacher, user=self.user, department=department, _quantity=2)
        baker.make(Teacher, user=self.user, _quantity=3)

        r = self.client.get("/api/teachers/", {"department": department.id})
        self.assertEqual(len(r.json()), 2)

    def test_bad_filter_value_returns_empty_list(self):
        baker.make(Teacher, user=self.user)

        r = self.client.get("/api/teachers/", {"department": "abc"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])


class CoursesViewsetTestCase(BaseAPITestCase):
    def test_get_list(self):
        teacher = baker.make(Teacher)
        courses = baker.make(Course, teacher=teacher, user=self.user, _quantity=3)

        r = self.client.get("/api/courses/")
        data = r.json()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 3)
        for course in courses:
            item = next(c for c in data if c["id"] == course.id)
            self.assertEqual(item["code"], course.code)
            self.assertEqual(item["title"], course.title)
            self.assertEqual(item["department"]["id"], course.department.id)
            self.assertEqual(item["teacher"]["id"], teacher.id)

    def test_create(self):
        department = baker.make(Department)
        teacher = baker.make(Teacher, department=department)

        r = self.client.post(
            "/api/courses/",
            {
                "code": "CS101",
                "title": "Основы Python",
                "credits": 4,
                "max_students": 25,
                "department_id": department.id,
                "teacher_id": teacher.id,
            },
        )
        self.assertEqual(r.status_code, 201)

        course = Course.objects.get(id=r.json()["id"])
        self.assertEqual(course.code, "CS101")
        self.assertEqual(course.department, department)
        self.assertEqual(course.teacher, teacher)

    def test_create_without_teacher(self):
        department = baker.make(Department)

        r = self.client.post(
            "/api/courses/",
            {"code": "MA101", "title": "Линейная алгебра", "department_id": department.id},
        )
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(r.json()["teacher"])

    def test_delete(self):
        courses = baker.make(Course, user=self.user, _quantity=10)
        r = self.client.get("/api/courses/")
        self.assertEqual(len(r.json()), 10)

        course_id_to_delete = courses[3].id
        r = self.client.delete(f"/api/courses/{course_id_to_delete}/")
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/courses/")
        self.assertEqual(len(r.json()), 9)
        self.assertNotIn(course_id_to_delete, [c["id"] for c in r.json()])

    def test_update(self):
        course = baker.make(Course, user=self.user)
        new_teacher = baker.make(Teacher)

        r = self.client.patch(
            f"/api/courses/{course.id}/",
            {"title": "Новое название", "credits": 6, "teacher_id": new_teacher.id},
        )
        self.assertEqual(r.status_code, 200)

        course.refresh_from_db()
        self.assertEqual(course.title, "Новое название")
        self.assertEqual(course.credits, 6)
        self.assertEqual(course.teacher, new_teacher)

    def test_stats(self):
        baker.make(Course, user=self.user, credits=2, max_students=10)
        baker.make(Course, user=self.user, credits=6, max_students=20)

        r = self.client.get("/api/courses/stats/")
        self.assertEqual(stat_value(r.json(), "Courses"), 2)
        self.assertEqual(stat_value(r.json(), "Avg credits"), 4)
        self.assertEqual(stat_value(r.json(), "Total seats"), 30)


class CoursePhotosViewsetTestCase(BaseAPITestCase):
    def test_album_upload_list_and_delete(self):
        course = baker.make(Course, user=self.user)
        other_course = baker.make(Course, user=self.user)

        for name in ["a.png", "b.png"]:
            r = self.client.post(
                "/api/course-photos/",
                {"course": course.id, "caption": name, "image": make_image(name)},
                format="multipart",
            )
            self.assertEqual(r.status_code, 201)
        baker.make(CoursePhoto, course=other_course, user=self.user, image="courses/x.png")

        # альбом конкретного курса
        r = self.client.get("/api/course-photos/", {"course": course.id})
        self.assertEqual(len(r.json()), 2)

        photo_id = r.json()[0]["id"]
        r = self.client.delete(f"/api/course-photos/{photo_id}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(CoursePhoto.objects.filter(course=course).count(), 1)


class StudentsViewsetTestCase(BaseAPITestCase):
    def test_get_list(self):
        students = baker.make(Student, user=self.user, _quantity=3)

        r = self.client.get("/api/students/")
        data = r.json()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 3)
        for student in students:
            item = next(s for s in data if s["id"] == student.id)
            self.assertEqual(item["first_name"], student.first_name)
            self.assertEqual(item["last_name"], student.last_name)
            self.assertEqual(item["email"], student.email)

    def test_create(self):
        r = self.client.post(
            "/api/students/",
            {
                "first_name": "Мария",
                "last_name": "Иванова",
                "email": "ivanova@test.example",
                "birth_date": "2005-03-14",
                "year_of_study": 2,
            },
        )
        self.assertEqual(r.status_code, 201)

        student = Student.objects.get(id=r.json()["id"])
        self.assertEqual(student.last_name, "Иванова")
        self.assertEqual(str(student.birth_date), "2005-03-14")
        self.assertEqual(student.year_of_study, 2)

    def test_create_with_picture(self):
        r = self.client.post(
            "/api/students/",
            {
                "first_name": "Пётр",
                "last_name": "Сидоров",
                "email": "sidorov@test.example",
                "birth_date": "",  # пустая дата из формы -> null
                "picture": make_image(),
            },
            format="multipart",
        )
        self.assertEqual(r.status_code, 201)

        student = Student.objects.get(id=r.json()["id"])
        self.assertIsNone(student.birth_date)
        self.assertTrue(student.picture.name.startswith("students/"))

    def test_delete(self):
        students = baker.make(Student, user=self.user, _quantity=10)
        r = self.client.get("/api/students/")
        self.assertEqual(len(r.json()), 10)

        student_id_to_delete = students[3].id
        r = self.client.delete(f"/api/students/{student_id_to_delete}/")
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/students/")
        self.assertEqual(len(r.json()), 9)
        self.assertNotIn(student_id_to_delete, [s["id"] for s in r.json()])

    def test_update(self):
        student = baker.make(Student, user=self.user)

        r = self.client.put(
            f"/api/students/{student.id}/",
            {
                "first_name": "Дмитрий",
                "last_name": "Кузнецов",
                "email": "kuznetsov@test.example",
                "birth_date": "2004-11-02",
                "year_of_study": 3,
            },
        )
        self.assertEqual(r.status_code, 200)

        student.refresh_from_db()
        self.assertEqual(student.first_name, "Дмитрий")
        self.assertEqual(student.email, "kuznetsov@test.example")
        self.assertEqual(student.year_of_study, 3)

    def test_filters(self):
        baker.make(Student, user=self.user, last_name="Иванов", year_of_study=1)
        baker.make(Student, user=self.user, last_name="Иванова", year_of_study=2)
        baker.make(Student, user=self.user, last_name="Петров", year_of_study=2)

        r = self.client.get("/api/students/", {"last_name": "иван"})
        self.assertEqual(len(r.json()), 2)

        r = self.client.get("/api/students/", {"last_name": "иван", "year_of_study": 2})
        self.assertEqual([s["last_name"] for s in r.json()], ["Иванова"])

    def test_stats_respect_filters(self):
        baker.make(Student, user=self.user, year_of_study=1, _quantity=2)
        baker.make(Student, user=self.user, year_of_study=5, _quantity=2)

        r = self.client.get("/api/students/stats/")
        self.assertEqual(stat_value(r.json(), "Students"), 4)
        self.assertEqual(stat_value(r.json(), "Avg year of study"), 3)

        r = self.client.get("/api/students/stats/", {"year_of_study": 5})
        self.assertEqual(stat_value(r.json(), "Students"), 2)

    def test_export_excel_and_word(self):
        baker.make(Student, user=self.user, _quantity=3)

        r = self.client.get("/api/students/export/", {"type": "xlsx"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("spreadsheetml", r["Content-Type"])
        self.assertIn("students.xlsx", r["Content-Disposition"])
        self.assertTrue(r.content.startswith(b"PK"))  # xlsx и docx — это zip-архивы

        r = self.client.get("/api/students/export/", {"type": "docx"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("wordprocessingml", r["Content-Type"])
        self.assertTrue(r.content.startswith(b"PK"))


class EnrollmentsViewsetTestCase(BaseAPITestCase):
    def test_get_list(self):
        enrollments = baker.make(Enrollment, user=self.user, _quantity=3)

        r = self.client.get("/api/enrollments/")
        data = r.json()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(data), 3)
        for enrollment in enrollments:
            item = next(e for e in data if e["id"] == enrollment.id)
            self.assertEqual(item["student"]["id"], enrollment.student.id)
            self.assertEqual(item["course"]["id"], enrollment.course.id)
            self.assertEqual(item["status"], enrollment.status)

    def test_create(self):
        student = baker.make(Student)
        course = baker.make(Course)

        r = self.client.post(
            "/api/enrollments/", {"student_id": student.id, "course_id": course.id}
        )
        self.assertEqual(r.status_code, 201)

        enrollment = Enrollment.objects.get(id=r.json()["id"])
        self.assertEqual(enrollment.student, student)
        self.assertEqual(enrollment.course, course)
        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)

    def test_create_duplicate_is_rejected(self):
        enrollment = baker.make(Enrollment, user=self.user)

        r = self.client.post(
            "/api/enrollments/",
            {"student_id": enrollment.student.id, "course_id": enrollment.course.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_delete(self):
        enrollments = baker.make(Enrollment, user=self.user, _quantity=10)
        r = self.client.get("/api/enrollments/")
        self.assertEqual(len(r.json()), 10)

        enrollment_id_to_delete = enrollments[3].id
        r = self.client.delete(f"/api/enrollments/{enrollment_id_to_delete}/")
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/enrollments/")
        self.assertEqual(len(r.json()), 9)
        self.assertNotIn(enrollment_id_to_delete, [e["id"] for e in r.json()])

    def test_update(self):
        enrollment = baker.make(Enrollment, user=self.user, status=Enrollment.Status.ACTIVE)

        r = self.client.patch(
            f"/api/enrollments/{enrollment.id}/", {"status": "completed", "grade": 5}
        )
        self.assertEqual(r.status_code, 200)

        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.COMPLETED)
        self.assertEqual(enrollment.grade, 5)

    def test_stats(self):
        baker.make(Enrollment, user=self.user, status="completed", grade=4)
        baker.make(Enrollment, user=self.user, status="completed", grade=5)
        baker.make(Enrollment, user=self.user, status="active")

        r = self.client.get("/api/enrollments/stats/")
        self.assertEqual(stat_value(r.json(), "Enrollments"), 3)
        self.assertEqual(stat_value(r.json(), "Completed"), 2)
        self.assertEqual(stat_value(r.json(), "Avg grade"), 4.5)


class OwnershipTestCase(BaseAPITestCase):
    def test_anonymous_has_no_access(self):
        r = APIClient().get("/api/students/")
        self.assertIn(r.status_code, (401, 403))

    def test_user_sees_only_own_data(self):
        baker.make(Student, user=self.user, _quantity=2)
        other_student = baker.make(Student, user=baker.make(User))

        r = self.client.get("/api/students/")
        self.assertEqual(len(r.json()), 2)

        # чужую запись нельзя ни открыть, ни удалить
        self.assertEqual(self.client.get(f"/api/students/{other_student.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/students/{other_student.id}/").status_code, 404)

    def test_superuser_sees_all_and_can_filter_by_user(self):
        other = baker.make(User)
        baker.make(Student, user=self.user, _quantity=2)
        baker.make(Student, user=other, _quantity=3)

        admin = baker.make(User, is_superuser=True)
        self.client.force_authenticate(admin)

        r = self.client.get("/api/students/")
        self.assertEqual(len(r.json()), 5)

        r = self.client.get("/api/students/", {"user": other.id})
        self.assertEqual(len(r.json()), 3)

    def test_users_list_only_for_superuser(self):
        self.assertEqual(self.client.get("/api/users/").status_code, 403)

        self.client.force_authenticate(baker.make(User, is_superuser=True))
        r = self.client.get("/api/users/")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()), 2)


class AuthTestCase(APITestCase):
    def test_login_info_logout(self):
        User.objects.create_user("anna", password="secret-pass-123")
        client = APIClient()

        r = client.get("/api/users/info/")
        self.assertFalse(r.json()["is_authenticated"])
        self.assertIn("csrftoken", r.cookies)

        r = client.post("/api/users/login/", {"username": "anna", "password": "wrong"})
        self.assertEqual(r.status_code, 400)

        r = client.post("/api/users/login/", {"username": "anna", "password": "secret-pass-123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["username"], "anna")

        r = client.get("/api/users/info/")
        self.assertTrue(r.json()["is_authenticated"])
        self.assertEqual(client.get("/api/students/").status_code, 200)

        client.post("/api/users/logout/")
        r = client.get("/api/users/info/")
        self.assertFalse(r.json()["is_authenticated"])


class GenerateDataCommandTestCase(APITestCase):
    def test_generates_records_for_user(self):
        user = baker.make(User)

        call_command(
            "generate_data",
            user=user.username,
            departments=2,
            teachers=3,
            courses=5,
            students=4,
            enrollments=6,
            stdout=StringIO(),
        )

        self.assertEqual(Department.objects.filter(user=user).count(), 2)
        self.assertEqual(Teacher.objects.filter(user=user).count(), 3)
        self.assertEqual(Course.objects.filter(user=user).count(), 5)
        self.assertEqual(Student.objects.filter(user=user).count(), 4)
        self.assertEqual(Enrollment.objects.filter(user=user).count(), 6)
