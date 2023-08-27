from django.utils.translation import gettext as _
from django.contrib import messages

from utils.classes import RegisterMethodsMeta
from main_app.models import Question, BaseScoredQuiz


class AbstractBaseValidator(metaclass=RegisterMethodsMeta, collection_name="validators", method_pattern="check_"):
    # Methods starting by [check_] will register and run automatically

    validators = []

    @staticmethod
    def add_msg_2_panel(request, msg_text, msg_type=messages.ERROR):
        messages.add_message(request, msg_type, _(msg_text))

    @staticmethod
    def high_light_fields(*formsets, field, msg):
        def _perform_highlight(_form, _field, _msg):
            if hasattr(_form, "forms"):
                for frm in _form.forms:
                    if frm.cleaned_data:
                        frm.add_error(field, _(msg))
                return
            _form.add_error(field, _(_msg))

        for formset in formsets:
            _perform_highlight(formset, field, msg)

    def check(self, request, form, formsets):
        for method in self.validators:
            if not method(self, request, form, formsets):
                return False
        return True


class BaseQuizValidator(AbstractBaseValidator, collection_name="validators", method_pattern="check_"):
    @staticmethod
    def ensure_has_choice_data(formset):
        for data in formset.cleaned_data:
            if data:
                return True
        return False

    def _check_has_choice(self, formsets):
        for formset in formsets:
            if type(formset).__name__ == "ChoiceFormFormSet":
                if self.ensure_has_choice_data(formset):
                    return True
        return False

    def check_has_question(self, request, _, formsets):
        for formset in formsets:
            if type(formset).__name__ == "QuestionFormFormSet" and formset.is_valid():
                data = formset.cleaned_data
                for item in data:
                    if item.keys():
                        return True
        self.add_msg_2_panel(request, "Quiz must contain questions!")
        return False

    def check_question_containing_choice(self, request, _, formsets):
        def _raise(target):
            self.add_msg_2_panel(request, "Question must contain choices!")
            self.high_light_fields(target, field="answer_type", msg="should define choices for this answer type!")
            return False

        for formset in formsets:
            if type(formset).__name__ == "QuestionFormFormSet" and formset.is_valid():
                for form in formset.forms:
                    if not form.cleaned_data.get("answer_type") in Question.CHOICE_ALLOWED_TYPES:
                        continue
                    if nested_forms := form.nested_formsets:
                        for _form in nested_forms:
                            if not _form.is_valid():
                                return _raise(form)
                            if data := _form.cleaned_data:
                                for _item in data:
                                    if _item.keys():
                                        break
                                else:
                                    return _raise(form)
                            else:
                                return _raise(form)
            return True

    def check_choice_based(self, request, form, formsets):
        if self._check_has_choice(formsets):
            return self.validate_has_choice(request, form, formsets)
        return self.validate_no_choice(request, form, formsets)

    def validate_has_choice(self, request, form, formsets):
        raise NotImplementedError

    def validate_no_choice(self, request, form, formsets):
        raise NotImplementedError

    def validate_single_choice(self, request, formsets):
        raise NotImplementedError

    def validate_multi_choice(self, request, formsets):
        raise NotImplementedError


class BaseScoredQuizValidator(BaseQuizValidator, collection_name="validators", method_pattern="check_"):

    def validate_has_choice(self, request, form, formsets):
        for formset in formsets:
            if type(formset).__name__ == "ChoiceFormFormSet":
                parent_grade = formset.parent_form.cleaned_data.get("grade")
                sum_grade = 0
                if not formset.cleaned_data:
                    continue
                for item in formset.cleaned_data:
                    if not item.keys():
                        continue
                    sum_grade += item["grade"]
                if sum_grade != parent_grade:
                    self.high_light_fields(formset, formset.parent_form, field="grade", msg="fix grade!")
                    self.add_msg_2_panel(request, "total grade of choices and question are not the same!")
                    return False
                parent_answer_type = formset.parent_form.cleaned_data.get("answer_type")
                if parent_answer_type == Question.AnswerType.ANSWER_TYPE_CHECKBOX.value:
                    if not self.validate_multi_choice(request, formset):
                        return False
                if not self.validate_single_choice(request, formset):
                    return False
        return True

    def validate_no_choice(self, request, form, formsets):
        return True

    def validate_single_choice(self, request, formset):
        correct_counter = 0
        for item in formset.cleaned_data:
            if (grade := item.get("grade")) is not None and grade > 0:
                correct_counter += 1
        if correct_counter == 1:
            return True
        self.high_light_fields(formset, field="grade", msg="fix grade!")
        self.add_msg_2_panel(request, "there must be one correct answer!")
        return False

    def validate_multi_choice(self, request, formset):
        correct_counter = 0
        for item in formset.cleaned_data:
            if (grade := item.get("grade")) is not None and grade > 0:
                correct_counter += 1
        if correct_counter > 1:
            return True
        self.high_light_fields(formset, field="grade", msg="fix grade!")
        self.add_msg_2_panel(request, "there must be more than one correct answer for checkbox!")
        return False

    def check_total_grade(self, request, form, formsets):
        total_grade = form.cleaned_data["grade"]
        sum_grade = 0
        for formset in formsets:
            if type(formset).__name__ == "QuestionFormFormSet":
                for item in formset.cleaned_data:
                    if (grade := item.get("grade")) is not None:
                        sum_grade += grade
        if total_grade == sum_grade:
            return True
        self.add_msg_2_panel(request, "question grades must equal to quiz grade!")
        self.high_light_fields(form, *formsets, field="grade", msg="fix grade!")
        return False


class BaseScorelessQuizValidator(BaseQuizValidator, collection_name="validators", method_pattern="check_"):
    def validate_has_choice(self, request, form, formsets):
        return True

    def validate_no_choice(self, request, form, formsets):
        return True

    def validate_single_choice(self, request, formset):
        return True

    def validate_multi_choice(self, request, formset):
        return True


# -------------------------------------------- EXERCISE VALIDATORS -----------------------------------------------------
class ExerciseValidator(BaseScoredQuizValidator, collection_name="validators", method_pattern="check_"):
    pass


# ---------------------------------------------- QUIZ VALIDATORS -------------------------------------------------------
class QuizValidator(BaseScoredQuizValidator, collection_name="validators", method_pattern="check_"):
    pass


# ---------------------------------------------- POOL VALIDATORS -------------------------------------------------------
class PoolValidator(BaseScorelessQuizValidator, collection_name="validators", method_pattern="check_"):
    pass


# ---------------------------------------------- MATCH VALIDATORS ------------------------------------------------------
class MatchValidator(BaseScoredQuizValidator, collection_name="validators", method_pattern="check_"):
    pass


# ------------------------------------------- USER QUIZ VALIDATORS -----------------------------------------------------
class UserQuizValidator(AbstractBaseValidator, collection_name="validators", method_pattern="check_"):
    def check_grades_question(self, request, form, formsets):
        if not isinstance(form.instance.quiz.related_model, BaseScoredQuiz):
            return True
        for formset in formsets:
            for _form in formset.forms:
                submitted_grade = _form.cleaned_data["grade"]
                if submitted_grade is None:
                    continue
                if submitted_grade > _form.instance.question.grade or submitted_grade < 0:
                    self.add_msg_2_panel(request, "given grade is higher than question grade!")
                    self.high_light_fields(formset, field="grade", msg="fix grade!")
                    return False
        return True

    def check_grades_quiz(self, request, form, formsets):
        quiz = form.instance.quiz.related_model
        if not isinstance(form.instance.quiz.related_model, BaseScoredQuiz):
            return True

        total_quiz_grade = quiz.grade
        sum_grade = 0
        for formset in formsets:
            for data in formset.cleaned_data:
                sum_grade = data.get("grade") or 0

        if sum_grade > total_quiz_grade:
            self.add_msg_2_panel(request, "total given grades are above quiz grade!")
            self.high_light_fields(formsets, field="grade", msg="fix grade!")
            return False
        return True
