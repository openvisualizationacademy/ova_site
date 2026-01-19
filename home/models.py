from django.db import models
from django.db.models import Prefetch
from wagtail.admin.panels import FieldPanel

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField

from courses.models import CoursesIndexPage, CoursePage, CourseProgress, Instructor

import re


class HomePage(Page):
    max_count = 1
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        user = request.user

        # Get the CoursesIndexPage instance
        courses_index = CoursesIndexPage.objects.live().first()
        if courses_index:
            # Build the complete queryset with all prefetches
            courses_query = (
                courses_index.get_children()
                .live()
                .specific()
                .prefetch_related(
                    "tags",
                    "course_instructors__instructor",
                    "course_instructors__instructor__image",
                    "image",  # Prefetch course images
                )
            )

            # Add progress prefetch for authenticated users
            if user.is_authenticated:
                progress_queryset = CourseProgress.objects.filter(user=user)
                courses_query = courses_query.prefetch_related(
                    Prefetch(
                        "courseprogress_set",
                        queryset=progress_queryset,
                        to_attr="progress",
                    )
                )

            # Evaluate queryset ONCE into a list
            courses = list(courses_query)

            # Get all tags - data already loaded
            tags = set()
            for course in courses:
                for tag in course.tags.all():
                    tags.add(str(tag))

            # Set completed flag for authenticated users
            if user.is_authenticated:
                for course in courses:
                    # Access and assign first item in the list created by to_attr
                    progress = course.progress[0] if course.progress else None
                    course.completed = progress.completed if progress else False

            context["courses"] = courses

            # TODO: Consider sorting in order of importance
            context["all_tags"] = sorted(tags)

        # Process social links for instructors or contributors for displaying in UI
        def clean_social_links(people):
            # Pre-compile regex for removing links protocol and www.
            URL_CLEANER = re.compile(r"^(https?://)?(www\.)?", re.IGNORECASE)
            for person in people:
                person.processed_social_links = []
                for link in person.social_links:
                    processed = {
                        # Full URL to be used for href
                        "url": link,
                        # Clean URL for displaying (no protocol, www, or trailing slash)
                        "clean": URL_CLEANER.sub("", link).rstrip("/"),
                    }
                    person.processed_social_links.append(processed)
            return people

        # Get list of all instructors
        instructors = (
            Instructor.objects.filter(role__name="instructor")
            .order_by("name")
            .prefetch_related(
                "instructor_course__page", "image"  # Prefetch instructor images
            )
        )
        context["instructors"] = clean_social_links(instructors)

        # Get list of all contributors
        contributors = (
            Instructor.objects.filter(role__name="contributor")
            .order_by("name")
            .prefetch_related("image")  # Prefetch contributor images
        )
        context["contributors"] = clean_social_links(contributors)

        return context


class NonCoursePage(Page):
    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = []


class AboutPage(NonCoursePage):
    template = "home/about.html"


class SponsorsPage(NonCoursePage):
    template = "home/sponsors.html"


class AccessibilityPage(NonCoursePage):
    template = "home/accessibility.html"


class BrandPage(NonCoursePage):
    template = "home/brand.html"
