from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, Tag
from wagtail.models import Page, Orderable
from wagtail.fields import StreamField
from wagtail.blocks import RichTextBlock
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images import get_image_model
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtailmarkdown.blocks import MarkdownBlock
import re


User = get_user_model()


@register_snippet
class TagSnippet(Tag):
    class Meta:
        proxy = True
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


@register_snippet
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class InstructorsOrderable(Orderable):
    """This allows selection of one or more instructors for a course."""
    page = ParentalKey("courses.CoursePage", related_name="course_instructors")
    instructor = models.ForeignKey(
        "courses.Instructor",
        on_delete=models.CASCADE
    )

    panels = [
        FieldPanel("instructor"),
    ]


@register_snippet
class Instructor(models.Model):
    name = models.CharField(max_length=255)
    tagline = models.CharField(max_length=255, blank=True)
    bio = models.TextField()
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
    )
    social_links = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=False)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("role"),
                FieldPanel("image"),
            ],
            heading="Name and Role",
        ),
        MultiFieldPanel(
            [
                FieldPanel("tagline"),
                FieldPanel("bio"),
            ]
        ),
        MultiFieldPanel(
            [
                FieldPanel("social_links"),
            ],
            heading="Links",
        )
    ]

    def __str__(self):
        return self.name


class CourseCategoryTag(TaggedItemBase):
    content_object = ParentalKey(
        "courses.CoursePage",
        related_name="course_categories",
        on_delete=models.CASCADE,
    )


class CoursesIndexPage(Page):
    subpage_types = ['CoursePage']
    max_count = 1  # optional

    # def get_context(self, request, *args, **kwargs):
    #     context = super().get_context(request, *args, **kwargs)
    #     context["courses"] = self.get_children().live().specific()
    #     return context

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request)
        courses = self.get_children().live().specific()
        tags = set()
        for course in courses:
            for tag in course.tags.all():
                tags.add(str(tag))
        context['courses'] = courses

        # TODO: Consider sorting in order of importance
        context['all_tags'] = sorted(tags)
        return context


class CoursePage(Page):
    """Instructors are linked via InstructorsOrderable model to implement many to one."""
    content = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("markdown", MarkdownBlock()),
        ],
        use_json_field=True,
        blank=True,
        null=True,
    )
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tags = ClusterTaggableManager(through=CourseCategoryTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("content"),
        MultiFieldPanel(
            [
                InlinePanel("materials", label="Materials", max_num=5),
            ],
            heading="Downloadable Materials",
        ),
        MultiFieldPanel(
            [
                InlinePanel("course_instructors", label="Instructors", min_num=1, max_num=5),
            ],
            heading="Instructors",
        ),
        FieldPanel("tags"),
    ]

    # TODO: Add fields for:
    # duration (hours of video as int or float)
    # percentage (of completion, int or float from 0 to 100)
    # content_updated (manually updated, as date or string YYYY-MM or YYYY-MM-DD)

    parent_page_types = ['CoursesIndexPage']
    subpage_types = ["ChapterPage"]

    # Redirect to first segment of first chapter
    def serve(self, request):
        first_chapter = self.get_children().type(ChapterPage).live().first()
        
        if first_chapter:
            first_segment = first_chapter.specific.get_children().type(SegmentPage).live().first()
            
            if first_segment:
                return redirect(first_segment.specific.url)

        return super().serve(request)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Create alias, so the same template include can be used for course & segments pages
        context['course'] = self
        return context


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
    
    # TODO: Allow empty content

    content_panels = Page.content_panels + [
        FieldPanel("video_url"),
        FieldPanel("content"),
    ]

    # TODO: Add fields for completion, materials, video aspect ratio, and video duration

    parent_page_types = ["ChapterPage"]
    subpage_types = []

    def get_previous_segment(self):
        chapter = self.get_parent().specific

        previous = self.get_prev_siblings().live().first()
      
        if previous:
            return previous
        
        previous_chapter = chapter.get_prev_siblings().type(ChapterPage).live().first()
        
        if previous_chapter:
            return previous_chapter.specific.get_children().type(SegmentPage).live().last()
        
        return None
    
    def get_next_segment(self):
        chapter = self.get_parent().specific
        
        next_seg = self.get_next_siblings().live().first()
        
        if next_seg:
            return next_seg
        
        next_chapter = chapter.get_next_siblings().type(ChapterPage).live().first()
        
        if next_chapter:
            return next_chapter.specific.get_children().type(SegmentPage).live().first()
        
        return None

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Extract Vimeo id
        if self.video_url:
            match = re.search(r'vimeo\.com/(\d+)', self.video_url)
            context["vimeo_id"] = match.group(1) if match else None
        
        # Get the respective CoursePage
        chapter = self.get_parent()
        if chapter:
            course = chapter.get_parent()  # This is the CoursePage
            if course and isinstance(course.specific, CoursePage):
                context["course"] = course.specific

        # Create alias, so we can check if segment details exists in course include
        context['segment'] = self

        return context


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
