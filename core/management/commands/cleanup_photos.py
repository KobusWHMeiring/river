#!/usr/bin/env python
"""
Clean up orphaned photo records that reference non-existent files.
Run with: python manage.py cleanup_photos
"""
from django.core.management.base import BaseCommand
from core.models import Photo


class Command(BaseCommand):
    help = 'Remove photo database records for files that no longer exist on disk'

    def handle(self, *args, **options):
        photos = Photo.objects.all()
        deleted_count = 0
        
        for photo in photos:
            if not photo.file or not photo.file.storage.exists(photo.file.name):
                self.stdout.write(
                    self.style.WARNING(
                        f'Deleting orphaned record: {photo.id} - {photo.file.name}'
                    )
                )
                photo.delete()
                deleted_count += 1
        
        if deleted_count:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} orphaned photo records.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('No orphaned photo records found.'))
