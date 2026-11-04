"""Конфигурация приложения blog."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Класс конфигурации приложения blog."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
    verbose_name = "Блог"
