from nested_admin import nested



from models import (
    Choice,
    Question
)
from admins.base import (
    CustomNestedModelAdmin,
    PoolValidator
)


class ChoiceAdmin(nested.NestedStackedInline):
    model = Choice
    extra = 0

    def __repr__(self):
        return "ChoiceAdmin"


class QuestionAdmin(nested.NestedStackedInline):
    model = Question
    inlines = [ChoiceAdmin]
    extra = 1

    def __repr__(self):
        return "QuestionAdmin"


# ------------------------------------------------ POOL ADMIN CONFIG ---------------------------------------------------
class PoolAdmin(CustomNestedModelAdmin):
    VALIDATOR = PoolValidator()

    list_display = [
        "title",
        "id",
        "start_time",
        "end_time",
        "randomize_questions",
        "back_ability",
        "continue_ability",
        "is_enable"
    ]

    exclude = ("quiz_type",)
    inlines = [QuestionAdmin]

    def __repr__(self):
        return "PoolAdmin"
