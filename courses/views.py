from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json

from .models import (
    SegmentPage,
    ChapterPage,
    CoursePage,
    SegmentProgress,
    ChapterProgress,
    CourseProgress,
    QuizProgress,
    Quiz,
    Choice,
)


@require_POST
def submit_quiz(request, quiz_id):
    """
    Expects:
    {
      "answers": {
        "12": 45, # quiz id: question id
        "13": 48,
        "14": 50
      }
    }

    Returns:
    {
      "quiz_id": 5,
      "correct": 1,
      "total": 2,
      "score": 50,
      "details": {
        "12": { # quiz id
          "question": "What is the capital of France?",
          "submitted_choice": "45", # choice id
          "is_correct": true
        },
        "13": {
          "question": "Which planet is closest to the sun?",
          "submitted_choice": "48",
          "is_correct": false
        }
      },
      "saved": false
    }
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Parse JSON
    data = request.json or {}
    answers = data.get("answers", {})

    total = quiz.questions.count()
    correct_count = 0
    details = {}

    for q in quiz.questions.all():
        qid = str(q.id)
        submitted_choice_id = answers.get(qid)

        is_correct = False

        # Evaluate submitted answer
        if submitted_choice_id:
            try:
                submitted_choice = Choice.objects.get(
                    id=submitted_choice_id,
                    question=q
                )
                is_correct = submitted_choice.is_correct
            except Choice.DoesNotExist:
                pass

        if is_correct:
            correct_count += 1

        details[q.id] = {
            "question": q.text,
            "submitted_choice": submitted_choice_id,
            "is_correct": is_correct,
        }

    # Score
    score = int((correct_count / total) * 100) if total > 0 else 0

    # Save progress only for authenticated users
    if request.user.is_authenticated:
        qp, _ = QuizProgress.objects.get_or_create(
            user=request.user,
            quiz=quiz
        )
        qp.completed = True
        qp.score = score
        qp.save()

    return JsonResponse({
        "quiz_id": quiz.id,
        "correct": correct_count,
        "total": total,
        "score": score,
        "details": details,
        "saved": request.user.is_authenticated,
    })


def _is_chapter_complete(user, chapter):
    """
    A chapter is complete when ALL of its segments for this user
    have percent_watched >= 100.
    """
    # All segments under this chapter
    segments_qs = (
        chapter.get_children()
        .type(SegmentPage)
        .live()
    )

    total_segments = segments_qs.count()
    if total_segments == 0:
        return False

    completed_segments = SegmentProgress.objects.filter(
        user=user,
        segment__in=segments_qs,
        percent_watched__gte=100,
    ).count()

    return completed_segments == total_segments


def _is_course_complete(user, course):
    """
    A course is complete when ALL of its chapters are complete for this user.
    """
    chapters_qs = (
        course.get_children()
        .type(ChapterPage)
        .live()
        .specific()
    )

    if not chapters_qs.exists():
        return False

    for ch in chapters_qs:
        if not _is_chapter_complete(user, ch):
            return False

    return True


@require_POST
def update_progress(request):
    # Parse JSON safely
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request"}, status=400)

    segment_id = data.get("segment_id")
    percent_watched = data.get("percent_watched")

    if segment_id is None or percent_watched is None:
        return JsonResponse({"error": "Invalid request"}, status=400)

    segment = get_object_or_404(SegmentPage, id=segment_id)

    try:
        percent = float(percent_watched)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid percent_watched"}, status=400)

    # Clamp percent to 0–100
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100

    user = request.user
    authenticated = user.is_authenticated

    chapter_completed = False
    course_completed = False

    if authenticated:
        # Save or update SegmentProgress
        sp, _ = SegmentProgress.objects.get_or_create(
            user=user,
            segment=segment,
        )
        # either overwrite or keep the max; here we overwrite
        sp.percent_watched = percent
        sp.save()

        # Resolve chapter and course
        chapter = segment.get_parent().specific
        course = chapter.get_parent().specific if chapter else None

        # Update ChapterProgress
        if isinstance(chapter, ChapterPage):
            chapter_completed = _is_chapter_complete(user, chapter)
            cp, _ = ChapterProgress.objects.get_or_create(
                user=user,
                chapter=chapter,
            )
            cp.completed = chapter_completed
            if chapter_completed and cp.completed_at is None:
                cp.completed_at = timezone.now()
            cp.save()

        # Update CourseProgress
        if isinstance(course, CoursePage):
            course_completed = _is_course_complete(user, course)
            cprog, _ = CourseProgress.objects.get_or_create(
                user=user,
                course=course,
            )
            cprog.completed = course_completed
            if course_completed and cprog.completed_at is None:
                cprog.completed_at = timezone.now()
            cprog.save()

    # Anonymous users don’t get persisted state or completion inference
    return JsonResponse({
        "segment_id": segment.id,
        "saved": authenticated,
        "percent_watched": percent,
        "chapter_completed": chapter_completed if authenticated else False,
        "course_completed": course_completed if authenticated else False,
    })

