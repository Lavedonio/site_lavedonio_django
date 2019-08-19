from django.shortcuts import render


def blog(request):
    context = {
        "title": "Blog",
        "navbar_active": "blog"
    }
    return render(request, "blog/blog.html", context)
