from django.template.response import TemplateResponse


class QuizMixin:

    def get_quiz(self):
        """Assume max 1 quiz per segment"""
        return self.quizzes.first()

    def extract_answers(self, request, quiz):
        answers = {}
        for question in quiz.questions.all():
            qid = question.id
            raw = request.POST.get(str(qid))

            try:
                answers[qid] = int(raw) if raw is not None else None
            except (TypeError, ValueError):
                answers[qid] = None

        return answers

    def grade_quiz(self, quiz, answers):
        from courses.models import Choice

        correct = 0
        total = quiz.questions.count()
        answer_results = {}

        for question in quiz.questions.all():
            qid = str(question.id)
            submitted = answers.get(question.id)

            if not submitted:
                answer_results[qid] = False
                continue

            try:
                choice = question.choices.get(id=submitted)
                is_correct = choice.is_correct
            except Choice.DoesNotExist:
                is_correct = False

            answer_results[question.id] = is_correct

            if is_correct:
                correct += 1

        score = int((correct / total) * 100) if total else 0
        return score, answer_results

    def save_quiz_progress(self, user, quiz, score, answers, answer_results):
        from .models import QuizProgress

        QuizProgress.objects.update_or_create(
            user=user,
            quiz=quiz,
            defaults={
                "completed": True,
                "score": score,
                "answers_snapshot": {
                    "answers": answers,
                    "results": answer_results,
                },
            },
        )

    def mark_segment_complete(self, user, score):
        from .models import SegmentProgress

        seg_prog, _ = SegmentProgress.objects.get_or_create(
            user=user,
            segment=self,
        )
        seg_prog.percent_watched = score
        seg_prog.save()

    def handle_quiz_submission(self, request):
        quiz = self.get_quiz()

        if not quiz:
            context = self.get_context(request)
            return TemplateResponse(request, self.get_template(request), context)

        answers = self.extract_answers(request, quiz)
        score, answer_results = self.grade_quiz(quiz, answers)

        if request.user.is_authenticated:
            self.save_quiz_progress(
                user=request.user,
                quiz=quiz,
                score=score,
                answers=answers,
                answer_results=answer_results,
            )
            self.mark_segment_complete(request.user, score)

        context = self.get_context(request)
        context.update(
            {
                "quiz": quiz,
                "answers": answers,
                "answer_results": answer_results,
                "submitted": True,
                "score": score,
            }
        )

        return TemplateResponse(request, self.get_template(request), context)

    def hydrate_quiz_from_progress(self, request):
        if not request.user.is_authenticated:
            return None

        quiz = self.get_quiz()
        if not quiz:
            return None

        from .models import QuizProgress

        qp = QuizProgress.objects.filter(
            user=request.user,
            quiz=quiz,
        ).first()

        if not qp or not qp.answers_snapshot:
            return None

        raw = qp.answers_snapshot

        # Normalize keys back to ints for template logic
        answers = {int(k): v for k, v in raw.get("answers", {}).items()}
        answer_results = {int(k): v for k, v in raw.get("results", {}).items()}

        return {
            "quiz": quiz,
            "answers": answers,
            "answer_results": answer_results,
            "submitted": True,
            "score": qp.score or 0,
        }
