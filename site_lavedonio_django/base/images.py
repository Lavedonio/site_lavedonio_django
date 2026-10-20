"""
Image optimization for uploads made through the site (cover images and images
added in the editors), so photos taken with a smartphone don't end up as
multi-megabyte files.
"""
import base64
import os
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps

DEFAULT_MAX_SIZE = 1920

# Largest side of the blurred preview shown while an image loads
PLACEHOLDER_SIZE = 32


def optimize_image(uploaded_file, max_size=DEFAULT_MAX_SIZE, quality=85):
    """
    Returns a WebP version of `uploaded_file`, with the EXIF orientation applied
    (photos from phones are often stored rotated) and its largest side limited
    to `max_size` pixels. Animated images (e.g. GIFs) are returned untouched.
    """
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as image:
        if getattr(image, 'is_animated', False):
            uploaded_file.seek(0)
            return uploaded_file

        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'transparency' in image.info or image.mode in ('LA', 'PA') else 'RGB')

        output = BytesIO()
        image.save(output, format='WEBP', quality=quality, method=6)

    output.seek(0)
    name = f'{os.path.splitext(os.path.basename(uploaded_file.name))[0]}.webp'
    return InMemoryUploadedFile(output, 'image', name, 'image/webp', output.getbuffer().nbytes, None)


def make_placeholder(image_file):
    """Tiny version of an image, as a data URI (around 500 bytes), to show blurred while it loads."""
    with Image.open(image_file) as image:
        # Decodes JPEGs at a reduced size, much faster for big photos
        image.draft('RGB', (PLACEHOLDER_SIZE * 2, PLACEHOLDER_SIZE * 2))
        image = ImageOps.exif_transpose(image)
        image.thumbnail((PLACEHOLDER_SIZE, PLACEHOLDER_SIZE))
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')

        output = BytesIO()
        image.save(output, format='WEBP', quality=60)

    return 'data:image/webp;base64,' + base64.b64encode(output.getvalue()).decode()
