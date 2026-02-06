import json

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from users.models import User
from courses.models import (
    CoursePage,
    ChapterPage,
    SegmentPage,
    CourseProgress,
    ChapterProgress,
    SegmentProgress,
    QuizProgress,
    Instructor,
)


def analytics_dashboard(request):
    """Main analytics dashboard view."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # ===================
    # USER METRICS
    # ===================
    total_users = User.objects.filter(is_active=True, is_staff=False).count()

    # New users (last 30 days)
    new_users_30d = User.objects.filter(
        date_joined__gte=thirty_days_ago,
        is_staff=False,
    ).count()

    # New users (last 7 days)
    new_users_7d = User.objects.filter(
        date_joined__gte=seven_days_ago,
        is_staff=False,
    ).count()

    # Active users (logged in within 30 days)
    active_users_30d = User.objects.filter(
        last_login__gte=thirty_days_ago,
        is_staff=False,
    ).count()

    # Active users (logged in within 7 days)
    active_users_7d = User.objects.filter(
        last_login__gte=seven_days_ago,
        is_staff=False,
    ).count()

    # Users with any progress (all time)
    users_with_progress = User.objects.filter(
        segmentprogress__isnull=False,
        is_staff=False,
    ).distinct().count()

    # Users with progress in last 30 days
    users_with_progress_30d = User.objects.filter(
        segmentprogress__last_updated__gte=thirty_days_ago,
        is_staff=False,
    ).distinct().count()

    # Users with progress in last 7 days
    users_with_progress_7d = User.objects.filter(
        segmentprogress__last_updated__gte=seven_days_ago,
        is_staff=False,
    ).distinct().count()

    user_metrics = {
        "total_users": total_users,
        "new_users_30d": new_users_30d,
        "new_users_7d": new_users_7d,
        "active_users_30d": active_users_30d,
        "active_users_7d": active_users_7d,
        "users_with_progress": users_with_progress,
        "users_with_progress_30d": users_with_progress_30d,
        "users_with_progress_7d": users_with_progress_7d,
    }

    # ===================
    # COURSE ENGAGEMENT METRICS
    # ===================

    # Course starts (users who have any progress in a course)
    course_starts = CourseProgress.objects.count()

    # Course completions
    course_completions = CourseProgress.objects.filter(completed=True).count()

    # Course completion rate
    completion_rate = (
        (course_completions / course_starts * 100) if course_starts > 0 else 0
    )

    # Chapter completions
    chapter_completions = ChapterProgress.objects.filter(completed=True).count()

    # Average watch percentage across all segment progress
    avg_watch_percentage = (
        SegmentProgress.objects.aggregate(avg=Avg("percent_watched"))["avg"] or 0
    )

    # Segments with 100% watched
    segments_completed = SegmentProgress.objects.filter(
        percent_watched__gte=100
    ).count()

    # Total segment progress records
    total_segment_progress = SegmentProgress.objects.count()

    # Recent completions (last 30 days)
    recent_completions = CourseProgress.objects.filter(
        completed=True,
        completed_at__gte=thirty_days_ago,
    ).count()

    # Quiz performance
    quiz_attempts = QuizProgress.objects.filter(completed=True).count()
    avg_quiz_score = (
        QuizProgress.objects.filter(completed=True).aggregate(avg=Avg("score"))["avg"] or 0
    )

    engagement_metrics = {
        "course_starts": course_starts,
        "course_completions": course_completions,
        "completion_rate": round(completion_rate, 1),
        "chapter_completions": chapter_completions,
        "avg_watch_percentage": round(avg_watch_percentage, 1),
        "segments_completed": segments_completed,
        "total_segment_progress": total_segment_progress,
        "recent_completions": recent_completions,
        "quiz_attempts": quiz_attempts,
        "avg_quiz_score": round(avg_quiz_score, 1),
    }

    # ===================
    # CONTENT ANALYTICS
    # ===================

    # Get all live courses
    courses = CoursePage.objects.live()

    course_stats = []
    for course in courses:
        # Count users who started this course
        starts = CourseProgress.objects.filter(course=course).count()

        # Count completions
        completions = CourseProgress.objects.filter(
            course=course, completed=True
        ).count()

        # Completion rate for this course
        rate = (completions / starts * 100) if starts > 0 else 0

        # Get segments for this course
        segments = SegmentPage.objects.filter(
            path__startswith=course.path
        ).live()

        # Average watch % for this course's segments
        avg_watch = (
            SegmentProgress.objects.filter(segment__in=segments)
            .aggregate(avg=Avg("percent_watched"))["avg"] or 0
        )

        # Get instructors
        instructors = [
            io.instructor.name
            for io in course.course_instructors.select_related("instructor").all()
        ]

        course_stats.append({
            "course": course,
            "title": course.title,
            "starts": starts,
            "completions": completions,
            "completion_rate": round(rate, 1),
            "avg_watch_percentage": round(avg_watch, 1),
            "instructors": ", ".join(instructors),
            "tags": list(course.tags.values_list("name", flat=True)),
            "coming_soon": bool(course.coming_soon),
        })

    # Sort by starts (most popular first)
    course_stats.sort(key=lambda x: x["starts"], reverse=True)

    # Instructor performance
    instructor_stats = []
    for instructor in Instructor.objects.all():
        # Get courses for this instructor
        instructor_courses = CoursePage.objects.filter(
            course_instructors__instructor=instructor
        ).live()

        if not instructor_courses.exists():
            continue

        total_starts = 0
        total_completions = 0

        for course in instructor_courses:
            total_starts += CourseProgress.objects.filter(course=course).count()
            total_completions += CourseProgress.objects.filter(
                course=course, completed=True
            ).count()

        rate = (total_completions / total_starts * 100) if total_starts > 0 else 0

        instructor_stats.append({
            "name": instructor.name,
            "courses_count": instructor_courses.count(),
            "total_starts": total_starts,
            "total_completions": total_completions,
            "completion_rate": round(rate, 1),
        })

    instructor_stats.sort(key=lambda x: x["total_starts"], reverse=True)

    # Tag performance
    from taggit.models import Tag
    tag_stats = []
    for tag in Tag.objects.all():
        tagged_courses = CoursePage.objects.filter(tags=tag).live()

        if not tagged_courses.exists():
            continue

        total_starts = 0
        total_completions = 0

        for course in tagged_courses:
            total_starts += CourseProgress.objects.filter(course=course).count()
            total_completions += CourseProgress.objects.filter(
                course=course, completed=True
            ).count()

        rate = (total_completions / total_starts * 100) if total_starts > 0 else 0

        tag_stats.append({
            "name": tag.name,
            "courses_count": tagged_courses.count(),
            "total_starts": total_starts,
            "total_completions": total_completions,
            "completion_rate": round(rate, 1),
        })

    tag_stats.sort(key=lambda x: x["total_starts"], reverse=True)

    content_metrics = {
        "course_stats": course_stats,
        "instructor_stats": instructor_stats,
        "tag_stats": tag_stats,
        "total_courses": courses.count(),
        "total_chapters": ChapterPage.objects.live().count(),
        "total_segments": SegmentPage.objects.live().count(),
    }

    # Prepare JSON export data (without course objects, just serializable data)
    metrics_for_json = {
        "generated_at": now.isoformat(),
        "user_metrics": user_metrics,
        "engagement_metrics": engagement_metrics,
        "content_metrics": {
            "course_stats": [
                {
                    "id": s["course"].id,
                    "title": s["title"],
                    "starts": s["starts"],
                    "completions": s["completions"],
                    "completion_rate": s["completion_rate"],
                    "avg_watch_percentage": s["avg_watch_percentage"],
                    "instructors": s["instructors"].split(", ") if s["instructors"] else [],
                    "tags": s["tags"],
                    "coming_soon": s["coming_soon"],
                }
                for s in course_stats
            ],
            "instructor_stats": instructor_stats,
            "tag_stats": tag_stats,
            "total_courses": content_metrics["total_courses"],
            "total_chapters": content_metrics["total_chapters"],
            "total_segments": content_metrics["total_segments"],
        },
    }

    context = {
        "title": "Analytics Dashboard",
        "user_metrics": user_metrics,
        "engagement_metrics": engagement_metrics,
        "content_metrics": content_metrics,
        "metrics_json": json.dumps(metrics_for_json),
        **admin.site.each_context(request),
    }

    return render(request, "admin/analytics_dashboard.html", context)


# Store original get_urls
_original_get_urls = admin.site.get_urls


def get_urls_with_analytics():
    """Add analytics URL to the default admin site."""
    urls = _original_get_urls()
    custom_urls = [
        path(
            "analytics/",
            admin.site.admin_view(analytics_dashboard),
            name="analytics-dashboard",
        ),
    ]
    return custom_urls + urls


# Monkey-patch the default admin site
admin.site.get_urls = get_urls_with_analytics
