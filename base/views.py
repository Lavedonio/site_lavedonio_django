from django.shortcuts import render


def home(request):
    context = {
        "title": "Homepage",
        "navbar_active": "home"
    }
    return render(request, "home.html", context)


def about(request):
    context = {
        "title": "Sobre",
        "navbar_active": "about"
    }
    return render(request, "about.html", context)


def contact(request):
    context = {
        "title": "Contato",
        "navbar_active": "contact"
    }
    return render(request, "contact.html", context)
