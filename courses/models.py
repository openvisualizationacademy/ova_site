from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.text import slugify
from django.utils import timezone
from django.shortcuts import render
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, Tag
from wagtail.models import Page, Orderable
from wagtail.fields import StreamField
from wagtail.blocks import RichTextBlock
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel
from wagtail.images import get_image_model
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtailmarkdown.blocks import MarkdownBlock
import re

from .mixins import QuizMixin

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
    instructor = models.ForeignKey("courses.Instructor", related_name="instructor_course", on_delete=models.CASCADE)

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
    role = models.ForeignKey("Role", on_delete=models.SET_NULL, null=True, blank=True)

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
        ),
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
    subpage_types = ["CoursePage"]
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
        context["courses"] = courses

        # TODO: Consider sorting in order of importance
        context["all_tags"] = sorted(tags)
        return context


class CourseMaterial(Orderable):
    page = ParentalKey(
        "courses.CoursePage", related_name="materials", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="course_materials/", blank=True, null=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return self.title


class ChapterMaterial(Orderable):
    page = ParentalKey(
        "courses.ChapterPage", related_name="materials", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="course_materials/", blank=True, null=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return self.title


class SegmentMaterial(Orderable):
    page = ParentalKey(
        "courses.SegmentPage", related_name="materials", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="course_materials/", blank=True, null=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return self.title


class CoursePage(Page):
    """Instructors are linked via InstructorsOrderable model to implement many to one."""

    duration = models.DurationField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

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
        FieldPanel("image"),
        FieldPanel("content"),
        MultiFieldPanel(
            [
                InlinePanel("materials", label="Materials"),
            ],
            heading="Course Materials",
        ),
        MultiFieldPanel(
            [
                InlinePanel(
                    "course_instructors", label="Instructors", min_num=1, max_num=5
                ),
            ],
            heading="Instructors",
        ),
        FieldPanel("tags"),
    ]

    parent_page_types = ["CoursesIndexPage"]
    subpage_types = ["ChapterPage"]

    def save(self, *args, **kwargs):
        # update slug to match title whenever it is changed
        self.slug = slugify(self.title)

        return super().save(*args, **kwargs)

    def get_all_materials(self):
        # 1. Course-level materials
        materials = list(self.materials.all())

        # 2. Chapter-level and segment-level materials
        chapters = self.get_children().type(ChapterPage).live().specific()

        for chapter in chapters:
            # Chapter materials
            materials.extend(chapter.materials.all())

            # Segment materials
            segments = chapter.get_children().type(SegmentPage).live().specific()
            for segment in segments:
                materials.extend(segment.materials.all())

        # 3. Remove duplicates while keeping order
        seen = set()
        deduped = []
        for mat in materials:
            if mat.id not in seen:
                deduped.append(mat)
                seen.add(mat.id)

        return deduped

    # Redirect to first segment of first chapter
    def serve(self, request):
        first_ch = self.get_children().type(ChapterPage).live().first()
        if first_ch:
            first_seg = first_ch.get_children().type(SegmentPage).live().first()
            if first_seg:
                return redirect(first_seg.url)

        # If no segments/chapters, fall back to normal view
        return super().serve(request)

    # Resolve URL to first segment of first chapter (that way no one ends up on the course page)
    # This "becomes" the url for the course
    def get_url(self, request=None, *args, **kwargs):
        # Get the first chapter
        first_ch = self.get_children().type(ChapterPage).live().specific().first()
        if not first_ch:
            return super().get_url(request, *args, **kwargs)

        # Get the first segment
        first_seg = first_ch.get_children().type(SegmentPage).live().specific().first()
        if not first_seg:
            return super().get_url(request, *args, **kwargs)

        # Return the segment URL instead
        return first_seg.get_url(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Needed for templates that expect 'course'
        context["course"] = self

        # Course-level materials
        context["course_materials"] = self.materials.all()

        return context


class ChapterPage(Page):
    content = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("markdown", MarkdownBlock()),
        ],
        use_json_field=True,
        blank=True,
        null=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("content"),
        MultiFieldPanel(
            [
                InlinePanel("materials", label="Materials"),
            ],
            heading="Chapter Materials",
        ),
    ]

    parent_page_types = ["CoursePage"]
    subpage_types = ["SegmentPage"]

    def save(self, *args, **kwargs):
        # update slug to match title whenever it is changed
        self.slug = slugify(self.title)

        return super().save(*args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        course = self.get_parent()
        course = course.specific if hasattr(course, "specific") else None
        context["course"] = course

        # Chapter materials
        context["chapter_materials"] = self.materials.all()

        # Course materials with EmptyQuerySet fallback
        context["course_materials"] = (
            course.materials.all()
            if course and hasattr(course, "materials")
            else CourseMaterial.objects.none()
        )

        return context


class SegmentPage(QuizMixin, Page):
    video_url = models.URLField(blank=True)
    duration = models.DurationField(blank=True, null=True)

    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    aspect_ratio = models.FloatField(editable=False, default=0)

    content = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("markdown", MarkdownBlock()),
        ],
        use_json_field=True,
        blank=True,
        null=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("video_url"),
        FieldRowPanel(
            [
                FieldPanel("width"),
                FieldPanel("height"),
                FieldPanel("aspect_ratio", read_only=True),
            ]
        ),
        MultiFieldPanel(
            [
                InlinePanel("materials", label="Materials"),
            ],
            heading="Segment Materials",
        ),
        FieldPanel("content"),
        InlinePanel("quizzes", label="Quizzes"),
    ]

    parent_page_types = ["ChapterPage"]
    subpage_types = []

    def _get_adjacent_segment(self, direction):
        """
        Internal helper to get the next or previous segment.
        direction: "next" or "previous"
        """

        if direction not in ("next", "previous"):
            raise ValueError("direction must be 'next' or 'previous'")

        # Select the correct sibling lookup
        sibling_lookup = (
            self.get_next_siblings().live().specific()
            if direction == "next"
            else self.get_prev_siblings().live().specific()
        )

        # 1. Try sibling segments
        sibling = sibling_lookup.first()
        if sibling:
            return sibling

        # 2. No siblings -> look in next/previous chapter
        chapter = self.get_parent().specific

        chapter_lookup = (
            chapter.get_next_siblings().type(ChapterPage).live().specific()
            if direction == "next"
            else chapter.get_prev_siblings().type(ChapterPage).live().specific()
        )

        adjacent_chapter = chapter_lookup.first()
        if not adjacent_chapter:
            return None

        # 3. Select first/last segment of that chapter
        segment_lookup = (
            adjacent_chapter.get_children().type(SegmentPage).live().specific()
        )

        return segment_lookup.first() if direction == "next" else segment_lookup.last()

    def get_next_segment(self):
        return self._get_adjacent_segment("next")

    def get_previous_segment(self):
        return self._get_adjacent_segment("previous")

    def save(self, *args, **kwargs):
        # update slug to match title whenever it is changed
        self.slug = slugify(self.title)

        # auto calculate aspect ratio
        if self.width and self.height:
            self.aspect_ratio = (self.height / self.width) * 100
        else:
            self.aspect_ratio = 0

        return super().save(*args, **kwargs)

    def serve(self, request):
        # POST always wins
        if request.method == "POST":
            return self.handle_quiz_submission(request)

        context = self.get_context(request)

        hydrated = self.hydrate_quiz_from_progress(request)
        if hydrated:
            context.update(hydrated)

        return render(request, self.get_template(request), context)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Vimeo
        if self.video_url:
            match = re.search(r"vimeo\.com/(\d+)", self.video_url)
            context["vimeo_id"] = match.group(1) if match else None

        # Parent chapter
        chapter = self.get_parent()
        context["chapter"] = chapter

        # Parent course
        course = None
        if chapter:
            parent_course = chapter.get_parent()
            if parent_course and hasattr(parent_course, "specific"):
                course = parent_course.specific
        context["course"] = course

        # Chapter number
        if chapter:
            context["chapter_number"] = (
                chapter.get_siblings(inclusive=True)
                .live()
                .filter(path__lt=chapter.path)
                .count()
                + 1
            )
        else:
            context["chapter_number"] = None

        # Segment number
        context["segment_number"] = (
            self.get_siblings(inclusive=True).live().filter(path__lt=self.path).count()
            + 1
        )

        # Get only first quiz
        context["quiz"] = self.get_quiz()

        # ---------------------------------------
        # MATERIALS
        # For current segment, chapter & course
        # ---------------------------------------
        context["segment_materials"] = self.materials.all()

        # Template still expects these keys so they must exist
        from .models import ChapterMaterial, CourseMaterial

        context["chapter_materials"] = (
            chapter.materials.all()
            if chapter and hasattr(chapter, "materials")
            else ChapterMaterial.objects.none()
        )
        context["course_materials"] = (
            course.materials.all()
            if course and hasattr(course, "materials")
            else CourseMaterial.objects.none()
        )

        # Alias for template
        context["segment"] = self

        user = request.user
        # Defaults for anonymous users
        context["segment_progress"] = None
        context["chapter_progress"] = None
        context["course_progress"] = None
        context["segments_in_chapter"] = []
        context["segments_progress_list"] = []
        context["chapters_in_course"] = []
        context["chapters_progress_list"] = []
        context["chapter_percent_complete"] = 0
        context["course_percent_complete"] = 0
        if user.is_authenticated:

            # -----------------------------
            # 1. Current segment progress
            # -----------------------------
            seg_prog = (
                SegmentProgress.objects.filter(user=user, segment=self)
                .values_list("percent_watched", flat=True)
                .first()
            )

            context["segment_progress"] = 0 if seg_prog is None else seg_prog

            chapter = context.get("chapter")
            course = context.get("course")

            # -----------------------------
            # 2. All segments in chapter
            # -----------------------------
            if chapter:
                segments = chapter.get_children().type(SegmentPage).live().specific()
                context["segments_in_chapter"] = segments

                # Get user progress for these segments
                seg_progress_map = {
                    p.segment_id: p
                    for p in SegmentProgress.objects.filter(
                        user=user, segment__in=segments
                    )
                }

                # List aligned with segments
                seg_progress_list = []
                completed_count = 0

                for s in segments:
                    p = seg_progress_map.get(s.id)
                    seg_progress_list.append(p)
                    if p and getattr(p, "completed", False):
                        completed_count += 1

                context["segments_progress_list"] = seg_progress_list

                # Percent chapter completion
                total_segments = segments.count()
                if total_segments > 0:
                    context["chapter_percent_complete"] = int(
                        (completed_count / total_segments) * 100
                    )

                # Current chapter progress object
                chap_prog = (
                    ChapterProgress.objects.filter(user=user, chapter=chapter)
                    .values_list("completed", flat=True)
                    .first()
                )
                context["chapter_progress"] = chap_prog

            # -----------------------------
            # 3. All chapters in course
            # -----------------------------
            if course:
                chapters = course.get_children().type(ChapterPage).live().specific()
                context["chapters_in_course"] = chapters

                chap_progress_map = {
                    p.chapter_id: p
                    for p in ChapterProgress.objects.filter(
                        user=user, chapter__in=chapters
                    )
                }

                chap_progress_list = []
                completed_chapters = 0

                for ch in chapters:
                    p = chap_progress_map.get(ch.id)
                    chap_progress_list.append(p)
                    if p and p.completed:
                        completed_chapters += 1

                context["chapters_progress_list"] = chap_progress_list

                total_chapters = chapters.count()
                if total_chapters > 0:
                    context["course_percent_complete"] = int(
                        (completed_chapters / total_chapters) * 100
                    )

                # Current course progress object
                course_prog = (
                    CourseProgress.objects.filter(user=user, course=course)
                    .values_list("completed", flat=True)
                    .first()
                )
                context["course_progress"] = course_prog

        return context


class Quiz(ClusterableModel):
    title = models.CharField(max_length=255, blank=True)
    segment = ParentalKey(
        SegmentPage,
        related_name="quizzes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    panels = [
        FieldPanel("title"),
        InlinePanel("questions", label="Questions"),
    ]

    def __str__(self):
        return f"Quiz for {self.segment}"


class Question(ClusterableModel):
    quiz = ParentalKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    text = models.TextField()

    panels = [
        FieldPanel("text"),
        InlinePanel("choices", label="Choices"),
    ]

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = ParentalKey("Question", related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    panels = [
        FieldPanel("text"),
        FieldPanel("is_correct"),
    ]

    def __str__(self):
        return self.text


class ChapterProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(ChapterPage, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "chapter")

    def __str__(self):
        return f"{self.user} completed {self.chapter}: {self.completed}"


class CourseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(CoursePage, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} completed {self.course}: {self.completed}"


class SegmentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    segment = models.ForeignKey(SegmentPage, on_delete=models.CASCADE)
    percent_watched = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "segment")

    def __str__(self):
        return f"{self.user} watched {self.segment}: {self.percent_watched}%"


class QuizProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    answers_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("user", "quiz")
