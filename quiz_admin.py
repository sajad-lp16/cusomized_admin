from nested_admin import nested



from main_app.models import (
    Choice,
    Question
)
from main_app.admins.base import (
    CustomNestedModelAdmin,
    QuizValidator
)


class ChoiceAdmin(nested.NestedStackedInline):
    model = Choice
    extra = 0

    def __repr__(self):
        return "ChoiceAdmin"


class QuestionAdmin(nested.NestedStackedInline):
    model = Question
    inlines = [ChoiceAdmin]
    extra = 0

    def __repr__(self):
        return "QuestionAdmin"


# ------------------------------------------------- QUIZ ADMIN CONFIG --------------------------------------------------
class QuizAdmin(CustomNestedModelAdmin):
    VALIDATOR = QuizValidator()

    list_display = [
        "title",
        "id",
        "start_time",
        "end_time",
        "grade",
        "randomize_questions",
        "back_ability",
        "continue_ability",
        "is_enable"
    ]

    exclude = ("quiz_type",)
    inlines = [QuestionAdmin]

    def __repr__(self):
        return "QuizAdmin"
