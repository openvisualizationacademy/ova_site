from django.db import models
from django.db.models import Prefetch
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
    instructor = models.ForeignKey(
        "courses.Instructor", related_name="instructor_course", on_delete=models.CASCADE
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
        user = request.user

        # Build the complete queryset with all prefetches
        courses_query = self.get_children().live().specific().prefetch_related(
            'tags',
            'course_instructors__instructor',
            'course_instructors__instructor__image',
            'image',  # Prefetch course images
        )

        # Add progress prefetch for authenticated users
        if user.is_authenticated:
            progress_queryset = CourseProgress.objects.filter(user=user)
            courses_query = courses_query.prefetch_related(
                Prefetch(
                    'courseprogress_set',
                    queryset=progress_queryset,
                    to_attr='progress'
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

        context['courses'] = courses

        # Sort tags by importance
        def custom_sorted(input_list):
            # Define ideal sorting of tags (in order of importance)
            ideal_order = ["Fundamentals", "Lecture", "Tutorial"]

            # Result: {"Fundamentals": 0, "Lecture": 1, "Tutorial": 2}
            rank_map = {word: i for i, word in enumerate(ideal_order)}

            # Compare based on rank instead of alphabetically, unknown words go to the end
            return sorted(input_list, key=lambda x: rank_map.get(x, float('inf')))

        context['all_tags'] = sorted(tags)
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
    duration_seconds = models.PositiveIntegerField(blank=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    # Coming Soon feature
    coming_soon = models.TextField(
        blank=True,
        null=True,
        help_text="If set, this course is marked as 'Coming Soon'. Enter estimated release date (e.g., 'Spring 2026', 'March 2026'). Leave empty to make course publicly available."
    )
    allowed_emails = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated list of email addresses allowed to access this course while it's coming soon. Staff and superusers always have access."
    )

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
        FieldRowPanel(
            [
                FieldPanel("image"),
                FieldPanel("duration_seconds", help_text="duration in seconds"),
                FieldPanel("updated_on"),
            ]
        ),
        FieldPanel("content"),
        MultiFieldPanel(
            [
                FieldPanel("coming_soon"),
                FieldPanel("allowed_emails"),
            ],
            heading="Coming Soon Settings",
        ),
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

    @property
    def sorted_tags(self):

        # Get all tags - data already loaded
        tags = set()
        for tag in self.tags.all():
            tags.add(str(tag))

        # Sort tags by importance
        def custom_sorted(input_list):
            # Define ideal sorting of tags (in order of importance)
            ideal_order = ["Fundamentals", "Lecture", "Tutorial"]

            # Result: {"Fundamentals": 0, "Lecture": 1, "Tutorial": 2}
            rank_map = {word: i for i, word in enumerate(ideal_order)}

            # Compare based on rank instead of alphabetically, unknown words go to the end
            return sorted(input_list, key=lambda x: rank_map.get(x, float('inf')))

        return custom_sorted(tags)

    @property
    def formatted_duration(self):
        if not self.duration_seconds:
            return None

        # Round to nearest 30 minutes
        steps = 30
        interval = steps * 60
        rounded_seconds = interval * round(self.duration_seconds / interval)
        
        # Calculate hours and minutes
        hours = rounded_seconds // 3600
        minutes = (rounded_seconds % 3600) // 60

        # Build string like 2h, 1h30, or 30min
        text = ""
        if hours > 0:
            text += f"{hours}h"
        if minutes > 0:
            text += f"{minutes}"
            if not hours > 0:
                text += "min"
            
        return text

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

    def user_has_access(self, user):
        """Check if a user has access to this coming soon course."""
        # If course is not coming soon, everyone has access
        if not self.coming_soon:
            return True

        # Staff and superusers always have access
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return True

        # Check if user's email is in the allowed list
        if user.is_authenticated and self.allowed_emails:
            allowed_list = [email.strip().lower() for email in self.allowed_emails.split(',') if email.strip()]
            if user.email.lower() in allowed_list:
                return True

        # No access
        return False

    # Redirect to first segment of first chapter
    def serve(self, request):
        # Check coming soon access restrictions
        if not self.user_has_access(request.user):
            return render(request, 'courses/coming_soon.html', {
                'page': self,
                'course': self,
                'estimated_release': self.coming_soon,
            }, status=403)
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

    def serve(self, request):
        # Check parent course's coming soon restrictions
        course = self.get_parent().specific
        if hasattr(course, 'user_has_access') and not course.user_has_access(request.user):
            return render(request, 'courses/coming_soon.html', {
                'page': self,
                'course': course,
                'estimated_release': course.coming_soon,
            }, status=403)

        return super().serve(request)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        course = self.get_parent()
        course = course.specific if hasattr(course, "specific") else None
        context["course"] = course

        # Segments in this chapter (preloaded to avoid query in template)
        context["segments"] = self.get_children().live().specific()

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
        # Check parent course's coming soon restrictions
        chapter = self.get_parent()
        if chapter:
            course = chapter.get_parent()
            if course and hasattr(course, 'specific'):
                course = course.specific
                if hasattr(course, 'user_has_access') and not course.user_has_access(request.user):
                    return render(request, 'courses/coming_soon.html', {
                        'page': self,
                        'course': course,
                        'estimated_release': course.coming_soon,
                    }, status=403)

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

        # Get chapters and segments (to be used for both anonymous and signed in users)
        # Use select_related for content_type to reduce queries from .specific()
        chapters = (
            course.get_children()
            .type(ChapterPage)
            .live()
            .select_related('content_type')
            .specific()
        )

        # Prefetch all segments once with their quizzes
        all_segments = (
            SegmentPage.objects.filter(path__startswith=course.path)
            .live()
            .select_related('content_type')
            .specific()
            .prefetch_related('quizzes')
        )

        # Build quiz lookup map early so we can use it for current segment too
        from courses.models import Quiz
        quiz_map = {}
        all_quiz_list = list(Quiz.objects.filter(segment__in=all_segments).select_related('segment'))
        for quiz in all_quiz_list:
            if quiz.segment_id not in quiz_map:
                quiz_map[quiz.segment_id] = quiz

        # Get quiz for current segment from the map (no extra query)
        context["quiz"] = quiz_map.get(self.id)

        # Calculate segment and chapter numbers using cached data to avoid COUNT queries
        # Segment number within chapter
        segments_in_chapter = [s for s in all_segments if s.path.startswith(chapter.path) and s.path != chapter.path]
        segments_in_chapter_sorted = sorted(segments_in_chapter, key=lambda s: s.path)
        segment_number = 1
        for idx, seg in enumerate(segments_in_chapter_sorted, 1):
            if seg.id == self.id:
                segment_number = idx
                break
        context["segment_number"] = segment_number

        # Chapter number within course
        if chapter:
            chapters_sorted = sorted(chapters, key=lambda c: c.path)
            chapter_number = 1
            for idx, ch in enumerate(chapters_sorted, 1):
                if ch.id == chapter.id:
                    chapter_number = idx
                    break
            context["chapter_number"] = chapter_number
        else:
            context["chapter_number"] = None

        # Build a mapping of chapter_id -> segments to avoid get_parent() calls
        segments_by_chapter = {}

        for segment in all_segments:
            # Use path-based parent detection to avoid query
            # Segment path is like '000100020001000200010001', chapter is parent
            chapter_path = segment.path[:-4]  # Remove last 4 chars to get parent path
            # Find chapter by matching path
            for chapter in chapters:
                if chapter.path == chapter_path:
                    if chapter.id not in segments_by_chapter:
                        segments_by_chapter[chapter.id] = []
                    segments_by_chapter[chapter.id].append(segment)
                    break

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
            # Chapters + segments + progress
            # -----------------------------

            context["chapters_in_course"] = chapters
            context["chapter_data"] = []

            # Segment progress lookup
            segment_progress_map = {
                p.segment_id: p
                for p in SegmentProgress.objects.filter(
                    user=user,
                    segment__in=all_segments,
                )
            }

            # Chapter progress lookup
            chapter_progress_map = {
                p.chapter_id: p
                for p in ChapterProgress.objects.filter(
                    user=user,
                    chapter__in=chapters,
                )
            }

            completed_chapters = 0

            for chapter in chapters:
                segments = segments_by_chapter.get(chapter.id, [])

                completed_segments = 0
                segment_rows = []

                for segment in segments:
                    prog = segment_progress_map.get(segment.id)
                    is_complete = prog and prog.percent_watched >= 100

                    if is_complete:
                        completed_segments += 1

                    # Get quiz from prebuilt map - no database query
                    quiz = quiz_map.get(segment.id)

                    segment_rows.append(
                        {
                            "segment": segment,
                            "progress": prog,
                            "completed": is_complete,
                            "quiz": quiz,
                        }
                    )

                chapter_complete = (
                    completed_segments == len(segments) and len(segments) > 0
                )

                if chapter_complete:
                    completed_chapters += 1

                context["chapter_data"].append(
                    {
                        "chapter": chapter,
                        "segments": segment_rows,
                        "completed": chapter_complete,
                        "percent_complete": (
                            int((completed_segments / len(segments)) * 100)
                            if segments
                            else 0
                        ),
                    }
                )

            # Course percent
            if chapters:
                context["course_percent_complete"] = int(
                    (completed_chapters / chapters.count()) * 100
                )
        else:

            # For anonymous users, provide simpler list of chapters and segments

            context["chapter_data"] = []

            for chapter in chapters:
                segments = segments_by_chapter.get(chapter.id, [])
                segment_rows = []
                for segment in segments:
                    # Get quiz from prebuilt map - no database query
                    quiz = quiz_map.get(segment.id)

                    segment_rows.append(
                        {
                            "segment": segment,
                            "quiz": quiz,
                        }
                    )

                context["chapter_data"].append(
                    {"chapter": chapter, "segments": segment_rows}
                )

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
