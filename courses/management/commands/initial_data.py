# load_people.py
# import json
# from pathlib import Path
# import json
#
# from courses.models import Instructor, Role
#
#
# file = Path(r"C:\Users\melis\PycharmProjects\ova\ova\temp\people.json")
# with open(file, 'r', encoding='utf-8') as f:
#     people = json.load(f)
#
# for p in people:
#     role_name = p.get("role","")
#     role = None
#     print(role_name)
#
#     if role_name:
#         role, _ = Role.objects.get_or_create(name=role_name)
#     Instructor.objects.update_or_create(
#         name=p["name"],
#         defaults={
#             "tagline": p.get("tagline", ""),
#             "photo": p.get("photo", ""),
#             "bio": p.get("bio", ""),
#             "role": role,
#             "links": p.get("links", []),
#             "former": p.get("former", False)
#         }
#     )

import json
from django.core.management.base import BaseCommand
from courses.models import Instructor, Role


class Command(BaseCommand):
    help = "Import people from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Path to people.json")

    def handle(self, *args, **options):
        json_path = options["json_path"]
        with open(json_path, "r", encoding="utf-8") as f:
            people = json.load(f)

        for p in people:
            role = None
            role_name = p.get("role")
            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)

            person, created = Instructor.objects.update_or_create(
                name=p["name"],
                defaults={
                    "tagline": p.get("tagline", ""),
                    # "photo": p.get("photo", ""),
                    "bio": p.get("bio", ""),
                    "role": role,
                    "social_links": p.get("links", []),
                    "active": p.get("former", False),
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{'Created' if created else 'Updated'} person: {person.name}"
                )
            )
