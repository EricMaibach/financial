"""
Custom route decorators.
"""

from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Restrict a route to admin users only.

    - Anonymous users are redirected to the login page.
    - Authenticated non-admin users receive a 403 response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
