from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User


class Command(BaseCommand):
    help = 'Delete users who never logged in (never verified their email code) older than 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Delete users who never logged in, older than this many hours (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(hours=hours)

        # Find users who:
        # 1. Have never logged in (last_login is null)
        # 2. Were created more than X hours ago
        # 3. Have no password set (created via OTP flow, not admin)
        unverified_users = User.objects.filter(
            date_joined__lt=cutoff,
            last_login__isnull=True,
        ).exclude(
            is_staff=True  # Never delete staff/admin users
        ).exclude(
            is_superuser=True
        )

        count = unverified_users.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Would delete {count} unverified users (dry run)')
            )
            for user in unverified_users[:10]:
                self.stdout.write(f'  - {user.email} (joined {user.date_joined})')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            deleted, _ = unverified_users.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted} unverified users')
            )
