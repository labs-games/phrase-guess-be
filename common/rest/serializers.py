from collections.abc import Mapping
from typing import Any, Generic, Optional, Type, TypeVar, cast

from django.core.exceptions import ImproperlyConfigured
from rest_framework.fields import empty
from rest_framework.serializers import BaseSerializer
from rest_framework.serializers import ErrorDetail as DRFErrorDetail
from rest_framework.serializers import Serializer
from rest_framework.serializers import ValidationError as DRFValidationError
from six import string_types

from .exceptions import FieldErrorCode, ValidationError, ValidationErrorDetail


class BaseSerializerMixin(BaseSerializer):
    def to_internal_value(self, data):
        ...

    def to_representation(self, instance):
        ...

    def update(self, instance, validated_data):
        ...

    def create(self, validated_data):
        ...

    def raise_validation_error_if_any(self) -> None:
        if self.is_valid():
            return
        details: list[ValidationErrorDetail] = self._parse_error_details([], self.errors)
        if details:
            raise ValidationError(validation_error_details=details)

    def _parse_error_details(
        self, path: list, unparsed_details: dict
    ) -> list[ValidationErrorDetail]:
        error_details: list[ValidationErrorDetail] = []
        for k, v in unparsed_details.items():
            if k == "non_field_errors":
                error_details.append(
                    ValidationErrorDetail(
                        path, FieldErrorCode.field_invalid, extra_data={"message": v}
                    )
                )
                continue
            if isinstance(v, list):
                error_details.extend(self._parse_list_error_details(path + [k], v))
                continue
            if isinstance(v, dict):
                error_details.extend(self._parse_error_details(path + [k], v))
        return error_details

    def _parse_list_error_details(
        self, path: list, unparsed_details: list
    ) -> list[ValidationErrorDetail]:
        error_details: list[ValidationErrorDetail] = []
        for idx, detail in enumerate(unparsed_details):
            current_path: list = path + [idx]
            if isinstance(detail, list):
                error_details.extend(self._parse_list_error_details(current_path, detail))
                continue
            if isinstance(detail, dict):
                error_details.extend(self._parse_error_details(current_path, detail))
                continue
            error_details.append(
                ValidationErrorDetail(
                    path,
                    self._map_error_code(detail.code),
                    extra_data={"message": str(detail)},
                )
            )
        return error_details

    def _map_error_code(self, django_error_code: str) -> FieldErrorCode:
        if django_error_code == "invalid":
            return FieldErrorCode.field_invalid
        if django_error_code == "required":
            return FieldErrorCode.field_required
        if django_error_code == "blank":
            return FieldErrorCode.field_required
        if django_error_code == "min_value":
            return FieldErrorCode.field_below_min_value
        if django_error_code == "max_value":
            return FieldErrorCode.field_above_max_value
        if django_error_code == "min_length":
            return FieldErrorCode.field_below_min_length
        if django_error_code == "max_length":
            return FieldErrorCode.field_above_max_length
        return FieldErrorCode.unknown


class EmptySerializer(Serializer, BaseSerializerMixin):
    class Meta:
        swagger_schema_fields = {"description": "Data field will not be available"}


# pylint: disable=invalid-name
T = TypeVar("T")


class PolymorphicSerializer(Serializer, Generic[T]):
    """
    References:
    https://github.com/apirobot/django-rest-polymorphic/blob/master/rest_polymorphic/serializers.py
    With modifications to allow polymorphism of non ModelSerializers
    """

    data_type_field_name: str = ""
    serializer_classes_by_data_type: dict[T, Type[Serializer]] = {}

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls.data_type_field_name, string_types):
            raise ImproperlyConfigured(
                "`{cls}.data_type_field_name` must be a string".format(cls=cls.__name__)
            )
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.serializers_by_data_type = {
            data_type: serializer_class(*args, **kwargs)
            for data_type, serializer_class in self.serializer_classes_by_data_type.items()
        }
        self._validated_data: dict = {}
        self._errors: dict = {}

    def to_representation(self, instance: Any) -> dict:
        serializer: Serializer = self._get_serializer_from_instance(instance)
        return serializer.to_representation(instance)

    def to_internal_value(self, data: dict) -> dict:
        serializer: Serializer = self._get_serializer_from_mapping(data)
        return serializer.to_internal_value(data)

    def is_valid(self, *args, raise_exception=False, **kwargs) -> bool:
        try:
            serializer: Serializer = self._get_serializer_from_mapping(self.initial_data)
        except DRFValidationError as e:
            self._errors = e.detail
            return False

        is_valid_result: bool = serializer.is_valid(*args, **kwargs)
        self._validated_data = serializer.validated_data
        self._errors = serializer.errors

        if self._errors and raise_exception:
            raise DRFValidationError(self.errors)
        return is_valid_result

    def run_validation(self, data=empty) -> Any:
        if data is empty and self.required:
            self.fail("required")

        if data is empty and not self.required:
            return None

        mapping: dict = data if data is not empty else {}
        serializer: Serializer = self._get_serializer_from_mapping(mapping)
        return serializer.run_validation(data)

    def create(self, validated_data: dict) -> Any:
        serializer: Serializer = self._get_serializer_from_mapping(validated_data)
        return serializer.create(validated_data)

    def update(self, instance: Any, validated_data: dict) -> Any:
        serializer: Serializer = self._get_serializer_from_mapping(validated_data)
        return serializer.update(instance, validated_data)

    def _get_serializer_from_instance(self, instance: Any) -> Serializer:
        data_type_value: T = self.get_data_type_from_instance(instance)
        return self.serializers_by_data_type[data_type_value]

    def _get_serializer_from_mapping(self, mapping: Mapping) -> Serializer:
        data_type_value: T = self._get_data_type_value_from_mapping(mapping)
        serializer: Optional[Serializer] = self.serializers_by_data_type.get(data_type_value)
        if serializer is None:
            raise DRFValidationError(
                {
                    self.data_type_field_name: [
                        DRFErrorDetail("This field is invalid", code="invalid")
                    ],
                },
                code="invalid",
            )
        return serializer

    def get_data_type_from_instance(self, instance: Any) -> T:
        return cast(T, getattr(instance, self.data_type_field_name))

    def _get_data_type_value_from_mapping(self, mapping: Mapping) -> T:
        data_type_value: Optional[T] = mapping.get(self.data_type_field_name)
        if data_type_value is None:
            raise DRFValidationError(
                {
                    self.data_type_field_name: [
                        DRFErrorDetail("This field is required", code="required")
                    ],
                },
                code="invalid",
            )
        return data_type_value
