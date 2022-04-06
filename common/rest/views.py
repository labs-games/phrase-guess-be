from typing import Type

from django.http import Http404
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response

from common.logger import log

from .exceptions import ErrorCode, ErrorCodeException
from .jwt import JWTTokenUserAuthentication
from .permissions import IsActive


class BaseAPIViewMixin:
    authentication_classes: list[Type[BaseAuthentication]] = []
    permission_classes: list[Type[BasePermission]] = [AllowAny]

    def generate_no_error_response(self, data: dict) -> Response:
        response_dict: dict = {"code": ErrorCode.no_error.value}
        if data:
            response_dict["data"] = data
        return Response(response_dict)


class ActiveUserAPIViewMixin(BaseAPIViewMixin):
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated, IsActive]


def exception_handler(exc, context):
    log.info("exception_handler|original exc=%s, context=%s|start", exc, context)
    converted_exception: ErrorCodeException
    if isinstance(exc, Http404):
        converted_exception = ErrorCodeException(
            ErrorCode.resource_not_found, error_details={"reason": str(exc)}
        )
    elif isinstance(exc, NotFound):
        converted_exception = ErrorCodeException(
            ErrorCode.resource_not_found, error_details=exc.detail
        )
    elif isinstance(exc, ValidationError):
        converted_exception = ErrorCodeException(
            ErrorCode.validation_error, error_details=exc.detail
        )
    elif isinstance(exc, NotAuthenticated):
        converted_exception = ErrorCodeException(
            ErrorCode.unauthenticated, error_details=exc.detail
        )
    elif isinstance(exc, AuthenticationFailed):
        converted_exception = ErrorCodeException(
            ErrorCode.unauthenticated, error_details=exc.detail
        )
    elif isinstance(exc, PermissionDenied):
        converted_exception = ErrorCodeException(
            ErrorCode.permission_denied, error_details=exc.detail
        )
    elif isinstance(exc, ErrorCodeException):
        converted_exception = exc
    else:
        log.error(exc, exc_info=True)
        converted_exception = ErrorCodeException(ErrorCode.unknown)

    log.info(
        "exception_handler|Returning error, code=%s, error_details=%s|end",
        converted_exception.error_code,
        converted_exception.error_details,
    )
    return Response(converted_exception.to_dict())
