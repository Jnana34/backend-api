# shopfusion_backend/auth.py
from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # ✅ Do nothing — disables CSRF check
