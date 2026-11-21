from django.apps import AppConfig
from django.db.backends.signals import connection_created


def sqlite_unicode_lower(sender, connection, **kwargs):
    # Встроенная функция LOWER в SQLite переводит в нижний регистр только латиницу.
    # Заменяем её на Python-версию, чтобы поиск без учёта регистра работал и для кириллицы.
    if connection.vendor == "sqlite":
        connection.connection.create_function(
            "LOWER", 1, lambda s: s.lower() if isinstance(s, str) else s, deterministic=True
        )


class SchoolConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "school"
    verbose_name = "Запись на курсы"

    def ready(self):
        connection_created.connect(sqlite_unicode_lower)
