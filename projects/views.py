from django.shortcuts import render


def pong(request):
    context = {
        "title": "Pong - Projetos",
        "navbar_active": "projects"
    }
    return render(request, "projects/pong.html", context)
