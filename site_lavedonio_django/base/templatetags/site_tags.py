import os
from functools import lru_cache

from django import template
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.templatetags.static import static

from base.images import make_placeholder
from base.management.commands.optimize_static_images import optimized_static_path

register = template.Library()


@register.simple_tag
def static_image(path):
    """
    URL of the optimized (WebP) version of a static photo, created by
    `manage.py optimize_static_images`, or of the original if there's none.
    """
    optimized = optimized_static_path(path)
    return static(optimized if finders.find(optimized) else path)


@lru_cache(maxsize=256)
def _static_placeholder(file_path, modified_time):
    return make_placeholder(file_path)


@register.simple_tag
def image_placeholder(source):
    """
    Tiny version of an image, as a data URI, shown blurred while the image loads.
    `source` is the path of a static file or an uploaded file (ImageField).
    """
    if not source:
        return ''

    try:
        if isinstance(source, str):
            file_path = finders.find(source)
            return _static_placeholder(file_path, os.path.getmtime(file_path)) if file_path else ''

        # Uploaded files never change their name, so it's a stable cache key
        key = f'image-placeholder:{source.name}'
        placeholder = cache.get(key)
        if placeholder is None:
            with source.open('rb') as image_file:
                placeholder = make_placeholder(image_file)
            cache.set(key, placeholder, timeout=None)
        return placeholder
    # Including the storage's errors (R2 on the servers): the page works without it
    except Exception:
        return ''


@register.simple_tag(takes_context=True)
def absolute_uri(context, url):
    """`url` with the request's scheme and host, unless it already has them (like uploads on R2)."""
    return context['request'].build_absolute_uri(url)


@register.simple_tag
def elided_page_range(page_obj, on_each_side=1, on_ends=1):
    """Page numbers to show in the pagination, with "…" between distant ones."""
    return page_obj.paginator.get_elided_page_range(page_obj.number, on_each_side=on_each_side, on_ends=on_ends)


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Current query string with some parameters replaced, e.g. {% query_string page=2 %}"""
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return f'?{query.urlencode()}' if query else '?'
