from django.contrib.auth import logout


class DeactivatedAccountMiddleware:
    """Django doesn't automatically invalidate an existing session when is_active flips to
    False — login_required only checks is_authenticated, so a deactivated user would stay
    logged in until their session naturally expired. This closes that gap by logging them out
    on their next request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            logout(request)
        return self.get_response(request)
