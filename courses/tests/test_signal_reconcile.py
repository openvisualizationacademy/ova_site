"""
Tests for the reconcile_progress signal (courses/signals.py).

These tests verify that saving a SegmentProgress record directly (without
going through the API endpoint) still triggers chapter and course completion.
This is the core value of the signal — progress reconciliation happens
regardless of how SegmentProgress is updated.

Page tree used by the course_tree fixture:

    Root
    └── Course
        ├── Chapter 1
        │   ├── Segment 1-1
        │   ├── Segment 1-2
        │   └── Segment 1-3
        └── Chapter 2
            ├── Segment 2-1
            ├── Segment 2-2
            └── Segment 2-3
"""

import pytest
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
    return User.objects.create_user(email="signal@example.com", password=None)


@pytest.fixture
def course_tree():
    """Build a course with 2 chapters × 3 segments each."""
    root = Page.get_first_root_node()

    course = CoursePage(title="Signal Test Course")
    root.add_child(instance=course)
    course.save_revision().publish()

    ch1 = ChapterPage(title="Chapter 1")
    course.add_child(instance=ch1)
    ch1.save_revision().publish()

    ch1_segs = []
    for i in range(1, 4):
        seg = SegmentPage(title=f"Segment 1-{i}")
        ch1.add_child(instance=seg)
        seg.save_revision().publish()
        ch1_segs.append(seg)

    ch2 = ChapterPage(title="Chapter 2")
    course.add_child(instance=ch2)
    ch2.save_revision().publish()

    ch2_segs = []
    for i in range(1, 4):
        seg = SegmentPage(title=f"Segment 2-{i}")
        ch2.add_child(instance=seg)
        seg.save_revision().publish()
        ch2_segs.append(seg)

    return {
        "course": course.specific,
        "ch1": ch1.specific,
        "ch2": ch2.specific,
        "ch1_segs": [s.specific for s in ch1_segs],
        "ch2_segs": [s.specific for s in ch2_segs],
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _complete_segment(user, segment):
    """Save SegmentProgress at 100% — triggers the reconcile signal."""
    sp, _ = SegmentProgress.objects.get_or_create(user=user, segment=segment)
    sp.percent_watched = 100
    sp.save()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChapterCompletion:
    """Chapter should only be marked complete when ALL its segments are at 100%."""

    def test_partial_chapter_not_complete(self, user, course_tree):
        """Completing 2 of 3 segments should NOT mark chapter complete."""
        segs = course_tree["ch1_segs"]
        _complete_segment(user, segs[0])
        _complete_segment(user, segs[1])

        assert not ChapterProgress.objects.filter(
            user=user, chapter=course_tree["ch1"], completed=True
        ).exists()

    def test_chapter_complete_when_all_segments_done(self, user, course_tree):
        """Completing all 3 segments should mark the chapter complete."""
        for seg in course_tree["ch1_segs"]:
            _complete_segment(user, seg)

        cp = ChapterProgress.objects.get(user=user, chapter=course_tree["ch1"])
        assert cp.completed is True
        assert cp.completed_at is not None

    def test_99_percent_does_not_complete_chapter(self, user, course_tree):
        """Segments at 99% should NOT count as complete."""
        for seg in course_tree["ch1_segs"]:
            sp, _ = SegmentProgress.objects.get_or_create(user=user, segment=seg)
            sp.percent_watched = 99
            sp.save()

        assert not ChapterProgress.objects.filter(
            user=user, chapter=course_tree["ch1"], completed=True
        ).exists()


class TestCourseCompletion:
    """Course should only be marked complete when ALL chapters are complete."""

    def test_one_chapter_done_does_not_complete_course(self, user, course_tree):
        """Completing chapter 1 alone should NOT mark the course complete."""
        for seg in course_tree["ch1_segs"]:
            _complete_segment(user, seg)

        assert not CourseProgress.objects.filter(
            user=user, course=course_tree["course"], completed=True
        ).exists()

    def test_course_complete_when_all_chapters_done(self, user, course_tree):
        """Completing all segments in both chapters should mark the course complete."""
        for seg in course_tree["ch1_segs"] + course_tree["ch2_segs"]:
            _complete_segment(user, seg)

        cprog = CourseProgress.objects.get(user=user, course=course_tree["course"])
        assert cprog.completed is True
        assert cprog.completed_at is not None


class TestSignalIdempotency:
    """Signal should be safe to fire multiple times on the same data."""

    def test_no_duplicate_chapter_progress(self, user, course_tree):
        """Saving the same segment twice should not create duplicate records."""
        for seg in course_tree["ch1_segs"]:
            _complete_segment(user, seg)

        # Fire again
        _complete_segment(user, course_tree["ch1_segs"][0])

        assert ChapterProgress.objects.filter(
            user=user, chapter=course_tree["ch1"]
        ).count() == 1

    def test_no_duplicate_course_progress(self, user, course_tree):
        """Saving a segment again after course is complete should not duplicate."""
        for seg in course_tree["ch1_segs"] + course_tree["ch2_segs"]:
            _complete_segment(user, seg)

        _complete_segment(user, course_tree["ch2_segs"][2])

        assert CourseProgress.objects.filter(
            user=user, course=course_tree["course"]
        ).count() == 1

    def test_completed_at_does_not_change_on_refire(self, user, course_tree):
        """Re-saving a 100% segment should not update the completion timestamp."""
        for seg in course_tree["ch1_segs"]:
            _complete_segment(user, seg)

        cp = ChapterProgress.objects.get(user=user, chapter=course_tree["ch1"])
        original_ts = cp.completed_at

        _complete_segment(user, course_tree["ch1_segs"][0])

        cp.refresh_from_db()
        assert cp.completed_at == original_ts
