from django.template.response import TemplateResponse


class QuizMixin:

    def get_quiz(self):
        return self.quizzes.first()

    def extract_answers(self, request, quiz):
        answers = {}
        for question in quiz.questions.all():
            key = str(question.id)
            answers[key] = request.POST.get(key)
        return answers

    def grade_quiz(self, quiz, answers):
        correct = 0
        total = quiz.questions.count()

        for question in quiz.questions.all():
            submitted = answers.get(str(question.id))
            if not submitted:
                continue

            try:
                choice = question.choices.get(id=submitted)
                if choice.is_correct:
                    correct += 1
            except Choice.DoesNotExist:
                pass

        return int((correct / total) * 100) if total else 0

    def save_quiz_progress(self, user, quiz, score):
        from .models import QuizProgress
        qp, _ = QuizProgress.objects.get_or_create(user=user, quiz=quiz)
        qp.completed = True
        qp.score = score
        qp.save()

    def handle_quiz_submission(self, request):
        quiz = self.get_quiz()
        if not quiz:
            return super().serve(request)

        answers = self.extract_answers(request, quiz)
        score = self.grade_quiz(quiz, answers)

        # Save quiz progress
        if request.user.is_authenticated:
            self.save_quiz_progress(request.user, quiz, score)

            # -----------------------------------------------------------
            # Mark the segment as complete via SegmentProgress
            # -----------------------------------------------------------
            from .models import SegmentProgress
            segment = self
            seg_prog, _ = SegmentProgress.objects.get_or_create(
                user=request.user,
                segment=segment
            )
            seg_prog.percent_watched = 100
            seg_prog.completed = True
            seg_prog.save()

        # Build context
        context = self.get_context(request)
        context["quiz"] = quiz
        context["answers"] = answers
        context["submitted"] = True
        context["score"] = score

        return TemplateResponse(
            request,
            self.get_template(request),
            context
        )
