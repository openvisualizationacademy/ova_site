from django.db import models
from django.contrib.auth import get_user_model
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.blocks import RichTextBlock
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

User = get_user_model()




@register_snippet
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Instructor(models.Model):
    name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True)
    bio = models.TextField()
    photo_url = models.URLField(blank=True)
    social_links = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=False)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("role"),
    ]

    def __str__(self):
        return self.name


class CoursesIndexPage(Page):
    subpage_types = ['CoursePage']
    max_count = 1  # optional

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["courses"] = self.get_children().live().specific()
        return context


class CoursePage(Page):
    instructors = models.ManyToManyField(User, related_name="courses")
    content = StreamField([
        ("rich_text", RichTextBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("instructors"),
        FieldPanel("content"),
        InlinePanel("materials", label="Course Materials"),
    ]

    parent_page_types = ['CoursesIndexPage']
    subpage_types = ["ChapterPage"]


class CourseMaterial(models.Model):
    course = ParentalKey(CoursePage, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="course_materials/", blank=True, null=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return self.title


class ChapterPage(Page):
    content = StreamField([
        ("rich_text", RichTextBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]

    parent_page_types = ["CoursePage"]
    subpage_types = ["SegmentPage"]


class SegmentPage(Page):
    video_url = models.URLField(blank=True)
    content = StreamField([
        ("rich_text", RichTextBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("video_url"),
        FieldPanel("content"),
    ]

    parent_page_types = ["ChapterPage"]
    subpage_types = []


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    chapter = models.ForeignKey(ChapterPage, related_name="quizzes", on_delete=models.CASCADE, null=True, blank=True)
    segment = models.ForeignKey(SegmentPage, related_name="quizzes", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Quiz for {self.chapter or self.segment}"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class ChapterProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(ChapterPage, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "chapter")


class CourseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(CoursePage, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "course")


class SegmentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    segment = models.ForeignKey(SegmentPage, on_delete=models.CASCADE)
    percent_watched = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "segment")
