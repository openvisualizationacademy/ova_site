from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField


class HomePage(Page):
    max_count = 1
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        "body",
    ]


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