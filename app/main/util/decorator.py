from functools import wraps
from typing import Callable

from app.main.service.auth_helper import Auth
from flask import request


def token_required(f) -> Callable:
    @wraps(f)
    def decorated(*args, **kwargs):
        data, status = Auth.get_logged_in_user(request)
        token = data.get('parameters')

        if not token:
            return data, status

        return f(*args, **kwargs)

    return decorated


def admin_token_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated(*args, **kwargs):

        data, status = Auth.get_logged_in_user(request)
        token = data.get('parameters')

        if not token:
            return data, status

        admin = token.get('admin')
        if not admin:
            response_object = {
                'status': 'fail',
                'message': 'admin token required'
            }
            return response_object, 401

        return f(*args, **kwargs)

    return decorated
