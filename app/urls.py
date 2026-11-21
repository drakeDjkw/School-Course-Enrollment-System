from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from school.api import (
    CoursePhotoViewSet,
    CourseViewSet,
    DepartmentViewSet,
    EnrollmentViewSet,
    StudentViewSet,
    TeacherViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="departments")
router.register("teachers", TeacherViewSet, basename="teachers")
router.register("courses", CourseViewSet, basename="courses")
router.register("course-photos", CoursePhotoViewSet, basename="course-photos")
router.register("students", StudentViewSet, basename="students")
router.register("enrollments", EnrollmentViewSet, basename="enrollments")
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),  # вход в браузерном API DRF
]

# раздача загруженных картинок в режиме разработки
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
