from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import Cliente

def cliente_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            if request.user.cliente.is_cliente():
                return view_func(request, *args, **kwargs)
        except Cliente.DoesNotExist:
            pass
        raise PermissionDenied
    return _wrapped_view

def recepcionista_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            if request.user.cliente.is_recepcionista():
                return view_func(request, *args, **kwargs)
        except Cliente.DoesNotExist:
            pass
        raise PermissionDenied
    return _wrapped_view