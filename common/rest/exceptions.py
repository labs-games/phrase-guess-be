from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Union

from common.utils import unwrap_or_default


class ErrorCode(IntEnum):
    no_error = 0
    unknown = 1
    unauthenticated = 2
    permission_denied = 3
    bad_request = 4
    validation_error = 5
    resource_not_found = 6
    external_request_error = 7


class FieldErrorCode(IntEnum):
    unknown = 0
    field_required = 1
    field_invalid = 2
    field_below_min_length = 3
    field_above_max_length = 4
    field_below_min_value = 5
    field_above_max_value = 6


@dataclass
class ValidationErrorDetail:
    path: list[Union[str, int]]
    field_error_code: FieldErrorCode
    extra_data: Optional[dict] = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, ValidationErrorDetail):
            return False
        return self.path == other.path and self.field_error_code == other.field_error_code


class ErrorCodeException(Exception):
    def __init__(self, error_code: ErrorCode, error_details: Optional[dict] = None) -> None:
        super().__init__()
        self.error_code: ErrorCode = error_code
        self.error_details: dict = unwrap_or_default(error_details, {})

    def to_dict(self) -> dict:
        return {
            "code": self.error_code.value,
            "data": {
                "error_details": self.error_details,
            },
        }

    def __str__(self):
        return str(self.to_dict())


class ValidationError(ErrorCodeException):
    def __init__(
        self,
        validation_error_details: list[ValidationErrorDetail],
        error_details: Optional[dict] = None,
    ) -> None:
        super().__init__(ErrorCode.validation_error, error_details)
        self.validation_error_details: list[ValidationErrorDetail] = validation_error_details

    def to_dict(self) -> dict:
        response_dict: dict = super().to_dict()
        data_dict: dict = response_dict.get("data", {})
        return {
            **response_dict,
            "data": {
                **data_dict,
                "validation_error_details": [
                    {
                        "path": detail.path,
                        "field_error_code": detail.field_error_code.value,
                        "extra_data": detail.extra_data if detail.extra_data is not None else {},
                    }
                    for detail in self.validation_error_details
                ],
            },
        }
