from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'questions'
    verbose_name = 'Вопросы и ответы'

    def ready(self):
        from . import signals  # noqa: F401
