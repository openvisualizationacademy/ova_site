from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.shortcuts import render, get_object_or_404

from .models import User
from courses.models import (
    CoursePage,
    ChapterPage,
    SegmentPage,
    CourseProgress,
    ChapterProgress,
    SegmentProgress,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "is_staff", "is_active", "date_joined"]
    search_fields = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")

    # to check course progress
    change_form_template = "admin/user_change_form_with_progress.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/course-progress/",
                self.admin_site.admin_view(self.course_progress_view),
                name="user-course-progress",
            ),
        ]
        return custom_urls + urls

    def course_progress_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)

        course_id = request.GET.get("course")
        courses = CoursePage.objects.live()

        selected_course = None
        progress = None
        course_percent_complete = None
        course_progress = None

        if course_id:
            selected_course = get_object_or_404(CoursePage, pk=course_id)

            chapters = (
                selected_course.get_children().type(ChapterPage).live().specific()
            )
            total_chapters = chapters.count()

            # course progress (persisted)
            course_progress = CourseProgress.objects.filter(
                user=user,
                course=selected_course,
            ).first()

            completed_chapters = ChapterProgress.objects.filter(
                user=user,
                chapter__in=chapters,
                completed=True,
            ).count()

            course_percent_complete = (
                int((completed_chapters / total_chapters) * 100)
                if total_chapters > 0
                else 0
            )

            # bulk-load chapter + segment progress
            chapter_progress_map = {
                cp.chapter_id: cp
                for cp in ChapterProgress.objects.filter(
                    user=user,
                    chapter__in=chapters,
                )
            }

            segments = (
                SegmentPage.objects.filter(path__startswith=selected_course.path)
                .live()
                .specific()
            )

            segment_progress_map = {
                sp.segment_id: sp
                for sp in SegmentProgress.objects.filter(
                    user=user,
                    segment__in=segments,
                )
            }

            progress = []

            for chapter in chapters:
                chapter_segments = [
                    s for s in segments if s.get_parent().id == chapter.id
                ]

                progress.append(
                    {
                        "chapter": chapter,
                        "chapter_progress": chapter_progress_map.get(chapter.id),
                        "segments": [
                            {
                                "segment": seg,
                                "progress": segment_progress_map.get(seg.id),
                            }
                            for seg in chapter_segments
                        ],
                    }
                )

        return render(
            request,
            "admin/user_course_progress.html",
            {
                "user": user,
                "courses": courses,
                "selected_course": selected_course,
                "course_progress": course_progress,
                "course_percent_complete": course_percent_complete,
                "progress": progress,
            },
        )
