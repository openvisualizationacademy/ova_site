# Seed the initial controlled topic vocabulary.
from django.db import migrations
from django.utils.text import slugify


# Order mirrors the previously hard-coded template dropdown, with the
# "Divertisy" typo corrected.
INITIAL_TOPICS = [
    "Design",
    "Statistics",
    "Diversity, Equity, Inclusion",
    "Data Journalism",
    "Programming",
    "Cartography",
    "Artificial Intelligence",
]


def create_topics(apps, schema_editor):
    Topic = apps.get_model("courses", "Topic")
    for order, name in enumerate(INITIAL_TOPICS):
        Topic.objects.get_or_create(
            name=name,
            defaults={"slug": slugify(name), "sort_order": order},
        )


def remove_topics(apps, schema_editor):
    Topic = apps.get_model("courses", "Topic")
    Topic.objects.filter(name__in=INITIAL_TOPICS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0025_topic_coursepage_topics"),
    ]

    operations = [
        migrations.RunPython(create_topics, remove_topics),
    ]