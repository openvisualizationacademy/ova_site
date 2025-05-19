from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField


class HomePage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + ["body"]