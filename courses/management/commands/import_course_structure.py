"""
Management command: import_course_structure

JSON format example:

{
  "generative-ai-data-analysis": {
    "Introduction": [
      "Welcome",
      "How to Use This Course"
    ],
    "Core Concepts": [
      "What Is GenAI",
      "Why It Matters",
      "Common Mistakes"
    ],
    "Hands-On": [
      "Setup",
      "Live Demo",
      "Wrap-Up"
    ]
  }
}

Rules:
- Top-level key MUST be the course slug
- Keys under the course are chapter titles
- Values are ordered lists of segment titles
- Order in JSON = order in Wagtail

------------------------------------
USAGE
------------------------------------

With uv (recommended):

  uv run python manage.py import_course_structure path/to/course_structure.json --dry-run
  uv run python manage.py import_course_structure path/to/course_structure.json

Without uv:

  python manage.py import_course_structure path/to/course_structure.json --dry-run
  python manage.py import_course_structure path/to/course_structure.json

Notes:
- The course must already be created in Wagtail
- Always run with --dry-run first
- Command is idempotent: existing chapters/segments are updated, missing ones are created
- Reordering requires adjusting JSON order and re-running
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from courses.models import CoursePage, ChapterPage, SegmentPage


class Command(BaseCommand):
    help = "Create or update chapters and segments for a course from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to JSON file containing course structure",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions without writing to the database",
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_file"])
        dry_run = options["dry_run"]

        if not json_path.exists():
            raise CommandError(f"JSON file not found: {json_path}")

        with json_path.open() as f:
            data = json.load(f)

        if not isinstance(data, dict) or len(data) != 1:
            raise CommandError(
                "JSON must contain exactly one top-level key (the course slug)"
            )

        course_slug, structure = next(iter(data.items()))

        try:
            course = CoursePage.objects.get(slug=course_slug)
        except CoursePage.DoesNotExist:
            raise CommandError(f"Course with slug '{course_slug}' does not exist")

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"{'DRY RUN: ' if dry_run else ''}Importing structure for '{course.title}'"
            )
        )

        for ch_idx, (chapter_title, segments) in enumerate(structure.items(), start=1):
            chapter_slug = f"{ch_idx:02d}-{slugify(chapter_title)}"

            chapter = (
                course.get_children()
                .type(ChapterPage)
                .filter(slug=chapter_slug)
                .specific()
                .first()
            )

            if chapter:
                self.stdout.write(f"Updating chapter: {chapter_title}")
                if not dry_run:
                    chapter.title = chapter_title
                    chapter.save_revision().publish()
            else:
                self.stdout.write(f"Creating chapter: {chapter_title}")
                if not dry_run:
                    chapter = ChapterPage(title=chapter_title, slug=chapter_slug)
                    course.add_child(instance=chapter)
                    chapter.save_revision().publish()

            if dry_run:
                continue

            for seg_idx, seg_title in enumerate(segments, start=1):
                segment_slug = f"{chapter_slug}-{seg_idx:02d}"

                segment = (
                    chapter.get_children()
                    .type(SegmentPage)
                    .filter(slug=segment_slug)
                    .specific()
                    .first()
                )

                if segment:
                    self.stdout.write(f"  └─ Updating segment: {seg_title}")
                    segment.title = seg_title
                    segment.save_revision().publish()
                else:
                    self.stdout.write(f"  └─ Creating segment: {seg_title}")
                    segment = SegmentPage(title=seg_title, slug=segment_slug)
                    chapter.add_child(instance=segment)
                    segment.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                "Dry run complete. No changes written."
                if dry_run
                else "Import completed successfully."
            )
        )
