import datetime
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.http import urlencode
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, RedirectView, UpdateView

from base.editing import TranslatableEditMixin
from base.i18n import build_language_url
from .forms import PostForm, PostTranslationForm
from .models import Post, Tag


class PostListView(ListView):
    """All posts, or the ones with a tag or from a month (archive)."""
    context_object_name = "posts"
    paginate_by = 5
    featured_count = 2
    # Posts not written in the language of the site are listed too, in the
    # language they were written and with a badge telling which one it is
    include_other_languages = True

    def get_base_queryset(self):
        queryset = Post.objects.visible_to(self.request.user)
        if not self.include_other_languages:
            queryset = queryset.in_language(translation.get_language())
        return queryset

    def get_queryset(self):
        queryset = self.get_base_queryset().with_related()

        if "tag" in self.kwargs:
            self.tag = get_object_or_404(Tag.objects.prefetch_related("translations"), slug=self.kwargs["tag"])
            queryset = queryset.filter(tags=self.tag)

        if "year" in self.kwargs:
            if not 1 <= self.kwargs["month"] <= 12:
                raise Http404
            queryset = queryset.filter(date_posted__year=self.kwargs["year"], date_posted__month=self.kwargs["month"])

        return queryset

    def get_archive(self, posts):
        """[{'year': 2026, 'months': [{'month': date, 'count': 3}, ...]}, ...]"""
        months = (
            posts.annotate(month=TruncMonth("date_posted"))
            .values("month")
            .annotate(count=Count("pk"))
            .order_by("-month")
        )
        return [{"year": year, "months": list(items)} for year, items in groupby(months, key=lambda item: item["month"].year)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Blog")
        context["navbar_active"] = "blog"

        visible_posts = self.get_base_queryset()
        context["tags"] = (
            Tag.objects.filter(posts__in=visible_posts.values("pk"))
            .annotate(num_posts=Count("posts", distinct=True))
            .prefetch_related("translations")
        )
        context["archive"] = self.get_archive(visible_posts)

        context["filter_tag"] = getattr(self, "tag", None)
        if "year" in self.kwargs:
            context["filter_month"] = datetime.date(self.kwargs["year"], self.kwargs["month"], 1)
        context["is_filtered"] = "tag" in self.kwargs or "year" in self.kwargs

        page = context["page_obj"]
        if not context["is_filtered"] and page.number == 1:
            context["featured_posts"] = visible_posts.filter(featured=True).with_related()[:self.featured_count]

        if self.request.user.has_perm("blog.change_post"):
            context["draft_count"] = Post.objects.exclude(pk__in=Post.objects.published().values("pk")).count()

        return context


class PostRedirectView(RedirectView):
    """Short URL (/blog/<id>/) that redirects to the post's full URL."""
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        post = get_object_or_404(Post.objects.visible_to(self.request.user).prefetch_related("translations"), pk=kwargs["pk"])
        return post.get_absolute_url()


class V1PostRedirectView(RedirectView):
    """The v1 site's post URLs (/blog/post/<slug>/), whose slugs are the posts' Portuguese ones."""
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        post = (
            Post.objects.visible_to(self.request.user)
            .filter(translations__language="pt-br", translations__slug=kwargs["slug"])
            .prefetch_related("translations")
            .first()
        )
        if post is None:
            raise Http404
        return post.get_absolute_url()


class PostDetailView(DetailView):
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.visible_to(self.request.user).with_related()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.translation = self.object.translation
        if self.translation is None:
            raise Http404

        # The slug is only informative: fixes it if it's outdated or from another language
        if kwargs["slug"] != self.translation.slug:
            return redirect(self.object.get_absolute_url(), permanent=True)

        # The same post in the other languages (which may have other slugs)
        request.language_alternate_paths = {
            language: self.object.get_absolute_url(language) for language in self.object.available_languages
        }

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_share_links(self, url, title):
        def tracked(source):
            query = urlencode({"utm_source": source, "utm_medium": "share", "utm_campaign": "blog-post"})
            return f"{url}?{query}"

        # (name, bootstrap icon, share URL, query parameters)
        networks = [
            ("LinkedIn", "linkedin", "https://www.linkedin.com/sharing/share-offsite/", {"url": tracked("linkedin")}),
            ("X", "twitter-x", "https://x.com/intent/post", {"text": title, "url": tracked("twitter")}),
            ("WhatsApp", "whatsapp", "https://wa.me/", {"text": f"{title} {tracked('whatsapp')}"}),
            ("Telegram", "telegram", "https://t.me/share/url", {"url": tracked("telegram"), "text": title}),
            ("Facebook", "facebook", "https://www.facebook.com/sharer/sharer.php", {"u": tracked("facebook")}),
            ("Reddit", "reddit", "https://www.reddit.com/submit", {"url": tracked("reddit"), "title": title}),
        ]
        return [{"name": name, "icon": icon, "url": f"{base_url}?{urlencode(query)}"} for name, icon, base_url, query in networks]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        post_translation = self.translation

        context["title"] = _("%(post)s - Blog") % {"post": post_translation.title}
        context["navbar_active"] = "blog"
        context["post_translation"] = post_translation

        # Posts only available in another language point search engines to the host of that language
        context["canonical_url"] = build_language_url(self.request, post_translation.language, post.get_absolute_url(post_translation.language))
        context["share_links"] = self.get_share_links(context["canonical_url"], post_translation.title)

        # Neighbor posts, following the same visibility rules
        posts = Post.objects.visible_to(self.request.user).prefetch_related("translations")
        context["previous_post"] = posts.filter(date_posted__lt=post.date_posted).order_by("-date_posted").first()
        context["next_post"] = posts.filter(date_posted__gt=post.date_posted).order_by("date_posted").first()
        return context


class PostEditMixin(PermissionRequiredMixin, TranslatableEditMixin):
    model = Post
    form_class = PostForm
    translation_form_class = PostTranslationForm
    translation_parent_field = "post"
    success_message = gettext_lazy("Post saved.")

    def get_queryset(self):
        return Post.objects.prefetch_related("translations")

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar_active"] = "blog"
        return context


class PostCreateView(PostEditMixin, CreateView):
    permission_required = "blog.add_post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("New post - Blog")
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostEditMixin, UpdateView):
    permission_required = "blog.change_post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Edit post - Blog")
        return context


class PostDeleteView(PermissionRequiredMixin, DeleteView):
    model = Post
    permission_required = "blog.delete_post"
    success_url = reverse_lazy("blog:list")

    def get_queryset(self):
        return Post.objects.prefetch_related("translations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Delete post - Blog")
        context["navbar_active"] = "blog"
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Post deleted."))
        return super().form_valid(form)
