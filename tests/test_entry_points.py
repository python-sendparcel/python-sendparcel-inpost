"""Tests for entry-point provider registration."""

from sendparcel.provider import BaseProvider
from sendparcel.registry import PluginRegistry

from sendparcel_inpost.providers.courier import InPostCourierProvider
from sendparcel_inpost.providers.locker import InPostLockerProvider


class TestEntryPointRegistration:
    def test_locker_provider_is_base_provider_subclass(self) -> None:
        assert issubclass(InPostLockerProvider, BaseProvider)

    def test_courier_provider_is_base_provider_subclass(self) -> None:
        assert issubclass(InPostCourierProvider, BaseProvider)

    def test_manual_registration_works(self) -> None:
        reg = PluginRegistry()
        reg._discovered = True  # skip auto-discover
        reg.register(InPostLockerProvider)
        reg.register(InPostCourierProvider)
        assert reg.get_by_slug("inpost_locker") is InPostLockerProvider
        assert reg.get_by_slug("inpost_courier") is InPostCourierProvider

    def test_get_choices_includes_inpost(self) -> None:
        reg = PluginRegistry()
        reg._discovered = True
        reg.register(InPostLockerProvider)
        reg.register(InPostCourierProvider)
        choices = reg.get_choices()
        slugs = [slug for slug, _ in choices]
        assert "inpost_locker" in slugs
        assert "inpost_courier" in slugs
