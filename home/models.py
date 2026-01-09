from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField

from courses.models import CoursesIndexPage, CoursePage, Instructor

class HomePage(Page):
    max_count = 1
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        "body",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get the CoursesIndexPage instance
        courses_index = CoursesIndexPage.objects.live().first()
        if courses_index:
            courses = courses_index.get_children().live().specific()
            
            # Get all tags
            tags = set()
            for course in courses:
                for tag in course.tags.all():
                    tags.add(str(tag))
            
            context['courses'] = courses

            # TODO: Consider sorting in order of importance
            context['all_tags'] = sorted(tags)

        # Get list of all instructors
        context['instructors'] = Instructor.objects.filter(role__name='instructor').order_by('name')

        # Get list of all contributors
        context['contributors'] = Instructor.objects.filter(role__name='contributor').order_by('name')
        
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