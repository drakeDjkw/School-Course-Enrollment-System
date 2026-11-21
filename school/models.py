from django.conf import settings
from django.db import models


def owner_field():
    """Пользователь, создавший запись (у каждой модели свой ForeignKey на User)."""
    return models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )


class Department(models.Model):
    """Кафедра (учебное подразделение), к которой относятся преподаватели и курсы."""

    name = models.CharField("Название", max_length=150, unique=True)
    description = models.TextField("Описание", blank=True)
    user = owner_field()

    class Meta:
        verbose_name = "Кафедра"
        verbose_name_plural = "Кафедры"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Teacher(models.Model):
    """Преподаватель. Связан с кафедрой через ForeignKey."""

    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    email = models.EmailField("E-mail", unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="teachers",
        verbose_name="Кафедра",
    )
    photo = models.ImageField("Фото", upload_to="teachers", null=True, blank=True)
    user = owner_field()

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Course(models.Model):
    """Учебный курс. Связан с кафедрой и с преподавателем."""

    code = models.CharField("Код курса", max_length=20, unique=True)
    title = models.CharField("Название", max_length=200)
    credits = models.PositiveSmallIntegerField("Кредиты", default=3)
    max_students = models.PositiveSmallIntegerField("Макс. число студентов", default=30)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="courses",
        verbose_name="Кафедра",
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name="Преподаватель",
    )
    user = owner_field()

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"


class CoursePhoto(models.Model):
    """Фотоальбом курса: к одному курсу можно привязать много фотографий."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Курс",
    )
    image = models.ImageField("Фото", upload_to="courses")
    caption = models.CharField("Подпись", max_length=200, blank=True)
    uploaded_at = models.DateTimeField("Загружено", auto_now_add=True)
    user = owner_field()

    class Meta:
        verbose_name = "Фото курса"
        verbose_name_plural = "Фотоальбом курсов"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.caption or f"Фото #{self.pk}"


class Student(models.Model):
    """Студент (ученик), который записывается на курсы."""

    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    email = models.EmailField("E-mail", unique=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    year_of_study = models.PositiveSmallIntegerField("Курс обучения", default=1)
    picture = models.ImageField("Фото", upload_to="students", null=True, blank=True)
    user = owner_field()

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Enrollment(models.Model):
    """Запись студента на курс. Связывает Student и Course (две ForeignKey)."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Обучается"
        COMPLETED = "completed", "Завершён"
        DROPPED = "dropped", "Отчислен с курса"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Студент",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Курс",
    )
    enrolled_on = models.DateField("Дата записи", auto_now_add=True)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    grade = models.PositiveSmallIntegerField("Оценка", null=True, blank=True)
    user = owner_field()

    class Meta:
        verbose_name = "Запись на курс"
        verbose_name_plural = "Записи на курсы"
        ordering = ["-enrolled_on", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course"
            )
        ]

    def __str__(self):
        return f"{self.student} → {self.course.code}"
