"""Tests for core decorators.

Story P14-5.1: Create @singleton decorator
"""

import threading
import pytest

from app.core.decorators import singleton, SingletonMeta


class TestSingletonDecorator:
    """Tests for the @singleton decorator."""

    def test_returns_same_instance(self):
        """Singleton should return the same instance on multiple calls."""
        @singleton
        class TestService:
            def __init__(self):
                self.value = 0

        try:
            s1 = TestService()
            s2 = TestService()
            assert s1 is s2
        finally:
            TestService._reset_instance()

    def test_reset_creates_new_instance(self):
        """Reset should allow creation of a new instance."""
        @singleton
        class TestService:
            def __init__(self):
                self.value = 0

        try:
            s1 = TestService()
            s1.value = 42
            TestService._reset_instance()
            s2 = TestService()
            assert s1 is not s2
            assert s2.value == 0
        finally:
            TestService._reset_instance()

    def test_get_instance_returns_none_before_creation(self):
        """_get_instance should return None before instance is created."""
        @singleton
        class TestService:
            pass

        try:
            TestService._reset_instance()
            assert TestService._get_instance() is None
        finally:
            TestService._reset_instance()

    def test_get_instance_returns_instance_after_creation(self):
        """_get_instance should return instance after creation."""
        @singleton
        class TestService:
            pass

        try:
            service = TestService()
            assert TestService._get_instance() is service
        finally:
            TestService._reset_instance()

    def test_init_called_once(self):
        """__init__ should only be called once."""
        call_count = 0

        @singleton
        class TestService:
            def __init__(self):
                nonlocal call_count
                call_count += 1

        try:
            TestService()
            TestService()
            TestService()
            assert call_count == 1
        finally:
            TestService._reset_instance()

    def test_init_with_arguments(self):
        """Singleton should work with __init__ arguments (first call only)."""
        @singleton
        class TestService:
            def __init__(self, name: str = "default"):
                self.name = name

        try:
            s1 = TestService("custom")
            s2 = TestService("other")  # Should be ignored
            assert s1.name == "custom"
            assert s2 is s1
        finally:
            TestService._reset_instance()

    def test_thread_safe(self):
        """Singleton should be thread-safe."""
        @singleton
        class TestService:
            def __init__(self):
                self.value = 0

        instances = []
        errors = []

        def get_instance():
            try:
                instances.append(TestService())
            except Exception as e:
                errors.append(e)

        try:
            threads = [threading.Thread(target=get_instance) for _ in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert not errors, f"Errors occurred: {errors}"
            assert len(instances) == 20
            assert all(i is instances[0] for i in instances)
        finally:
            TestService._reset_instance()

    def test_cleanup_called_on_reset(self):
        """Reset should call cleanup method if present."""
        cleanup_called = False

        @singleton
        class TestService:
            def cleanup(self):
                nonlocal cleanup_called
                cleanup_called = True

        try:
            TestService()
            TestService._reset_instance()
            assert cleanup_called
        finally:
            TestService._reset_instance()

    def test_cleanup_error_handled(self):
        """Cleanup errors should not prevent reset."""
        @singleton
        class TestService:
            def cleanup(self):
                raise ValueError("Cleanup failed")

        try:
            TestService()
            # Should not raise
            TestService._reset_instance()
            # Should be able to create new instance
            s2 = TestService()
            assert s2 is not None
        finally:
            TestService._reset_instance()


class TestSingletonMeta:
    """Tests for the SingletonMeta metaclass."""

    def test_returns_same_instance(self):
        """Singleton metaclass should return same instance."""
        class TestService(metaclass=SingletonMeta):
            def __init__(self):
                self.value = 0

        try:
            s1 = TestService()
            s2 = TestService()
            assert s1 is s2
        finally:
            TestService._reset_instance()

    def test_reset_creates_new_instance(self):
        """Reset should allow creation of new instance."""
        class TestService(metaclass=SingletonMeta):
            def __init__(self):
                self.value = 0

        try:
            s1 = TestService()
            s1.value = 42
            TestService._reset_instance()
            s2 = TestService()
            assert s1 is not s2
            assert s2.value == 0
        finally:
            TestService._reset_instance()

    def test_get_instance(self):
        """_get_instance should work correctly."""
        class TestService(metaclass=SingletonMeta):
            pass

        try:
            TestService._reset_instance()
            assert TestService._get_instance() is None
            service = TestService()
            assert TestService._get_instance() is service
        finally:
            TestService._reset_instance()

    def test_thread_safe(self):
        """Singleton metaclass should be thread-safe."""
        class TestService(metaclass=SingletonMeta):
            pass

        instances = []

        def get_instance():
            instances.append(TestService())

        try:
            threads = [threading.Thread(target=get_instance) for _ in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(instances) == 20
            assert all(i is instances[0] for i in instances)
        finally:
            TestService._reset_instance()

    def test_cleanup_called_on_reset(self):
        """Reset should call cleanup method."""
        cleanup_called = False

        class TestService(metaclass=SingletonMeta):
            def cleanup(self):
                nonlocal cleanup_called
                cleanup_called = True

        try:
            TestService()
            TestService._reset_instance()
            assert cleanup_called
        finally:
            TestService._reset_instance()
