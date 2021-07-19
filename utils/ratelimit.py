from ratelimit.exceptions import Ratelimited
from rest_framework import status
from rest_framework.views import exception_handler as _exception_handler


def exception_handler(exc, context):
    response = _exception_handler(exc, context)

    if isinstance(exc, Ratelimited):
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        response.data['detail'] = 'Too many requests, try again later.'

    return response
