"""
Creates smaller WebP versions of the photos in base/static/img, which the
{% static_image %} template tag uses instead of the originals:

    python manage.py optimize_static_images

Run it again after adding or changing a photo. Up-to-date versions are skipped.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from base.images import DEFAULT_MAX_SIZE, optimize_image

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
STATIC_DIR = Path(settings.PROJECT_DIR) / 'base' / 'static'
OPTIMIZED_DIR = 'optimized'


def optimized_static_path(path):
    """'img/photo.jpeg' -> 'img/optimized/photo.webp'"""
    path = Path(path)
    return (path.parent / OPTIMIZED_DIR / f'{path.stem}.webp').as_posix()


class Command(BaseCommand):
    help = 'Creates WebP versions of the photos in base/static/img (in img/optimized/), used by {% static_image %}.'

    def add_arguments(self, parser):
        parser.add_argument('--max-size', type=int, default=DEFAULT_MAX_SIZE, help='Largest side, in pixels.')
        parser.add_argument('--quality', type=int, default=80, help='WebP quality, from 0 to 100.')
        parser.add_argument('--force', action='store_true', help='Recreates versions that are up to date.')

    def handle(self, *args, **options):
        image_dir = STATIC_DIR / 'img'
        total_before = total_after = 0

        for source in sorted(image_dir.iterdir()):
            if source.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            target = STATIC_DIR / optimized_static_path(source.relative_to(STATIC_DIR))
            if not options['force'] and target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
                continue

            with source.open('rb') as file:
                optimized = optimize_image(File(file, name=source.name), max_size=options['max_size'], quality=options['quality'])
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(optimized.read())

            before, after = source.stat().st_size, target.stat().st_size
            total_before, total_after = total_before + before, total_after + after
            self.stdout.write(f'{source.name}: {before / 1024:,.0f} KB -> {after / 1024:,.0f} KB')

        if total_before:
            self.stdout.write(self.style.SUCCESS(f'Total: {total_before / 1024 / 1024:,.1f} MB -> {total_after / 1024 / 1024:,.1f} MB'))
        else:
            self.stdout.write('All optimized images are up to date.')
