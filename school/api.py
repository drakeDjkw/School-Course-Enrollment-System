from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.middleware.csrf import get_token
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response

from .exporters import DOCX_TYPE, XLSX_TYPE, build_docx, build_xlsx
from .models import Course, CoursePhoto, Department, Enrollment, Student, Teacher
from .serializers import (
    CoursePhotoSerializer,
    CourseSerializer,
    DepartmentSerializer,
    EnrollmentSerializer,
    StudentSerializer,
    TeacherSerializer,
    UserSerializer,
)


def stat(label, value):
    """Одна строка статистики: {"label": ..., "value": ...}."""
    if isinstance(value, float):
        value = round(value, 2)
    return {"label": label, "value": value}


def owner_name(obj):
    return obj.user.username if obj.user else ""


class CrudViewSet(
    mixins.CreateModelMixin,    # POST   /api/<model>/         — создание
    mixins.RetrieveModelMixin,  # GET    /api/<model>/<id>/    — один объект
    mixins.UpdateModelMixin,    # PUT/PATCH /api/<model>/<id>/ — изменение
    mixins.DestroyModelMixin,   # DELETE /api/<model>/<id>/    — удаление
    mixins.ListModelMixin,      # GET    /api/<model>/         — список
    viewsets.GenericViewSet,
):
    """Базовый ViewSet: CRUD, доступ только к своим данным, фильтры, статистика, экспорт."""

    permission_classes = [IsAuthenticated]

    # фильтры по колонкам: параметр запроса -> выражение для .filter()
    filterset = {}

    # экспорт: заголовок документа и колонки (название, функция от объекта)
    export_title = "Data"
    export_fields = []

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        params = self.request.query_params
        try:
            if user.is_superuser:
                # суперпользователь видит всё и может отфильтровать по владельцу
                owner = params.get("user")
                if owner:
                    qs = qs.filter(user_id=owner)
            else:
                # обычный пользователь видит только свои записи
                qs = qs.filter(user=user)

            for param, lookup in self.filterset.items():
                value = params.get(param)
                if value in (None, ""):
                    continue
                if lookup.endswith("__icontains"):
                    # поиск без учёта регистра: сравниваем LOWER(поле) с value.lower()
                    # (обычный icontains в SQLite не понимает регистр кириллицы)
                    field = lookup.removesuffix("__icontains")
                    alias = f"_filter_{param}"
                    qs = qs.annotate(**{alias: Lower(field)}).filter(**{f"{alias}__contains": value.lower()})
                else:
                    qs = qs.filter(**{lookup: value})
        except (ValueError, ValidationError):
            # неправильное значение фильтра (например, буквы вместо id) — пустой результат
            return qs.none()
        return qs

    def get_stats(self, qs):
        return [stat("Total records", qs.count())]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """GET /api/<model>/stats/ — агрегированная статистика с учётом фильтров."""
        return Response(self.get_stats(self.get_queryset()))

    @action(detail=False, methods=["get"])
    def export(self, request):
        """GET /api/<model>/export/?type=xlsx|docx — выгрузка таблицы с учётом фильтров."""
        headers = [header for header, _ in self.export_fields]
        rows = [[getter(obj) for _, getter in self.export_fields] for obj in self.get_queryset()]

        if request.query_params.get("type") == "docx":
            content, content_type, ext = build_docx(self.export_title, headers, rows), DOCX_TYPE, "docx"
        else:
            content, content_type, ext = build_xlsx(self.export_title, headers, rows), XLSX_TYPE, "xlsx"

        response = HttpResponse(content, content_type=content_type)
        filename = f"{self.basename}.{ext}"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class DepartmentViewSet(CrudViewSet):
    queryset = Department.objects.select_related("user")
    serializer_class = DepartmentSerializer
    filterset = {
        "name": "name__icontains",
        "description": "description__icontains",
    }
    export_title = "Departments"
    export_fields = [
        ("ID", lambda o: o.id),
        ("Name", lambda o: o.name),
        ("Description", lambda o: o.description),
        ("Owner", owner_name),
    ]

    def get_stats(self, qs):
        per_department = qs.annotate(
            n_teachers=Count("teachers", distinct=True),
            n_courses=Count("courses", distinct=True),
        ).aggregate(
            avg_teachers=Avg("n_teachers"),
            avg_courses=Avg("n_courses"),
            max_courses=Max("n_courses"),
        )
        return [
            stat("Departments", qs.count()),
            stat("Avg teachers per department", per_department["avg_teachers"]),
            stat("Avg courses per department", per_department["avg_courses"]),
            stat("Most courses in one department", per_department["max_courses"]),
        ]


class TeacherViewSet(CrudViewSet):
    queryset = Teacher.objects.select_related("department", "user")
    serializer_class = TeacherSerializer
    filterset = {
        "first_name": "first_name__icontains",
        "last_name": "last_name__icontains",
        "email": "email__icontains",
        "department": "department_id",
    }
    export_title = "Teachers"
    export_fields = [
        ("ID", lambda o: o.id),
        ("Last name", lambda o: o.last_name),
        ("First name", lambda o: o.first_name),
        ("E-mail", lambda o: o.email),
        ("Department", lambda o: o.department.name),
        ("Owner", owner_name),
    ]

    def get_stats(self, qs):
        agg = qs.aggregate(
            total=Count("id"),
            departments=Count("department", distinct=True),
        )
        courses = qs.annotate(n=Count("courses")).aggregate(avg=Avg("n"), max=Max("n"))
        with_photo = qs.exclude(photo="").exclude(photo__isnull=True).count()
        return [
            stat("Teachers", agg["total"]),
            stat("Departments represented", agg["departments"]),
            stat("Avg courses per teacher", courses["avg"]),
            stat("Most courses per teacher", courses["max"]),
            stat("Teachers with photo", with_photo),
        ]


class CourseViewSet(CrudViewSet):
    queryset = Course.objects.select_related("department", "teacher", "user")
    serializer_class = CourseSerializer
    filterset = {
        "code": "code__icontains",
        "title": "title__icontains",
        "credits": "credits",
        "max_students": "max_students",
        "department": "department_id",
        "teacher": "teacher_id",
    }
    export_title = "Courses"
    export_fields = [
        ("ID", lambda o: o.id),
        ("Code", lambda o: o.code),
        ("Title", lambda o: o.title),
        ("Credits", lambda o: o.credits),
        ("Max students", lambda o: o.max_students),
        ("Department", lambda o: o.department.name),
        ("Teacher", lambda o: str(o.teacher) if o.teacher else ""),
        ("Owner", owner_name),
    ]

    def get_stats(self, qs):
        agg = qs.aggregate(
            total=Count("id"),
            avg_credits=Avg("credits"),
            min_credits=Min("credits"),
            max_credits=Max("credits"),
            seats=Sum("max_students"),
            no_teacher=Count("id", filter=Q(teacher__isnull=True)),
        )
        enrollments = qs.annotate(n=Count("enrollments")).aggregate(avg=Avg("n"))
        return [
            stat("Courses", agg["total"]),
            stat("Avg credits", agg["avg_credits"]),
            stat("Min credits", agg["min_credits"]),
            stat("Max credits", agg["max_credits"]),
            stat("Total seats", agg["seats"]),
            stat("Avg enrollments per course", enrollments["avg"]),
            stat("Courses without teacher", agg["no_teacher"]),
        ]


class CoursePhotoViewSet(CrudViewSet):
    queryset = CoursePhoto.objects.select_related("course", "user")
    serializer_class = CoursePhotoSerializer
    filterset = {"course": "course_id"}
    export_title = "Course photos"
    export_fields = [
        ("ID", lambda o: o.id),
        ("Course", lambda o: str(o.course)),
        ("Caption", lambda o: o.caption),
        ("Uploaded", lambda o: o.uploaded_at.strftime("%Y-%m-%d %H:%M")),
        ("Owner", owner_name),
    ]

    def get_stats(self, qs):
        agg = qs.aggregate(total=Count("id"), courses=Count("course", distinct=True))
        return [
            stat("Photos", agg["total"]),
            stat("Courses with photos", agg["courses"]),
        ]


class StudentViewSet(CrudViewSet):
    queryset = Student.objects.select_related("user")
    serializer_class = StudentSerializer
    filterset = {
        "first_name": "first_name__icontains",
        "last_name": "last_name__icontains",
        "email": "email__icontains",
        "birth_year": "birth_date__year",
        "year_of_study": "year_of_study",
    }
    export_title = "Students"
    export_fields = [
        ("ID", lambda o: o.id),
        ("Last name", lambda o: o.last_name),
        ("First name", lambda o: o.first_name),
        ("E-mail", lambda o: o.email),
        ("Birth date", lambda o: o.birth_date),
        ("Year of study", lambda o: o.year_of_study),
        ("Owner", owner_name),
    ]

    def get_stats(self, qs):
        agg = qs.aggregate(
            total=Count("id"),
            avg_year=Avg("year_of_study"),
            oldest=Min("birth_date"),
            youngest=Max("birth_date"),
        )
        courses = qs.annotate(n=Count("enrollments")).aggregate(avg=Avg("n"), max=Max("n"))
        with_photo = qs.exclude(picture="").exclude(picture__isnull=True).count()
        return [
            stat("Students", agg["total"]),
            stat("Avg year of study", agg["avg_year"]),
            stat("Earliest birth date", agg["oldest"]),
            stat("Latest birth date", agg["youngest"]),
            stat("Avg courses per student", courses["avg"]),
            stat("Most courses per student", courses["max"]),
            stat("Students with photo", with_photo),
        ]


class EnrollmentViewSet(CrudViewSet):
    queryset = Enrollment.objects.select_related("student", "course", "user")
    serializer_class = EnrollmentSerializer
    filterset = {
        "student": "student__last_name__icontains",
        "course": "course_id",
        "status": "status",
        "grade": "grade",
        "enrolled_on": "enrolled_on",
    }
    export_title = "Enrollments"
    export_fields = [
        ("ID", lambda o: o.id),
        ("Student", lambda o: str(o.student)),
        ("Course", lambda o: str(o.course)),
        ("Status", lambda o: o.get_status_display()),
        ("Grade", lambda o: o.grade),
        ("Enrolled on", lambda o: o.enrolled_on),
        ("Owner", owner_name),
    ]

    def get_stats(self, qs):
        agg = qs.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(status=Enrollment.Status.ACTIVE)),
            completed=Count("id", filter=Q(status=Enrollment.Status.COMPLETED)),
            dropped=Count("id", filter=Q(status=Enrollment.Status.DROPPED)),
            avg_grade=Avg("grade"),
            students=Count("student", distinct=True),
            courses=Count("course", distinct=True),
        )
        return [
            stat("Enrollments", agg["total"]),
            stat("Active", agg["active"]),
            stat("Completed", agg["completed"]),
            stat("Dropped", agg["dropped"]),
            stat("Avg grade", agg["avg_grade"]),
            stat("Distinct students", agg["students"]),
            stat("Distinct courses", agg["courses"]),
        ]


# --- Пользователи и авторизация ---


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


def user_info(user):
    if not user.is_authenticated:
        return {"is_authenticated": False}
    return {
        "is_authenticated": True,
        "id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
    }


class UserViewSet(viewsets.GenericViewSet):
    """
    GET  /api/users/         — список пользователей (только для суперпользователя)
    GET  /api/users/info/    — кто сейчас вошёл (+ выдаёт cookie csrftoken)
    POST /api/users/login/   — вход по логину и паролю
    POST /api/users/logout/  — выход
    """

    queryset = get_user_model().objects.order_by("username")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsSuperuser()]
        return [AllowAny()]

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=["get"])
    def info(self, request):
        get_token(request._request)  # гарантирует, что браузер получит cookie csrftoken
        return Response(user_info(request.user))

    @action(detail=False, methods=["post"])
    def login(self, request):
        user = auth.authenticate(
            request._request,
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        auth.login(request._request, user)
        return Response(user_info(user))

    @action(detail=False, methods=["post"])
    def logout(self, request):
        auth.logout(request._request)
        return Response(user_info(request._request.user))
