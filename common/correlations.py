import logging
from threading import local
from typing import Callable, Optional, Any

from django.http import HttpRequest


class CorrelationLocal(local):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)  # type: ignore
        self.correlation_id: Optional[str] = None

    def set_new_correlation_id(self, new_id: str) -> None:
        self.correlation_id = new_id

    def clear_correlation_id(self) -> None:
        self.correlation_id = None


class CorrelationMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response: Callable = get_response

    def __call__(self, request: HttpRequest) -> Any:
        server_request_id: str = request.META.get("HTTP_X_REQUEST_ID", "unknown_server_id")
        client_request_id: str = request.META.get("HTTP_CLIENT_REQUEST_ID", "unknown_client_id")
        correlation_local.set_new_correlation_id(f'[{client_request_id}]-[{server_request_id}]')

        response: Any = self.get_response(request)
        correlation_local.clear_correlation_id()
        return response


class CorrelationLogFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.correlation_id = correlation_local.correlation_id
        return True


correlation_local: CorrelationLocal = CorrelationLocal()
