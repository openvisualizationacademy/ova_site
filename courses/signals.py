"""
Signal: reconcile_progress
==========================
Listens to: post_save on SegmentProgress
Purpose:    Automatically update ChapterProgress and CourseProgress whenever
            a user's segment watch progress is saved.

How it works:
    1. A SegmentProgress record is created or updated (e.g. when the video
       player reports percent_watched via the /api/progress/update/ endpoint).
    2. This signal fires and walks up the Wagtail page tree:
       SegmentPage -> ChapterPage -> CoursePage.
    3. It checks whether ALL segments in the chapter are now complete
       (percent_watched >= 100). If so, ChapterProgress is marked complete.
    4. It then checks whether ALL chapters in the course are complete.
       If so, CourseProgress is marked complete.

This replaces the need to run temp/reconcile_progress_apply.py manually.
The reconciliation is idempotent -- running it multiple times on already-
completed progress is a no-op.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender="courses.SegmentProgress")
def reconcile_progress(sender, instance, **kwargs):
    """
    After a SegmentProgress is saved, check whether the parent chapter
    and course should be marked complete for that user.

    Walks the page hierarchy (Segment -> Chapter -> Course) and creates or
    updates the corresponding progress records when all child items are done.
    """
    from .models import (
        ChapterPage,
        CoursePage,
        ChapterProgress,
        CourseProgress,
    )
    from .views import _is_chapter_complete, _is_course_complete

    if instance.percent_watched < 100:
        return

    user = instance.user
    segment = instance.segment

    # Walk up the Wagtail page tree: Segment -> Chapter -> Course
    chapter = segment.get_parent()
    if not chapter:
        return
    chapter = chapter.specific

    if not isinstance(chapter, ChapterPage):
        return

    course = chapter.get_parent()
    if not course:
        return
    course = course.specific

    # --- Chapter progress ---
    # A chapter is complete when every segment has percent_watched >= 100.
    if _is_chapter_complete(user, chapter):
        cp, created = ChapterProgress.objects.get_or_create(
            user=user,
            chapter=chapter,
            defaults={"completed": True, "completed_at": timezone.now()},
        )
        if not created and not cp.completed:
            cp.completed = True
            cp.completed_at = timezone.now()
            cp.save()

    # --- Course progress ---
    # A course is complete when every chapter is complete.
    if isinstance(course, CoursePage) and _is_course_complete(user, course):
        cprog, created = CourseProgress.objects.get_or_create(
            user=user,
            course=course,
            defaults={"completed": True, "completed_at": timezone.now()},
        )
        if not created and not cprog.completed:
            cprog.completed = True
            cprog.completed_at = timezone.now()
            cprog.save()


@receiver(post_delete, sender="courses.SegmentPage")
def update_course_duration_on_segment_delete(sender, instance, **kwargs):
    from .models import CoursePage, SegmentPage

    # Each Wagtail path step is 4 chars: segment is 2 levels below course
    course_path = instance.path[: (instance.depth - 2) * 4]
    if not course_path:
        return

    segments = SegmentPage.objects.filter(path__startswith=course_path).live()

    total_seconds = sum(
        int(seg.duration.total_seconds()) for seg in segments if seg.duration
    )

    CoursePage.objects.filter(path=course_path).update(duration_seconds=total_seconds)
