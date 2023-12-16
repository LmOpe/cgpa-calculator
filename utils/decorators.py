import requests
import urllib.parse

from flask import redirect, render_template, request, session, flash
from functools import wraps
from flask_login import current_user


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please login.", "info")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def logout_required(f):
    """ Decorate register and login routes to require logout """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash("You are already authenticated in", "info")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function