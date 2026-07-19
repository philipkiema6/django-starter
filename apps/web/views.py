from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from apps.courses.selectors import instructor_dashboard_data, student_dashboard_data


def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            # Staff get their own dashboard (apps.adminpanel) rather than the
            # instructor/student view below — "Admin" is a distinct area, not a third
            # variant of this page.
            return redirect("adminpanel:dashboard")
        profile = request.user.profile
        context = {
            "active_tab": "dashboard",
            "page_title": _("Dashboard"),
            "profile": profile,
        }
        if profile.is_instructor:
            context.update(instructor_dashboard_data(request.user))
        else:
            context.update(student_dashboard_data(request.user))
        return render(request, "web/app_home.html", context=context)
    else:
        return render(request, "web/landing_page.html")


@user_passes_test(lambda u: u.is_superuser)
def simulate_error(request):
    raise Exception("This is a simulated error.")


def manifest(request):
    """PWA manifest, built from PROJECT_METADATA (rather than a static file) so it stays in
    sync with the site name/description like the rest of the app's meta tags. JsonResponse
    handles escaping correctly, unlike rendering JSON through an HTML-autoescaping template."""
    name = str(settings.PROJECT_METADATA["NAME"])
    return JsonResponse(
        {
            "name": name,
            "short_name": name,
            "description": str(settings.PROJECT_METADATA["DESCRIPTION"]),
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#ffffff",
            "icons": [
                {
                    "src": staticfiles_storage.url("images/favicons/android-chrome-192x192.png"),
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": staticfiles_storage.url("images/favicons/android-chrome-512x512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                },
            ],
        }
    )


def service_worker(request):
    """Serve static/sw.js at the site root so its default scope covers the whole site
    (a service worker's scope defaults to the directory it's served from, and /static/
    would only cover static assets). Uses the staticfiles finders (source STATICFILES_DIRS)
    rather than staticfiles_storage, since the latter requires collectstatic to have already
    run and would 404 in local development."""
    path = finders.find("sw.js")
    if not path:
        raise Http404
    with open(path, "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="application/javascript")
