from django.contrib import admin
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages

from .models import (
    Quiz,
    Question,
    CoursePage,
    ChapterPage,
    SegmentProgress,
    ChapterProgress,
    CourseProgress,
)
from .views import _is_chapter_complete, _is_course_complete


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    pass


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "completed", "completed_at")
    list_filter = ("completed", "course")
    search_fields = ("user__email",)

    change_list_template = "admin/courses/courseprogress/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "reconcile/",
                self.admin_site.admin_view(self.reconcile_view),
                name="courses_courseprogress_reconcile",
            ),
            path(
                "reconcile/apply/",
                self.admin_site.admin_view(self.reconcile_apply_view),
                name="courses_courseprogress_reconcile_apply",
            ),
        ]
        return custom_urls + urls

    def reconcile_view(self, request):
        """Generate a report of progress records that need fixing."""
        User = get_user_model()
        users = User.objects.all()
        courses = CoursePage.objects.live()

        issues = []

        for user in users:
            for course in courses:
                chapters = course.get_children().type(ChapterPage).live()

                # Check chapters
                for chapter in chapters:
                    should_be_completed = _is_chapter_complete(user, chapter)
                    if should_be_completed:
                        cp = ChapterProgress.objects.filter(
                            user=user, chapter=chapter
                        ).first()
                        if not cp:
                            issues.append({
                                "user": user.email,
                                "type": "Chapter",
                                "item": chapter.title,
                                "course": course.title,
                                "issue": "Missing record",
                            })
                        elif not cp.completed:
                            issues.append({
                                "user": user.email,
                                "type": "Chapter",
                                "item": chapter.title,
                                "course": course.title,
                                "issue": "Not marked complete",
                            })

                # Check course
                should_course_be_completed = _is_course_complete(user, course)
                if should_course_be_completed:
                    cprog = CourseProgress.objects.filter(
                        user=user, course=course
                    ).first()
                    if not cprog:
                        issues.append({
                            "user": user.email,
                            "type": "Course",
                            "item": course.title,
                            "course": course.title,
                            "issue": "Missing record",
                        })
                    elif not cprog.completed:
                        issues.append({
                            "user": user.email,
                            "type": "Course",
                            "item": course.title,
                            "course": course.title,
                            "issue": "Not marked complete",
                        })

        context = {
            **self.admin_site.each_context(request),
            "title": "Progress Reconciliation Report",
            "issues": issues,
            "issue_count": len(issues),
        }
        return TemplateResponse(
            request, "admin/courses/courseprogress/reconcile.html", context
        )

    def reconcile_apply_view(self, request):
        """Apply fixes to progress records."""
        if request.method != "POST":
            return redirect("admin:courses_courseprogress_reconcile")

        User = get_user_model()
        users = User.objects.all()
        courses = CoursePage.objects.live()

        chapter_created = 0
        chapter_updated = 0
        course_created = 0
        course_updated = 0

        for user in users:
            for course in courses:
                chapters = course.get_children().type(ChapterPage).live()

                # Fix chapters
                for chapter in chapters:
                    should_be_completed = _is_chapter_complete(user, chapter)
                    if should_be_completed:
                        cp, created = ChapterProgress.objects.get_or_create(
                            user=user,
                            chapter=chapter,
                            defaults={
                                "completed": True,
                                "completed_at": timezone.now(),
                            },
                        )
                        if created:
                            chapter_created += 1
                        elif not cp.completed:
                            cp.completed = True
                            cp.completed_at = timezone.now()
                            cp.save()
                            chapter_updated += 1

                # Fix course
                should_course_be_completed = _is_course_complete(user, course)
                if should_course_be_completed:
                    cprog, created = CourseProgress.objects.get_or_create(
                        user=user,
                        course=course,
                        defaults={
                            "completed": True,
                            "completed_at": timezone.now(),
                        },
                    )
                    if created:
                        course_created += 1
                    elif not cprog.completed:
                        cprog.completed = True
                        cprog.completed_at = timezone.now()
                        cprog.save()
                        course_updated += 1

        total = chapter_created + chapter_updated + course_created + course_updated
        messages.success(
            request,
            f"Reconciliation complete: {chapter_created} chapters created, "
            f"{chapter_updated} chapters updated, {course_created} courses created, "
            f"{course_updated} courses updated. Total: {total} changes.",
        )
        return redirect("admin:courses_courseprogress_changelist")


@admin.register(ChapterProgress)
class ChapterProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "chapter", "completed", "completed_at")
    list_filter = ("completed",)
    search_fields = ("user__email",)


@admin.register(SegmentProgress)
class SegmentProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "segment", "percent_watched", "last_updated")
    search_fields = ("user__email",)
