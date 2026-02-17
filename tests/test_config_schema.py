"""Tests for InPost provider config_schema declarations."""

from sendparcel_inpost.providers.courier import InPostCourierProvider
from sendparcel_inpost.providers.locker import InPostLockerProvider


class TestLockerConfigSchema:
    def test_has_config_schema(self) -> None:
        schema = InPostLockerProvider.config_schema
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_required_fields(self) -> None:
        schema = InPostLockerProvider.config_schema
        assert schema["token"]["required"] is True
        assert schema["organization_id"]["required"] is True

    def test_optional_fields(self) -> None:
        schema = InPostLockerProvider.config_schema
        assert schema["sandbox"]["required"] is False
        assert schema["sandbox"]["default"] is False
        assert schema["base_url"]["required"] is False
        assert schema["timeout"]["required"] is False
        assert schema["timeout"]["default"] == 30.0

    def test_secret_fields(self) -> None:
        schema = InPostLockerProvider.config_schema
        assert schema["token"]["secret"] is True
        assert schema["sandbox"]["secret"] is False

    def test_field_types(self) -> None:
        schema = InPostLockerProvider.config_schema
        assert schema["token"]["type"] == "str"
        assert schema["organization_id"]["type"] == "int"
        assert schema["sandbox"]["type"] == "bool"
        assert schema["timeout"]["type"] == "float"


class TestCourierConfigSchema:
    def test_has_same_schema_as_locker(self) -> None:
        assert (
            InPostCourierProvider.config_schema
            == InPostLockerProvider.config_schema
        )
