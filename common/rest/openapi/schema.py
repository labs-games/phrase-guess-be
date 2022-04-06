import enum

from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema as _SwaggerAutoSchema
from drf_yasg.openapi import Schema

from common.rest.exceptions import ErrorCode


def generate_enum_description(enums: list[enum.Enum]):
    base_description: str = """
| Enum | Description |
| ---- | ----------- |
"""
    return base_description + "\n".join([f"| {e.value} | {e.name} |" for e in enums])


ERROR_CODE_SCHEMA_DICT: dict = {
    "type": openapi.TYPE_INTEGER,
    "default": ErrorCode.no_error,
    "enum": list(ErrorCode),
    "description": generate_enum_description(list(ErrorCode)),
}


class SwaggerAutoSchema(_SwaggerAutoSchema):
    def get_response_schemas(self, response_serializers):
        responses: dict = super().get_response_schemas(response_serializers)

        for _, response in responses.items():
            if hasattr(response, "schema"):
                response.schema = Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "data": response.schema,
                        "code": ERROR_CODE_SCHEMA_DICT,
                    },
                )

        return responses
