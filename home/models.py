from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images import get_image_model
from wagtail.snippets.models import register_snippet

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField

from courses.models import CoursesIndexPage, Instructor, build_courses_listing_context

import re


@register_snippet
class Announcement(models.Model):
    text = models.TextField()
    button_text = models.CharField(max_length=255)
    button_url = models.URLField()
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    active = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("text"),
                FieldPanel("button_text"),
                FieldPanel("button_url"),
            ],
            heading="Content",
        ),
        MultiFieldPanel(
            [
                FieldPanel("image"),
            ],
            heading="Image",
        ),
        MultiFieldPanel(
            [
                FieldPanel("active"),
                FieldPanel("sort_order"),
            ],
            heading="Settings",
        ),
    ]

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return self.text[:50]


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
            context.update(build_courses_listing_context(courses_index, user))

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

        context["announcements"] = Announcement.objects.filter(active=True).order_by("sort_order")

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
