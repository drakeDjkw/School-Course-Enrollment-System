from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Course, CoursePhoto, Department, Enrollment, Student, Teacher


class OwnedSerializer(serializers.ModelSerializer):
    """Базовый сериализатор: при создании записывает в объект текущего пользователя."""

    user = serializers.SlugRelatedField(slug_field="username", read_only=True)

    def create(self, validated_data):
        # self.context["request"] заполняет ViewSet, в нём есть текущий пользователь
        if "request" in self.context:
            validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# --- Краткие сериализаторы для вложенного вывода связанных объектов ---


class DepartmentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class TeacherBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ["id", "first_name", "last_name"]


class StudentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "first_name", "last_name"]


class CourseBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "title"]


# --- Основные сериализаторы ---


class DepartmentSerializer(OwnedSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description", "user"]


class TeacherSerializer(OwnedSerializer):
    # при чтении — вложенный объект кафедры, при записи — её id
    department = DepartmentBriefSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department", queryset=Department.objects.all(), write_only=True
    )

    class Meta:
        model = Teacher
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "department",
            "department_id",
            "photo",
            "user",
        ]


class CourseSerializer(OwnedSerializer):
    department = DepartmentBriefSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department", queryset=Department.objects.all(), write_only=True
    )
    teacher = TeacherBriefSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        source="teacher",
        queryset=Teacher.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "code",
            "title",
            "credits",
            "max_students",
            "department",
            "department_id",
            "teacher",
            "teacher_id",
            "user",
        ]


class CoursePhotoSerializer(OwnedSerializer):
    class Meta:
        model = CoursePhoto
        fields = ["id", "course", "image", "caption", "uploaded_at", "user"]
        read_only_fields = ["uploaded_at"]


class StudentSerializer(OwnedSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "year_of_study",
            "picture",
            "user",
        ]


class EnrollmentSerializer(OwnedSerializer):
    student = StudentBriefSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        source="student", queryset=Student.objects.all(), write_only=True
    )
    course = CourseBriefSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course", queryset=Course.objects.all(), write_only=True
    )

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_id",
            "course",
            "course_id",
            "enrolled_on",
            "status",
            "grade",
            "user",
        ]
        read_only_fields = ["enrolled_on"]

    def validate(self, attrs):
        # студент не может записаться на один и тот же курс дважды
        student = attrs.get("student", getattr(self.instance, "student", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        duplicates = Enrollment.objects.filter(student=student, course=course)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if student and course and duplicates.exists():
            raise serializers.ValidationError("Студент уже записан на этот курс.")
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "is_superuser"]
