from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = "pages/about.html"


class RulesView(TemplateView):
    template_name = "pages/rules.html"


# Обработчики ошибок
def csrf_failure(request, reason=""):
    """Страница ошибки 403 (CSRF)."""
    return render(request, "pages/403csrf.html", status=403)


def page_not_found(request, exception):
    """Страница ошибки 404."""
    return render(request, "pages/404.html", status=404)


def server_error(request):
    """Страница ошибки 500."""
    return render(request, "pages/500.html", status=500)
