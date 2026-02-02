import json
import pytest
from django.urls import reverse
from django.utils import timezone
from wagtail.models import Page


from courses.models import (
    CoursePage,
    ChapterPage,
    SegmentPage,
    SegmentProgress,
    ChapterProgress,
    CourseProgress,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def course_structure():
    root = Page.get_first_root_node()

    course = CoursePage(title="Test Course")
    root.add_child(instance=course)
    course.save_revision().publish()

    chapter = ChapterPage(title="Test Chapter")
    course.add_child(instance=chapter)
    chapter.save_revision().publish()

    seg1 = SegmentPage(title="Segment 1")
    chapter.add_child(instance=seg1)
    seg1.save_revision().publish()

    seg2 = SegmentPage(title="Segment 2")
    chapter.add_child(instance=seg2)
    seg2.save_revision().publish()

    return (
        course.specific,
        chapter.specific,
        seg1.specific,
        seg2.specific,
    )


@pytest.fixture
def auth_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="test@example.com",
        password="pass",
    )
    client.force_login(user)
    return client, user


def post_progress(client, segment, percent):
    return client.post(
        reverse("update_progress"),
        data=json.dumps(
            {
                "segment_id": segment.id,
                "percent_watched": percent,
            }
        ),
        content_type="application/json",
    )


def test_progress_completion_contract_single_chapter(auth_client, course_structure):
    client, user = auth_client
    course, chapter, seg1, seg2 = course_structure

    # ---- First segment complete ----
    resp = post_progress(client, seg1, 100)
    data = resp.json()

    assert data["chapter_completed"] is False
    assert data["course_completed"] is False

    assert not ChapterProgress.objects.filter(
        user=user, chapter=chapter, completed=True
    ).exists()

    # ---- Second segment completes chapter ----
    resp = post_progress(client, seg2, 100)
    data = resp.json()

    assert data["chapter_completed"] is True
    assert data["course_completed"] is True

    cp = ChapterProgress.objects.get(user=user, chapter=chapter)
    coursep = CourseProgress.objects.get(user=user, course=course)

    assert cp.completed is True
    assert cp.completed_at is not None

    assert coursep.completed is True
    assert coursep.completed_at is not None

    completed_at_chapter = cp.completed_at
    completed_at_course = coursep.completed_at

    # ---- Reposting 100% does NOT change timestamps ----
    post_progress(client, seg2, 100)

    cp.refresh_from_db()
    coursep.refresh_from_db()

    assert cp.completed_at == completed_at_chapter
    assert coursep.completed_at == completed_at_course


def test_progress_completion_contract_multi_chapter(auth_client):
    client, user = auth_client

    root = Page.get_first_root_node()

    # Course
    course = CoursePage(title="Multi Chapter Course")
    root.add_child(instance=course)
    course.save_revision().publish()

    # Chapter 1
    ch1 = ChapterPage(title="Chapter 1")
    course.add_child(instance=ch1)
    ch1.save_revision().publish()

    ch1_s1 = SegmentPage(title="Ch1 Seg1")
    ch1.add_child(instance=ch1_s1)
    ch1_s1.save_revision().publish()

    # Chapter 2
    ch2 = ChapterPage(title="Chapter 2")
    course.add_child(instance=ch2)
    ch2.save_revision().publish()

    ch2_s1 = SegmentPage(title="Ch2 Seg1")
    ch2.add_child(instance=ch2_s1)
    ch2_s1.save_revision().publish()

    # ---- Complete chapter 1 ----
    post_progress(client, ch1_s1, 100)

    course_prog = CourseProgress.objects.get(user=user, course=course.specific)
    assert course_prog.completed is False

    # ---- Complete chapter 2 ----
    post_progress(client, ch2_s1, 100)

    course_prog.refresh_from_db()
    assert course_prog.completed is True
    assert course_prog.completed_at is not None


def test_progress_completion_is_monotonic(auth_client, course_structure):
    client, user = auth_client
    course, chapter, seg1, seg2 = course_structure

    # ---- Fully complete course ----
    post_progress(client, seg1, 100)
    post_progress(client, seg2, 100)

    cp = ChapterProgress.objects.get(user=user, chapter=chapter)
    coursep = CourseProgress.objects.get(user=user, course=course)

    chapter_completed_at = cp.completed_at
    course_completed_at = coursep.completed_at

    assert cp.completed is True
    assert coursep.completed is True

    # ---- Regress one segment ----
    post_progress(client, seg1, 50)

    cp.refresh_from_db()
    coursep.refresh_from_db()

    # Completion must NOT revert
    assert cp.completed is True
    assert coursep.completed is True
    assert cp.completed_at == chapter_completed_at
    assert coursep.completed_at == course_completed_at
