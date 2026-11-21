from django.contrib import admin
from django.utils.html import format_html

from .models import Course, CoursePhoto, Department, Enrollment, Student, Teacher


def image_preview(field_name):
    """Колонка-миниатюра для картинки в списке админки."""

    @admin.display(description="Фото")
    def preview(modeladmin, obj):
        image = getattr(obj, field_name)
        if not image:
            return "—"
        return format_html('<img src="{}" style="height:40px;border-radius:4px">', image.url)

    return preview


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description", "user"]
    list_filter = ["user"]
    search_fields = ["name"]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    photo_preview = image_preview("photo")
    list_display = ["id", "photo_preview", "last_name", "first_name", "email", "department", "user"]
    list_filter = ["department", "user"]
    search_fields = ["last_name", "first_name", "email"]


class CoursePhotoInline(admin.TabularInline):
    model = CoursePhoto
    extra = 0
    fields = ["image", "caption", "user"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # teacher__email — вывод поля связанной модели через двойное подчёркивание
    list_display = ["id", "code", "title", "credits", "department", "teacher", "teacher__email", "user"]
    list_filter = ["department", "teacher", "user"]
    search_fields = ["code", "title"]
    inlines = [CoursePhotoInline]


@admin.register(CoursePhoto)
class CoursePhotoAdmin(admin.ModelAdmin):
    photo_preview = image_preview("image")
    list_display = ["id", "photo_preview", "course", "caption", "uploaded_at", "user"]
    list_filter = ["course", "user"]
    search_fields = ["caption", "course__code"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    picture_preview = image_preview("picture")
    list_display = ["id", "picture_preview", "last_name", "first_name", "email", "year_of_study", "user"]
    list_filter = ["year_of_study", "user"]
    search_fields = ["last_name", "first_name", "email"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "course", "status", "grade", "enrolled_on", "user"]
    list_filter = ["status", "course", "user"]
    search_fields = ["student__last_name", "course__code", "course__title"]
    list_select_related = ["student", "course", "user"]
