import re

from django.core.paginator import Paginator
from drf_yasg import openapi
from drf_yasg.inspectors import PaginatorInspector, SerializerInspector

from common.rest.serializers import PolymorphicSerializer

PAGINATION_SCHEMA_DICT: dict = {
    "type": openapi.TYPE_OBJECT,
    "properties": {
        "page": {"type": openapi.TYPE_INTEGER},
        "per_page": {"type": openapi.TYPE_INTEGER},
        "total_entries_size": {"type": openapi.TYPE_INTEGER},
        "current_entries_size": {"type": openapi.TYPE_INTEGER},
        "total_pages": {"type": openapi.TYPE_INTEGER},
    },
    "required": ["page", "per_page", "total_entries_size", "current_entries_size", "total_pages"],
}


class PageNumberPaginatorInspector(PaginatorInspector):
    def get_paginated_response(
        self, paginator: Paginator, response_schema: openapi.Schema
    ) -> openapi.Schema:
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={"items": response_schema, "pagination": PAGINATION_SCHEMA_DICT},
            required=["items", "pagination"],
        )


class PolymorphicSerializerInspector(SerializerInspector):
    """
    References: https://gist.github.com/Safrone/8035d7e666cbedfba919b04404a003d2
    With modification to allow some kind of explanation in the swagger regarding the discriminator
    """

    def _get_definition_name(self, ref):
        m = re.search(r"#/definitions/(?P<definition_name>\w+)", ref)
        return m.group("definition_name")

    def _get_schema_ref(self, serializer: PolymorphicSerializer):
        field_inspectors = [
            x for x in self.field_inspectors if not issubclass(x, PolymorphicSerializerInspector)
        ]
        schema_ref = self.probe_inspectors(
            field_inspectors,
            "get_schema",
            serializer,
            {"field_inspectors": field_inspectors},
        )
        return schema_ref

    def _get_schema(self, serializer: PolymorphicSerializer, schema_ref=None):
        if schema_ref is None:
            schema_ref = self._get_schema_ref(serializer)
        schema = openapi.resolve_ref(schema_ref, self.components)
        return schema

    def process_result(self, result, method_name: str, obj, **kwargs):
        if not isinstance(result, openapi.Schema.OR_REF):
            return result

        if not isinstance(obj, PolymorphicSerializer):
            return result

        # pylint: disable=protected-access
        definitions: dict = self.components._objects["definitions"]
        definition_name: str = self._get_definition_name(result["$ref"])
        schema: openapi.Schema = self._get_schema(obj)

        schema["discriminator"] = obj.data_type_field_name
        schema["required"] = schema.setdefault("required", []) + [obj.data_type_field_name]
        schema["properties"][obj.data_type_field_name] = openapi.Schema(
            title="discriminator",
            description="This is discriminator field.\n"
            "The rest of the schema will be one of the below schema.\n"
            "Depending on the discriminator value.",
            type="Enum",
            enum=list(obj.serializers_by_data_type.keys()),
        )

        for data_type, serializer in obj.serializers_by_data_type.items():
            schema["properties"][f"discriminator={data_type}"] = self._get_schema_ref(serializer)
        definitions[definition_name] = schema

        return result
