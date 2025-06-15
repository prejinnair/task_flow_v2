from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            # Allow superadmin, admin, manager (optional) OR manual permission
            if user.is_superadmin or user.is_admin or user.role in [0, 1, 2] or user.has_perm(permission_code):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You do not have permission to do this action.")
                referer = request.META.get('HTTP_REFERER')
                return redirect(referer or '/')
        return _wrapped_view
    return decorator
