from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Post


def blog(request):
    context = {
        "title": "Blog",
        "navbar_active": "blog"
    }
    return render(request, "blog/blog.html", context)


class PostListView(ListView):
    model = Post
    # template_name = "blog/blog.html"
    context_object_name = "posts"
    ordering = ["-date_posted"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Blog"
        context["navbar_active"] = "blog"
        return context


class PostDetailView(DetailView):
    model = Post
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        context["title"] = post.title + " - Blog"
        context["navbar_active"] = "blog"
        context["no_container"] = True
        return context
