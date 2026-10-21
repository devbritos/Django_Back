from django.contrib.auth.decorators import login_required, user_passes_test
 
 
def require(perm):
    """Exige permiso Django o el rol Administrador, además de iniciar sesión.
 
    Sin acceso responde 403. Sin login redirige al login.
    """
    def decorator(view):
        def has_access(user):
            if user.has_perm(perm) or user.is_superuser:
                return True
            functionary = getattr(user, 'functionary', None)
            return bool(functionary and functionary.is_admin)

        return login_required(
            user_passes_test(has_access, raise_exception=True)(view)
        )

    return decorator
 