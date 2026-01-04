from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
import json

from .models import (
    SegmentPage,
    ChapterPage,
    CoursePage,
    SegmentProgress,
    ChapterProgress,
    CourseProgress,
    Quiz,
    Choice,
    QuizProgress,
)


def _is_chapter_complete(user, chapter):
    """
    A chapter is complete when ALL of its segments for this user
    have percent_watched >= 100.
    """
    # All segments under this chapter
    segments_qs = chapter.get_children().type(SegmentPage).live()

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
    chapters_qs = course.get_children().type(ChapterPage).live().specific()

    if not chapters_qs.exists():
        return False

    for ch in chapters_qs:
        if not _is_chapter_complete(user, ch):
            return False

    return True


@csrf_exempt
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
    return JsonResponse(
        {
            "segment_id": segment.id,
            "saved": authenticated,
            "percent_watched": percent,
            "chapter_completed": chapter_completed if authenticated else False,
            "course_completed": course_completed if authenticated else False,
        }
    )


@require_http_methods(["GET", "POST"])
def quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    submitted = False
    answers = {}
    correct_count = 0
    total = quiz.questions.count()

    if request.method == "POST":
        submitted = True

        for question in quiz.questions.all():
            qid = str(question.id)
            choice_id = request.POST.get(qid)

            if not choice_id:
                continue

            answers[question.id] = choice_id

            choice = Choice.objects.filter(id=choice_id, question=question).first()

            if choice and choice.is_correct:
                correct_count += 1

        score = round((correct_count / total) * 100) if total else 0

        # ✅ Mark quiz completed for authenticated users only
        if request.user.is_authenticated:
            QuizProgress.objects.update_or_create(
                user=request.user,
                quiz=quiz,
                defaults={
                    "completed": True,
                    "score": score,
                },
            )

    else:
        score = 0

    return render(
        request,
        "quiz.html",
        {
            "quiz": quiz,
            "submitted": submitted,
            "answers": answers,
            "score": score,
        },
    )
