from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField


class HomePage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        "body",
    ]


class AboutPage(Page):
    max_count = 1


class SponsorsPage(Page):
    max_count = 1


class ContactPage(Page):
    max_count = 1


class NewsPage(Page):
    max_count = 1
