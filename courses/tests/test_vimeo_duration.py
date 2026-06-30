"""
Tests for the Vimeo oEmbed auto-fetch feature (courses/models.py + signals.py).

Covers:
- Saving a video_url fetches duration, width, height, aspect_ratio from oEmbed
- The request uses maxwidth=3840 to get native video dimensions
- Changing video_url re-fetches; unchanged URL does not re-fetch
- API failure does not break the save
- Clearing video_url zeroes out all Vimeo-sourced fields
- CoursePage.duration_seconds is updated on every video_url change or clear
- Deleting a SegmentPage recalculates CoursePage.duration_seconds via post_delete signal

Page tree used by the `tree` fixture:

    Root
    └── Course
        └── Chapter
            ├── Segment A
            └── Segment B
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from wagtail.models import Page

from courses.models import CoursePage, ChapterPage, SegmentPage

pytestmark = pytest.mark.django_db

VIMEO_URL_A = "https://vimeo.com/1111111111"
VIMEO_URL_B = "https://vimeo.com/2222222222"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(duration=120, width=1920, height=1080):
    """Minimal Vimeo oEmbed response mock."""
    mock = MagicMock()
    mock.json.return_value = {"duration": duration, "width": width, "height": height}
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tree():
    """Course → Chapter → Segment A + Segment B, all without video URLs."""
    root = Page.get_first_root_node()

    course = CoursePage(title="Duration Test Course", live=True)
    root.add_child(instance=course)

    chapter = ChapterPage(title="Chapter 1", live=True)
    course.add_child(instance=chapter)

    seg_a = SegmentPage(title="Segment A", live=True)
    chapter.add_child(instance=seg_a)

    seg_b = SegmentPage(title="Segment B", live=True)
    chapter.add_child(instance=seg_b)

    return {
        "course": course.specific,
        "chapter": chapter.specific,
        "seg_a": seg_a.specific,
        "seg_b": seg_b.specific,
    }


# ---------------------------------------------------------------------------
# Tests: oEmbed field population
# ---------------------------------------------------------------------------

class TestVimeoFieldPopulation:
    """Fields are populated from the oEmbed response when video_url is set."""

    def test_setting_video_url_populates_duration(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            seg.video_url = VIMEO_URL_A
            seg.save()

        seg.refresh_from_db()
        assert seg.duration == timedelta(seconds=300)

    def test_setting_video_url_populates_width_and_height(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response(width=1920, height=1080)):
            seg.video_url = VIMEO_URL_A
            seg.save()

        seg.refresh_from_db()
        assert seg.width == 1920
        assert seg.height == 1080

    def test_aspect_ratio_calculated_from_oEmbed_dimensions(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response(width=1920, height=1080)):
            seg.video_url = VIMEO_URL_A
            seg.save()

        seg.refresh_from_db()
        assert seg.aspect_ratio == pytest.approx((1080 / 1920) * 100)

    def test_request_uses_maxwidth_3840(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response()) as mock_get:
            seg.video_url = VIMEO_URL_A
            seg.save()

        _, kwargs = mock_get.call_args
        assert kwargs.get("params", {}).get("maxwidth") == 3840

    def test_changing_video_url_re_fetches(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response(duration=100)):
            seg.video_url = VIMEO_URL_A
            seg.save()

        with patch("courses.models.requests.get", return_value=_mock_response(duration=200)):
            seg.video_url = VIMEO_URL_B
            seg.save()

        seg.refresh_from_db()
        assert seg.duration == timedelta(seconds=200)

    def test_saving_unchanged_video_url_does_not_call_vimeo(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response()):
            seg.video_url = VIMEO_URL_A
            seg.save()

        with patch("courses.models.requests.get") as mock_get:
            seg.save()  # same URL, no change

        mock_get.assert_not_called()

    def test_api_failure_does_not_break_save(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", side_effect=Exception("network error")):
            seg.video_url = VIMEO_URL_A
            seg.save()  # must not raise

        seg.refresh_from_db()
        assert seg.video_url == VIMEO_URL_A


# ---------------------------------------------------------------------------
# Tests: clearing video_url
# ---------------------------------------------------------------------------

class TestClearingVideoUrl:
    """Removing video_url zeroes out all Vimeo-sourced fields."""

    def test_clearing_video_url_clears_duration(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            seg.video_url = VIMEO_URL_A
            seg.save()

        seg.video_url = ""
        seg.save()
        seg.refresh_from_db()

        assert seg.duration is None

    def test_clearing_video_url_clears_width_and_height(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response(width=1920, height=1080)):
            seg.video_url = VIMEO_URL_A
            seg.save()

        seg.video_url = ""
        seg.save()
        seg.refresh_from_db()

        assert seg.width is None
        assert seg.height is None

    def test_clearing_video_url_resets_aspect_ratio_to_zero(self, tree):
        seg = tree["seg_a"]
        with patch("courses.models.requests.get", return_value=_mock_response()):
            seg.video_url = VIMEO_URL_A
            seg.save()

        seg.video_url = ""
        seg.save()
        seg.refresh_from_db()

        assert seg.aspect_ratio == 0


# ---------------------------------------------------------------------------
# Tests: CoursePage.duration_seconds updates
# ---------------------------------------------------------------------------

class TestCourseDurationUpdates:
    """CoursePage.duration_seconds stays in sync with its segments."""

    def test_setting_video_url_updates_course_total(self, tree):
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            tree["seg_a"].video_url = VIMEO_URL_A
            tree["seg_a"].save()

        tree["course"].refresh_from_db()
        assert tree["course"].duration_seconds == 300

    def test_two_segments_are_summed(self, tree):
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            tree["seg_a"].video_url = VIMEO_URL_A
            tree["seg_a"].save()

        with patch("courses.models.requests.get", return_value=_mock_response(duration=180)):
            tree["seg_b"].video_url = VIMEO_URL_B
            tree["seg_b"].save()

        tree["course"].refresh_from_db()
        assert tree["course"].duration_seconds == 480

    def test_clearing_video_url_reduces_course_total(self, tree):
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            tree["seg_a"].video_url = VIMEO_URL_A
            tree["seg_a"].save()

        with patch("courses.models.requests.get", return_value=_mock_response(duration=180)):
            tree["seg_b"].video_url = VIMEO_URL_B
            tree["seg_b"].save()

        tree["seg_a"].video_url = ""
        tree["seg_a"].save()

        tree["course"].refresh_from_db()
        assert tree["course"].duration_seconds == 180


# ---------------------------------------------------------------------------
# Tests: post_delete signal
# ---------------------------------------------------------------------------

class TestSegmentDeleteSignal:
    """Deleting a SegmentPage recalculates CoursePage.duration_seconds."""

    def test_deleting_segment_reduces_course_total(self, tree):
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            tree["seg_a"].video_url = VIMEO_URL_A
            tree["seg_a"].save()

        with patch("courses.models.requests.get", return_value=_mock_response(duration=180)):
            tree["seg_b"].video_url = VIMEO_URL_B
            tree["seg_b"].save()

        tree["seg_a"].delete()

        tree["course"].refresh_from_db()
        assert tree["course"].duration_seconds == 180

    def test_deleting_segment_without_duration_does_not_affect_total(self, tree):
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            tree["seg_a"].video_url = VIMEO_URL_A
            tree["seg_a"].save()

        # seg_b has no duration — deleting it should leave total unchanged
        tree["seg_b"].delete()

        tree["course"].refresh_from_db()
        assert tree["course"].duration_seconds == 300

    def test_deleting_all_segments_sets_total_to_zero(self, tree):
        with patch("courses.models.requests.get", return_value=_mock_response(duration=300)):
            tree["seg_a"].video_url = VIMEO_URL_A
            tree["seg_a"].save()

        tree["seg_a"].delete()
        tree["seg_b"].delete()

        tree["course"].refresh_from_db()
        assert tree["course"].duration_seconds == 0
