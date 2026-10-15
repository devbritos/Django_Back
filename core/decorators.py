from django.contrib.auth.decorators import login_required, permission_required
 
 
def require(perm):
    """Exige estar logueado y tener el permiso indicado (ej: "personal.add_position").
 
    Sin permiso responde 403. Sin login redirige al login.
    """
    def decorator(view):
        return login_required(permission_required(perm, raise_exception=True)(view))
    return decorator
 