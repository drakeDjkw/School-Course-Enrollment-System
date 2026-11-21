import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from faker import Faker

from school.models import Course, Department, Enrollment, Student, Teacher

SUBJECTS = [
    "Информатика", "Математика", "Физика", "Химия", "Биология",
    "История", "Литература", "Экономика", "Философия", "Иностранные языки",
    "География", "Психология", "Право", "Социология", "Электроника",
    "Механика", "Робототехника", "Искусственный интеллект", "Статистика", "Дизайн",
]
COURSE_PREFIXES = ["Введение в", "Основы", "Практикум:", "Продвинутый курс:", "Спецкурс:"]
COURSE_TOPICS = [
    "программирование", "алгоритмы", "базы данных", "веб-разработку", "машинное обучение",
    "компьютерное зрение", "дискретную математику", "теорию вероятностей", "сети",
    "операционные системы", "анализ данных", "линейную алгебру", "квантовую физику",
    "органическую химию", "генетику", "микроэкономику", "этику", "робототехнику",
]


def next_id(model):
    """Максимальный id в таблице — новые записи получат id больше него."""
    return model.objects.aggregate(m=Max("id"))["m"] or 0


class Command(BaseCommand):
    help = "Заполняет базу случайными данными (по умолчанию 1000+ записей в основных таблицах)"

    def add_arguments(self, parser):
        parser.add_argument("--user", help="логин владельца записей (по умолчанию первый суперпользователь)")
        parser.add_argument("--departments", type=int, default=20)
        parser.add_argument("--teachers", type=int, default=200)
        parser.add_argument("--courses", type=int, default=1000)
        parser.add_argument("--students", type=int, default=1000)
        parser.add_argument("--enrollments", type=int, default=3000)
        parser.add_argument("--clear", action="store_true", help="удалить старые данные перед генерацией")

    @transaction.atomic
    def handle(self, *args, **options):
        owner = self.get_owner(options["user"])
        fake = Faker(["ru_RU"])

        if options["clear"]:
            # порядок важен: Department и Teacher защищены PROTECT
            Enrollment.objects.all().delete()
            Course.objects.all().delete()
            Teacher.objects.all().delete()
            Student.objects.all().delete()
            Department.objects.all().delete()
            self.stdout.write("Old data deleted")

        # --- кафедры ---
        start = next_id(Department)
        Department.objects.bulk_create(
            Department(
                name=f"{SUBJECTS[i % len(SUBJECTS)]} №{start + i + 1}",
                description=fake.sentence(nb_words=8),
                user=owner,
            )
            for i in range(options["departments"])
        )
        departments = list(Department.objects.filter(id__gt=start))

        # --- преподаватели ---
        start = next_id(Teacher)
        teachers = []
        for i in range(options["teachers"]):
            male = random.random() < 0.5
            teachers.append(
                Teacher(
                    first_name=fake.first_name_male() if male else fake.first_name_female(),
                    last_name=fake.last_name_male() if male else fake.last_name_female(),
                    email=f"{fake.user_name()}.t{start + i + 1}@school.example",
                    department=random.choice(departments),
                    user=owner,
                )
            )
        Teacher.objects.bulk_create(teachers)
        teachers = list(Teacher.objects.filter(id__gt=start))

        # --- курсы ---
        start = next_id(Course)
        courses = []
        for i in range(options["courses"]):
            teacher = random.choice(teachers + [None])  # иногда курс без преподавателя
            department = teacher.department if teacher else random.choice(departments)
            courses.append(
                Course(
                    code=f"C{start + i + 1:05d}",
                    title=f"{random.choice(COURSE_PREFIXES)} {random.choice(COURSE_TOPICS)}",
                    credits=random.randint(1, 8),
                    max_students=random.choice([15, 20, 25, 30, 40, 60]),
                    department=department,
                    teacher=teacher,
                    user=owner,
                )
            )
        Course.objects.bulk_create(courses)
        courses = list(Course.objects.filter(id__gt=start))

        # --- студенты ---
        start = next_id(Student)
        students = []
        for i in range(options["students"]):
            male = random.random() < 0.5
            students.append(
                Student(
                    first_name=fake.first_name_male() if male else fake.first_name_female(),
                    last_name=fake.last_name_male() if male else fake.last_name_female(),
                    email=f"{fake.user_name()}.s{start + i + 1}@student.example",
                    birth_date=fake.date_of_birth(minimum_age=16, maximum_age=25),
                    year_of_study=random.randint(1, 5),
                    user=owner,
                )
            )
        Student.objects.bulk_create(students)
        students = list(Student.objects.filter(id__gt=start))

        # --- записи на курсы (уникальные пары студент + курс) ---
        wanted = min(options["enrollments"], len(students) * len(courses))
        pairs = set()
        while len(pairs) < wanted:
            pairs.add((random.choice(students).id, random.choice(courses).id))

        statuses = [Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED, Enrollment.Status.DROPPED]
        enrollments = []
        for student_id, course_id in pairs:
            status = random.choices(statuses, weights=[6, 3, 1])[0]
            grade = random.randint(2, 5) if status == Enrollment.Status.COMPLETED else None
            enrollments.append(
                Enrollment(student_id=student_id, course_id=course_id, status=status, grade=grade, user=owner)
            )
        Enrollment.objects.bulk_create(enrollments, batch_size=500)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created for user '{owner.username}': {len(departments)} departments, "
                f"{len(teachers)} teachers, {len(courses)} courses, "
                f"{len(students)} students, {len(enrollments)} enrollments"
            )
        )

    def get_owner(self, username):
        User = get_user_model()
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' not found")
        owner = User.objects.filter(is_superuser=True).order_by("id").first()
        if owner is None:
            raise CommandError("No superuser found: run createsuperuser first or pass --user <login>")
        return owner
