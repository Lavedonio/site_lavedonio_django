import datetime
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, Q
from .models import Post, Tag


class PostFilterListView(ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self, **kwargs):
        if self.kwargs.get('year_month') is not None:
            year_month_str = self.kwargs.get('year_month')
            year_month = datetime.date(
                year=int(year_month_str[:4]),
                month=int(year_month_str[-2:]),
                day=1
            )

            if self.request.user.is_authenticated:
                return Post.objects.filter(date_posted_year_month=year_month).order_by('-date_posted')
            else:
                return Post.objects.filter(Q(date_posted_year_month=year_month) & Q(published=True)).order_by('-date_posted')

        else:
            tag = Tag.objects.filter(name__iexact=self.kwargs['tag_name']).first()

            if self.request.user.is_authenticated:
                return Post.objects.filter(tag=tag).order_by('-date_posted')
            else:
                return Post.objects.filter(Q(tag=tag) & Q(published=True)).order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Blog"
        context["navbar_active"] = "blog"
        context["featured"] = False
        context["filtering"] = True
        context["tags"] = Tag.objects.all().order_by("name")

        # Getting info of archive or tag, acording to the kwargs
        if self.kwargs.get('year_month') is not None:
            context["filtered_by"] = 'archive'

            year_month_str = self.kwargs['year_month']
            context["filtered_url"] = year_month_str

            context["year_month_date"] = datetime.date(
                year=int(year_month_str[:4]),
                month=int(year_month_str[-2:]),
                day=1
            )
        else:
            context["filtered_by"] = 'tag'

            context["tag"] = Tag.objects.filter(name__iexact=self.kwargs['tag_name']).first()

            context["filtered_url"] = self.kwargs['tag_name']

        if self.request.user.is_authenticated:
            # Getting distinct years for template
            distinct_year_months_queryset = Post.objects.values_list('date_posted_year_month').distinct()

            context["archive_queryset_years"] = sorted(list({str(x[0].year) for x in distinct_year_months_queryset}), reverse=True)

            # Getting total posts for each year_month
            context["archive_queryset"] = Post.objects \
                .values('date_posted_year_month') \
                .order_by('-date_posted_year_month') \
                .annotate(num_posts=Count('date_posted_year_month'))

        else:
            # Getting distinct years for template
            distinct_year_months_queryset = Post.objects.filter(published=True).values_list('date_posted_year_month').distinct()

            context["archive_queryset_years"] = sorted(list({str(x[0].year) for x in distinct_year_months_queryset}), reverse=True)

            # Getting total posts for each year_month
            context["archive_queryset"] = Post.objects.filter(published=True) \
                .values('date_posted_year_month') \
                .order_by('-date_posted_year_month') \
                .annotate(num_posts=Count('date_posted_year_month'))

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

    def get_queryset(self, **kwargs):
        if self.request.user.is_authenticated:
            return Post.objects.all().order_by('-date_posted')
        else:
            return Post.objects.filter(published=True).order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Blog"
        context["navbar_active"] = "blog"
        context["archive"] = False
        context["tags"] = Tag.objects.all().order_by("name")

        # Archived year_month
        if self.request.user.is_authenticated:
            # Getting distinct years for template
            distinct_year_months_queryset = Post.objects.values_list('date_posted_year_month').distinct()

            context["archive_queryset_years"] = sorted(list({str(x[0].year) for x in distinct_year_months_queryset}), reverse=True)

            # Getting total posts for each year_month
            context["archive_queryset"] = Post.objects.values('date_posted_year_month').annotate(num_posts=Count('date_posted_year_month'))
        else:
            # Getting distinct years for template
            distinct_year_months_queryset = Post.objects.filter(published=True).values_list('date_posted_year_month').distinct()

            context["archive_queryset_years"] = sorted(list({str(x[0].year) for x in distinct_year_months_queryset}), reverse=True)

            # Getting total posts for each year_month
            context["archive_queryset"] = Post.objects.filter(published=True).values('date_posted_year_month').annotate(num_posts=Count('date_posted_year_month'))

        # Featured Posts
        has_featured = Post.objects.filter(featured=True).count() > 0
        context["featured"] = has_featured

        if has_featured:
            if self.request.user.is_authenticated:
                context["posts_featured"] = Post.objects.filter(featured=True).order_by('-date_posted')[:2]
            else:
                context["posts_featured"] = Post.objects.filter(Q(featured=True) & Q(published=True)).order_by('-date_posted')[:2]

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
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = [
        "title",
        "subtitle",
        "tags",
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
        "tags",
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
