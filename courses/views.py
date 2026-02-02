from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import get_object_or_404
import json
import requests

from .models import (
    SegmentPage,
    ChapterPage,
    CoursePage,
    SegmentProgress,
    ChapterProgress,
    CourseProgress,
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

            if chapter_completed and not cp.completed:
                cp.completed = True
                cp.completed_at = timezone.now()
                cp.save()

        # Update CourseProgress
        if isinstance(course, CoursePage):
            course_completed = _is_course_complete(user, course)

            cprog, _ = CourseProgress.objects.get_or_create(
                user=user,
                course=course,
            )

            if course_completed and not cprog.completed:
                cprog.completed = True
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


@login_required
def generate_certificate(request, course_id):
    # ---- 1. Get course and verify completion ----
    course = get_object_or_404(CoursePage, id=course_id)

    course_completed = CourseProgress.objects.filter(
        user=request.user,
        course=course,
        # completed=True,
    ).first()

    if not course_completed:
        raise Http404("Course not completed")

    # ---- 2. Resolve certificate fields ----
    # Display name: you can swap this for a form value later
    student_name = request.POST.get("display_name")
    if not student_name:
        raise Http404("Missing display name")

    # Course duration (human-readable)
    # TODO: calculate course duration from segments
    if course.duration:
        total_minutes = int(course.duration.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if minutes:
            course_duration = f"{hours}h {minutes}m"
        else:
            course_duration = f"{hours}h"
    else:
        course_duration = ""

    # Instructor names (comma-separated)
    instructors = [
        ci.instructor.name
        for ci in course.course_instructors.select_related("instructor").all()
    ]
    course_instructor = ", ".join(instructors)

    issue_date = course_completed.completed_at.date()

    # ---- 3. Render certificate HTML ----
    html = render_to_string(
        "certificate.html",
        {
            "student_name": student_name,
            "course_name": course.title,
            "course_duration": course_duration,
            "course_instructor": course_instructor,
            "issue_date": issue_date,
        },
    )

    # ---- 4. Call Azure Function ----
    response = requests.post(
        settings.CERT_FUNCTION_URL,  # includes ?code=...
        headers={
            "Content-Type": "text/html; charset=utf-8",
        },
        data=html.encode("utf-8"),
        timeout=30,
    )

    if response.status_code != 200:
        return HttpResponse(
            "Certificate generation failed",
            status=500,
        )

    # ---- 5. Return PDF ----
    return HttpResponse(
        response.content,
        content_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="certificate-{course.slug}.pdf"'
            ),
        },
    )
