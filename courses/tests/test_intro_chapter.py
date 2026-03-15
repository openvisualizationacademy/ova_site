"""
Tests for is_intro chapter behaviour.

Intro chapters should:
- NOT count toward course completion percentage
- NOT block course completion (signal path)
- Still allow their segments to be marked as watched (100%)

Page tree used by the fixtures:

    Root
    └── Course
        ├── Intro Chapter  (is_intro=True)
        │   └── Intro Segment
        ├── Chapter 1
        │   └── Segment 1
        └── Chapter 2
            └── Segment 2
"""

import pytest
from django.test import RequestFactory
from wagtail.models import Page

from users.models import User
from courses.models import (
    CoursePage,
    ChapterPage,
    SegmentPage,
    SegmentProgress,
    ChapterProgress,
    CourseProgress,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user():
    return User.objects.create_user(email="intro@example.com", password=None)


@pytest.fixture
def course_with_intro():
    """Course with 1 intro chapter + 2 regular chapters, each with 1 segment."""
    root = Page.get_first_root_node()

    course = CoursePage(title="Intro Test Course")
    root.add_child(instance=course)
    course.save_revision().publish()

    intro_ch = ChapterPage(title="Introduction", is_intro=True)
    course.add_child(instance=intro_ch)
    intro_ch.save_revision().publish()

    intro_seg = SegmentPage(title="Welcome")
    intro_ch.add_child(instance=intro_seg)
    intro_seg.save_revision().publish()

    ch1 = ChapterPage(title="Chapter 1")
    course.add_child(instance=ch1)
    ch1.save_revision().publish()

    ch1_seg = SegmentPage(title="Segment 1")
    ch1.add_child(instance=ch1_seg)
    ch1_seg.save_revision().publish()

    ch2 = ChapterPage(title="Chapter 2")
    course.add_child(instance=ch2)
    ch2.save_revision().publish()

    ch2_seg = SegmentPage(title="Segment 2")
    ch2.add_child(instance=ch2_seg)
    ch2_seg.save_revision().publish()

    return {
        "course": course.specific,
        "intro_ch": intro_ch.specific,
        "intro_seg": intro_seg.specific,
        "ch1": ch1.specific,
        "ch1_seg": ch1_seg.specific,
        "ch2": ch2.specific,
        "ch2_seg": ch2_seg.specific,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _complete_segment(user, segment):
    sp, _ = SegmentProgress.objects.get_or_create(user=user, segment=segment)
    sp.percent_watched = 100
    sp.save()


def _get_context(user, segment):
    """Call get_context directly on the segment page, bypassing HTTP/templates."""
    factory = RequestFactory()
    request = factory.get("/fake-path/")
    request.user = user
    return segment.specific.get_context(request)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIntroExcludedFromProgress:
    """Intro chapters must not affect course completion percentage."""

    def test_completing_only_intro_gives_zero_percent(self, user, course_with_intro):
        """Watching the intro should leave course progress at 0%."""
        _complete_segment(user, course_with_intro["intro_seg"])

        ctx = _get_context(user, course_with_intro["ch1_seg"])
        assert ctx["course_percent_complete"] == 0

    def test_completing_one_regular_chapter_gives_50_percent(self, user, course_with_intro):
        """1 of 2 regular chapters done = 50%, not 33%."""
        _complete_segment(user, course_with_intro["ch1_seg"])

        ctx = _get_context(user, course_with_intro["ch1_seg"])
        assert ctx["course_percent_complete"] == 50

    def test_completing_all_regular_chapters_gives_100_percent(self, user, course_with_intro):
        """Both regular chapters done = 100%, regardless of intro."""
        _complete_segment(user, course_with_intro["ch1_seg"])
        _complete_segment(user, course_with_intro["ch2_seg"])

        ctx = _get_context(user, course_with_intro["ch1_seg"])
        assert ctx["course_percent_complete"] == 100


class TestIntroExcludedFromSignalCompletion:
    """The reconcile_progress signal should ignore intro chapters."""

    def test_course_completes_without_intro_watched(self, user, course_with_intro):
        """Course marked complete when all regular chapters are done, even if intro is unwatched."""
        _complete_segment(user, course_with_intro["ch1_seg"])
        _complete_segment(user, course_with_intro["ch2_seg"])

        assert CourseProgress.objects.filter(
            user=user, course=course_with_intro["course"], completed=True
        ).exists()

    def test_intro_alone_does_not_complete_course(self, user, course_with_intro):
        """Completing only the intro must NOT mark the course complete."""
        _complete_segment(user, course_with_intro["intro_seg"])

        assert not CourseProgress.objects.filter(
            user=user, course=course_with_intro["course"], completed=True
        ).exists()


class TestIntroSegmentStillTrackable:
    """Intro segments should still be individually trackable."""

    def test_intro_segment_can_reach_100(self, user, course_with_intro):
        """An intro segment's percent_watched should be stored as 100."""
        _complete_segment(user, course_with_intro["intro_seg"])

        sp = SegmentProgress.objects.get(user=user, segment=course_with_intro["intro_seg"])
        assert sp.percent_watched == 100

    def test_intro_chapter_progress_still_created(self, user, course_with_intro):
        """ChapterProgress for the intro chapter should still be created."""
        _complete_segment(user, course_with_intro["intro_seg"])

        assert ChapterProgress.objects.filter(
            user=user, chapter=course_with_intro["intro_ch"], completed=True
        ).exists()


class TestIntroFlagInContext:
    """The is_intro flag should be available in chapter_data context."""

    def test_chapter_data_contains_is_intro(self, user, course_with_intro):
        ctx = _get_context(user, course_with_intro["ch1_seg"])

        chapter_data = ctx["chapter_data"]
        intro_rows = [r for r in chapter_data if r["is_intro"]]
        regular_rows = [r for r in chapter_data if not r["is_intro"]]

        assert len(intro_rows) == 1
        assert len(regular_rows) == 2
        assert intro_rows[0]["chapter"].title == "Introduction"
