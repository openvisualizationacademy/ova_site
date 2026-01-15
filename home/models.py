from django.db import models
from django.db.models import Prefetch

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField

from courses.models import CoursesIndexPage, CoursePage, CourseProgress, Instructor

import re

class HomePage(Page):
    max_count = 1
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        "body",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        user = request.user

        # Get the CoursesIndexPage instance
        courses_index = CoursesIndexPage.objects.live().first()
        if courses_index:
            courses = courses_index.get_children().live().specific()
            
            # Get all tags
            tags = set()
            for course in courses:
                for tag in course.tags.all():
                    tags.add(str(tag))
            
            # Check if user completed any course
            if user.is_authenticated:
                progress_queryset = CourseProgress.objects.filter(user=user)
                courses = courses.prefetch_related(
                    Prefetch(
                        'courseprogress_set',
                        queryset=progress_queryset,
                        to_attr='progress'
                    )
                )
                for course in courses:
                    # Access and assign first item in the list created by to_attr
                    progress = course.progress[0] if course.progress else None
                    course.completed = progress.completed if progress else False

            context['courses'] = courses

            # TODO: Consider sorting in order of importance
            context['all_tags'] = sorted(tags)

        # Process social links for instructors or contributors for displaying in UI
        def clean_social_links(people):
            # Pre-compile regex for removing links protocol and www.
            URL_CLEANER = re.compile(r'^(https?://)?(www\.)?', re.IGNORECASE)
            for person in people:
                person.processed_social_links = []
                for link in person.social_links:
                    processed = {
                        # Full URL to be used for href
                        'url': link,

                        # Clean URL for displaying (no protocol, www, or trailing slash)
                        'clean': URL_CLEANER.sub('', link).rstrip('/')
                    }
                    person.processed_social_links.append(processed)
            return people

        # Get list of all instructors
        instructors = Instructor.objects.filter(role__name='instructor').order_by('name').prefetch_related('instructor_course__page')
        context['instructors'] = clean_social_links(instructors)

        # Get list of all contributors
        contributors = Instructor.objects.filter(role__name='contributor').order_by('name')
        context['contributors'] = clean_social_links(contributors)
        
        return context


class NonCoursePage(Page):
    max_count = 1
    parent_page_types = ["home.HomePage"]


class AboutPage(NonCoursePage):
    template = "home/about.html"


class SponsorsPage(NonCoursePage):
    template = "home/sponsors.html"


class ContactPage(NonCoursePage):
    template = "home/contact.html"


class NewsPage(NonCoursePage):
    template = "home/news.html"