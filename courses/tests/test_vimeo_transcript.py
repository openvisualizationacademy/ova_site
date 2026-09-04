"""
Tests for the Vimeo transcript fetch feature (courses/models.py + admin.py).

Covers:
- _vtt_to_cues parses WebVTT into a flat list of {timestamp, text} cues
- _cues_to_sentences re-segments the cue stream into sentence spans
- _group_cues_into_paragraphs chunks those sentences into fixed-size paragraphs
- SegmentPage._refresh_vimeo_transcript fetches, parses, groups, and persists
- The transcript fetch is never triggered from save() -- it's admin-action only
- get_context exposes the stored transcript under the "transcript" key
- The two Django admin actions call _refresh_vimeo_transcript for the right segments

Page tree used by the `tree` fixture:

    Root
    └── Course
        └── Chapter
            ├── Segment A
            └── Segment B
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from django.contrib.auth.models import AnonymousUser
from wagtail.models import Page

from courses.admin import fetch_missing_transcripts, redownload_transcript
from courses.models import (
    CoursePage,
    ChapterPage,
    SegmentPage,
    _cues_to_sentences,
    _group_cues_into_paragraphs,
    _vtt_to_cues,
)

pytestmark = pytest.mark.django_db

VIMEO_URL_A = "https://vimeo.com/1111111111"
VIMEO_URL_B = "https://vimeo.com/2222222222"

SAMPLE_VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.000
There were, at the time, some researchers

2
00:00:04.000 --> 00:00:07.000
and doctors who had begun doubting the theory. One

3
00:00:14.000 --> 00:00:18.000
of them was Dr. John Snow, who is also quite

4
00:00:18.000 --> 00:00:22.000
famous because of this map. He plotted the

5
00:00:22.000 --> 00:00:26.000
cholera deaths street by street. What did that

6
00:00:26.000 --> 00:00:30.000
reveal? A single contaminated water pump.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_texttracks_response(link="https://example.com/transcript.vtt"):
    mock = MagicMock()
    mock.json.return_value = {"data": [{"link": link}]}
    return mock


def _mock_vtt_response(text=SAMPLE_VTT):
    mock = MagicMock()
    mock.text = text
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tree():
    """Course → Chapter → Segment A + Segment B, all without video URLs."""
    root = Page.get_first_root_node()

    course = CoursePage(title="Transcript Test Course", live=True)
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
# Tests: _vtt_to_cues
# ---------------------------------------------------------------------------


class TestVttToCues:
    def test_parses_cue_count_and_order(self):
        cues = _vtt_to_cues(SAMPLE_VTT)
        assert len(cues) == 6
        assert cues[0] == {
            "timestamp": "00:01",
            "text": "There were, at the time, some researchers",
        }
        assert cues[2] == {
            "timestamp": "00:14",
            "text": "of them was Dr. John Snow, who is also quite",
        }

    def test_excludes_header_index_and_timing_lines(self):
        cues = _vtt_to_cues(SAMPLE_VTT)
        texts = [c["text"] for c in cues]
        assert not any("WEBVTT" in t for t in texts)
        assert not any("-->" in t for t in texts)
        assert "1" not in texts and "2" not in texts

    def test_strips_inline_tags(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:02.000\n"
            "<v Speaker>Hello <c.colorE5E5E5>world</c></v>\n"
        )
        cues = _vtt_to_cues(vtt)
        assert cues == [{"timestamp": "00:01", "text": "Hello world"}]

    def test_joins_multiline_cue_text(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:02.000\n"
            "First line\n"
            "second line\n"
        )
        cues = _vtt_to_cues(vtt)
        assert cues == [{"timestamp": "00:01", "text": "First line second line"}]

    def test_formats_hours_into_mmss(self):
        vtt = "WEBVTT\n\n" "01:02:03.000 --> 01:02:05.000\n" "An hour and change in\n"
        cues = _vtt_to_cues(vtt)
        assert cues[0]["timestamp"] == "62:03"


# ---------------------------------------------------------------------------
# Tests: _cues_to_sentences
# ---------------------------------------------------------------------------


class TestCuesToSentences:
    def test_joins_cues_and_splits_on_sentence_punctuation(self):
        sentences = _cues_to_sentences(_vtt_to_cues(SAMPLE_VTT))
        assert [s["text"] for s in sentences] == [
            "There were, at the time, some researchers and doctors "
            "who had begun doubting the theory.",
            "One of them was Dr. John Snow, who is also quite "
            "famous because of this map.",
            "He plotted the cholera deaths street by street.",
            "What did that reveal?",
            "A single contaminated water pump.",
        ]

    def test_sentence_keeps_timestamp_of_the_cue_it_starts_in(self):
        sentences = _cues_to_sentences(_vtt_to_cues(SAMPLE_VTT))
        assert sentences[0]["timestamp"] == "00:01"
        # "One of them..." begins in cue 2 (00:04)
        assert sentences[1]["timestamp"] == "00:04"
        # "He plotted..." begins in cue 4 (00:18)
        assert sentences[2]["timestamp"] == "00:18"

    def test_abbreviation_does_not_end_a_sentence(self):
        sentences = _cues_to_sentences(
            [
                {"timestamp": "00:01", "text": "We spoke to Dr."},
                {"timestamp": "00:04", "text": "John Snow about the outbreak."},
            ]
        )
        assert sentences == [
            {
                "timestamp": "00:01",
                "text": "We spoke to Dr. John Snow about the outbreak.",
            }
        ]

    def test_single_letter_initial_does_not_end_a_sentence(self):
        sentences = _cues_to_sentences(
            [{"timestamp": "00:01", "text": "It was named for J. Snow himself."}]
        )
        assert sentences == [
            {"timestamp": "00:01", "text": "It was named for J. Snow himself."}
        ]

    def test_unpunctuated_stream_stays_one_sentence(self):
        sentences = _cues_to_sentences(
            [
                {"timestamp": "00:01", "text": "no punctuation here at all"},
                {"timestamp": "00:04", "text": "just an endless run of words"},
            ]
        )
        assert sentences == [
            {
                "timestamp": "00:01",
                "text": "no punctuation here at all just an endless run of words",
            }
        ]

    def test_empty_list_returns_empty(self):
        assert _cues_to_sentences([]) == []


# ---------------------------------------------------------------------------
# Tests: _group_cues_into_paragraphs
# ---------------------------------------------------------------------------


class TestGroupCuesIntoParagraphs:
    def test_chunks_sentences_four_per_paragraph(self):
        cues = [
            {"timestamp": f"00:0{i}", "text": f"Sentence number {i}."}
            for i in range(1, 7)
        ]
        paragraphs = _group_cues_into_paragraphs(cues)
        assert [len(p) for p in paragraphs] == [4, 2]
        assert paragraphs[0][0]["text"] == "Sentence number 1."
        assert paragraphs[1][0]["text"] == "Sentence number 5."

    def test_sample_vtt_groups_into_sentence_spans(self):
        paragraphs = _group_cues_into_paragraphs(_vtt_to_cues(SAMPLE_VTT))
        # 5 sentences, 4 per paragraph -> 2 paragraphs
        assert [len(p) for p in paragraphs] == [4, 1]
        assert paragraphs[0][0]["text"].startswith("There were, at the time")
        assert paragraphs[1][0] == {
            "timestamp": "00:26",
            "text": "A single contaminated water pump.",
        }

    def test_empty_list_returns_empty(self):
        assert _group_cues_into_paragraphs([]) == []


# ---------------------------------------------------------------------------
# Tests: real caption track
# ---------------------------------------------------------------------------


class TestRealTranscriptShape:
    """Guard against regressions using a real Vimeo-style auto-caption track."""

    VTT_PATH = (
        Path(__file__).resolve().parents[2]
        / "ova"
        / "static"
        / "media"
        / "videos"
        / "intro-en.vtt"
    )

    def test_intro_vtt_groups_into_readable_paragraphs(self):
        cues = _vtt_to_cues(self.VTT_PATH.read_text(encoding="utf-8"))
        paragraphs = _group_cues_into_paragraphs(cues)

        assert len(paragraphs) > 1
        assert all(1 <= len(p) <= 4 for p in paragraphs)

        spans = [s for p in paragraphs for s in p]
        # every sentence but the last ends on terminal punctuation
        assert all(s["text"].rstrip("\"')]")[-1] in ".?!…" for s in spans[:-1])
        # no span is a bare fragment
        assert all(len(s["text"].split()) >= 3 for s in spans)


class TestRefreshVimeoTranscript:
    def test_successful_fetch_populates_transcript(self, tree, settings):
        settings.VIMEO_ACCESS_TOKEN = "test-token"
        seg = tree["seg_a"]
        seg.video_url = VIMEO_URL_A
        seg.save()

        with patch(
            "courses.models.requests.get",
            side_effect=[_mock_texttracks_response(), _mock_vtt_response()],
        ):
            result = seg._refresh_vimeo_transcript()

        assert result is True
        seg.refresh_from_db()
        assert seg.transcript == _group_cues_into_paragraphs(_vtt_to_cues(SAMPLE_VTT))

    def test_missing_access_token_skips_gracefully(self, tree, settings):
        settings.VIMEO_ACCESS_TOKEN = None
        seg = tree["seg_a"]
        seg.video_url = VIMEO_URL_A
        seg.save()

        with patch("courses.models.requests.get") as mock_get:
            result = seg._refresh_vimeo_transcript()

        mock_get.assert_not_called()
        assert result is False
        seg.refresh_from_db()
        assert seg.transcript == []

    def test_empty_texttracks_response_returns_false(self, tree, settings):
        settings.VIMEO_ACCESS_TOKEN = "test-token"
        seg = tree["seg_a"]
        seg.video_url = VIMEO_URL_A
        seg.save()

        empty_response = MagicMock()
        empty_response.json.return_value = {"data": []}
        with patch("courses.models.requests.get", return_value=empty_response):
            result = seg._refresh_vimeo_transcript()

        assert result is False
        seg.refresh_from_db()
        assert seg.transcript == []

    def test_network_failure_does_not_raise(self, tree, settings):
        settings.VIMEO_ACCESS_TOKEN = "test-token"
        seg = tree["seg_a"]
        seg.video_url = VIMEO_URL_A
        seg.save()

        with patch(
            "courses.models.requests.get", side_effect=Exception("network error")
        ):
            result = seg._refresh_vimeo_transcript()  # must not raise

        assert result is False

    def test_saving_video_url_does_not_trigger_transcript_fetch(self, tree, settings):
        settings.VIMEO_ACCESS_TOKEN = "test-token"
        seg = tree["seg_a"]

        with patch("courses.models.requests.get", return_value=MagicMock()) as mock_get:
            mock_get.return_value.json.return_value = {
                "duration": 120,
                "width": 1920,
                "height": 1080,
            }
            seg.video_url = VIMEO_URL_A
            seg.save()

        # Only the oEmbed call should have happened, never texttracks.
        called_urls = [call.args[0] for call in mock_get.call_args_list]
        assert all("texttracks" not in url for url in called_urls)


# ---------------------------------------------------------------------------
# Tests: get_context
# ---------------------------------------------------------------------------


class TestGetContext:
    def test_context_exposes_stored_transcript(self, tree, rf):
        seg = tree["seg_a"]
        seg.transcript = [[{"timestamp": "00:01", "text": "Hello."}]]
        seg.save()

        request = rf.get("/")
        request.user = AnonymousUser()
        context = seg.get_context(request)

        assert context["transcript"] == seg.transcript


# ---------------------------------------------------------------------------
# Tests: admin actions
# ---------------------------------------------------------------------------


class TestAdminActions:
    def test_fetch_missing_transcripts_skips_segments_with_transcript(self, tree):
        seg_a, seg_b, course = tree["seg_a"], tree["seg_b"], tree["course"]
        seg_a.video_url = VIMEO_URL_A
        seg_a.transcript = [[{"timestamp": "00:01", "text": "Already fetched."}]]
        seg_a.save()
        seg_b.video_url = VIMEO_URL_B
        seg_b.save()

        with patch.object(
            SegmentPage, "_refresh_vimeo_transcript", return_value=True
        ) as mock_refresh:
            fetch_missing_transcripts(
                None, MagicMock(), CoursePage.objects.filter(pk=course.pk)
            )

        assert mock_refresh.call_count == 1

    def test_redownload_transcript_runs_unconditionally(self, tree):
        seg_a = tree["seg_a"]
        seg_a.video_url = VIMEO_URL_A
        seg_a.transcript = [[{"timestamp": "00:01", "text": "Already fetched."}]]
        seg_a.save()

        with patch.object(
            SegmentPage, "_refresh_vimeo_transcript", return_value=True
        ) as mock_refresh:
            redownload_transcript(
                None, MagicMock(), SegmentPage.objects.filter(pk=seg_a.pk)
            )

        mock_refresh.assert_called_once()
