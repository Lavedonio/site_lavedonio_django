import datetime
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from .models import Post


class PostFilterListView(ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self):
        year_month_str = self.kwargs.get('year_month')
        year_month = datetime.date(
            year=int(year_month_str[:4]),
            month=int(year_month_str[-2:]),
            day=1
        )

        return Post.objects.filter(date_posted_year_month=year_month).order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Blog"
        context["navbar_active"] = "blog"
        context["featured"] = False
        context["archive"] = True
        context["archive_year_month_url"] = self.kwargs['year_month']

        year_month_str = self.kwargs['year_month']
        context["year_month_date"] = datetime.date(
            year=int(year_month_str[:4]),
            month=int(year_month_str[-2:]),
            day=1
        )

        queryset_archive = Post.objects.values('date_posted_year_month') \
            .order_by('-date_posted_year_month') \
            .annotate(num_posts=Count('date_posted_year_month'))
        context["archive_queryset"] = queryset_archive

        posts = self.get_queryset()
        page = self.request.GET.get('pagina')
        paginator = Paginator(posts, self.paginate_by)

        try:
            posts = paginator.page(page)

        except PageNotAnInteger:
            posts = paginator.page(1)

        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        context['page_obj'] = posts
        return context


class PostListView(ListView):
    model = Post
    context_object_name = "posts"
    ordering = ["-date_posted"]
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Blog"
        context["navbar_active"] = "blog"
        context["archive"] = False

        # Archived year_month
        queryset_archive = Post.objects.values('date_posted_year_month').annotate(num_posts=Count('date_posted_year_month'))
        context["archive_queryset"] = queryset_archive

        # Featured Posts
        has_featured = Post.objects.filter(featured=True).count() > 0
        context["featured"] = has_featured

        if has_featured:
            context["posts_featured"] = Post.objects.filter(featured=True).order_by('-date_posted')[:2]

        # Pagination
        posts = self.get_queryset()
        page = self.request.GET.get('pagina')
        paginator = Paginator(posts, self.paginate_by)

        try:
            posts = paginator.page(page)

        except PageNotAnInteger:
            posts = paginator.page(1)

        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        context['page_obj'] = posts

        return context


class PostDetailView(DetailView):
    model = Post
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, slug=self.kwargs['slug'])
        context["title"] = post.title + " - Blog"
        context["navbar_active"] = "blog"
        context["no_container"] = True
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = [
        "title",
        "subtitle",
        "main_image",
        "featured",
        "published",
        "content",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editar"] = False
        context["title"] = "Nova Publicação - Blog"
        context["navbar_active"] = "blog"
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = [
        "title",
        "subtitle",
        "main_image",
        "featured",
        "published",
        "content",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editar"] = True
        context["title"] = "Editar Publicação - Blog"
        context["navbar_active"] = "blog"
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author  # if/else


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("blog")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Deletar Publicação - Blog"
        context["navbar_active"] = "blog"
        return context

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author  # if/else
