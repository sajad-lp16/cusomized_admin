from nested_admin import nested



from main_app.admins.base import (
    CustomNestedModelAdmin,
    UserQuizValidator
)
from main_app.models import (
    FileAnswer,
    TextAnswer,
    BaseScoredQuiz
)
from cachelib.cache_managers import StateCacheManager


class FileAnswersAdmin(nested.NestedStackedInline):
    model = FileAnswer

    # ---------------------------------------- PERMISSION AND FIELDS DISPLAY -------------------------------------------
    def has_add_permission(self, request, obj):
        return False

    @staticmethod
    def question_grade(instance):
        return instance.question.grade

    @staticmethod
    def question_text(instance):
        return instance.question.text

    def get_exclude(self, request, obj=None):
        exclude = [
            "answer_type",
            "question"
        ]
        if not isinstance(obj.quiz.related_model, BaseScoredQuiz):
            exclude += ["grade", "question_grade"]
        return exclude

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ["question_text", "file"]
        if isinstance(obj.quiz.related_model, BaseScoredQuiz):
            readonly_fields += ["question_grade"]
        return readonly_fields

    # ---------------------------------------------- EXTRA FIELDS ------------------------------------------------------


class TextAnswerAdmin(nested.NestedStackedInline):
    model = TextAnswer

    # ---------------------------------------- PERMISSION AND FIELDS DISPLAY -------------------------------------------
    def has_add_permission(self, request, obj):
        return False

    def get_exclude(self, request, obj=None):
        exclude = [
            "answer_type",
            "question",
            "text"
        ]
        if not isinstance(obj.quiz.related_model, BaseScoredQuiz):
            exclude += ["grade", "question_grade"]
        return exclude

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "question_text",
            "user_answer"
        ]
        if isinstance(obj.quiz.related_model, BaseScoredQuiz):
            readonly_fields += ["question_grade"]
        return readonly_fields

    # ---------------------------------------------- EXTRA FIELDS ------------------------------------------------------
    @staticmethod
    def question_grade(instance):
        return instance.question.grade

    @staticmethod
    def question_text(instance):
        return instance.question.text

    @staticmethod
    def user_answer(instance):
        return instance.text


class UserQuizAdmin(CustomNestedModelAdmin):
    VALIDATOR = UserQuizValidator()

    list_filter = "is_checked", "quiz__title", "user_id"
    search_fields = "user_id", "user_id", "quiz__title"
    list_display = (
        "user_id",
        "quiz_id",
        "quiz_type",
        "quiz_title",
        "is_checked",
        "grade",
        "quiz_grade",
        "finish_time",
        "correct_answers_count",
        "wrong_answers_count",
    )

    inlines = [FileAnswersAdmin, TextAnswerAdmin]

    # ---------------------------------------- PERMISSION AND FIELDS DISPLAY -------------------------------------------

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_exclude(self, request, obj=None):
        ex_fields = [
            "quiz",
            "grade",
        ]
        if not isinstance(obj.quiz.related_model, BaseScoredQuiz):
            ex_fields += ["user_grade", "total_quiz_grade", "correct_answers_count", "wrong_answers_count"]
        return ex_fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "user_id",
            "finish_time",
            "questions_count",
            "is_checked",
            "quiz_info"
        ]
        if isinstance(obj.quiz.related_model, BaseScoredQuiz):
            readonly_fields += ["user_grade", "total_quiz_grade", "correct_answers_count", "wrong_answers_count"]
        return readonly_fields

    def get_queryset(self, request):
        StateCacheManager.check_expired_states()
        return super().get_queryset(request).filter(finish_time__isnull=False)

    # ---------------------------------------------- EXTRA FIELDS ------------------------------------------------------
    @staticmethod
    def total_quiz_grade(instance):
        return instance.quiz.related_model.grade

    @staticmethod
    def user_grade(instance):
        return instance.grade

    @staticmethod
    def quiz_info(instance):
        return f"title: {instance.quiz.title}, id: {instance.quiz_id}"

    @staticmethod
    def quiz_grade(instance):
        try:
            return instance.quiz.related_model.grade
        except AttributeError:
            return None

    @staticmethod
    def quiz_title(instance):
        return instance.quiz.title

    @staticmethod
    def quiz_type(instance):
        return type(instance.quiz.related_model).__name__
