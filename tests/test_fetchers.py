"""Unit tests untuk src/fetchers.py — menggunakan mock agar tidak menyentuh API sungguhan."""
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fetchers import safe_fetch

logger = logging.getLogger("test")


class TestSafeFetch:
    def test_returns_result_on_success(self):
        fn = MagicMock(return_value=["model-a", "model-b"])
        result = safe_fetch("TestProvider", fn, logger)
        assert result == ["model-a", "model-b"]
        fn.assert_called_once_with(logger)

    def test_returns_default_on_exception(self):
        def boom(logger):
            raise RuntimeError("API down")

        result = safe_fetch("TestProvider", boom, logger, default=[])
        assert result == []

    def test_returns_custom_default_on_exception(self):
        def boom(logger):
            raise ConnectionError("Timeout")

        result = safe_fetch("TestProvider", boom, logger, default={"fallback": True})
        assert result == {"fallback": True}

    def test_skips_when_env_missing(self, monkeypatch):
        # Pastikan key tidak ada di environment
        monkeypatch.delenv("MY_SECRET_KEY", raising=False)
        fn = MagicMock()
        result = safe_fetch("TestProvider", fn, logger, needed_env=("MY_SECRET_KEY",))
        fn.assert_not_called()
        assert result == []

    def test_runs_when_env_present(self, monkeypatch):
        monkeypatch.setenv("MY_SECRET_KEY", "abc123")
        fn = MagicMock(return_value=["ok"])
        result = safe_fetch("TestProvider", fn, logger, needed_env=("MY_SECRET_KEY",))
        fn.assert_called_once()
        assert result == ["ok"]

    def test_default_is_empty_list(self):
        def boom(logger):
            raise ValueError("fail")

        result = safe_fetch("TestProvider", boom, logger)
        assert result == []

    def test_multiple_missing_env_keys_skip(self, monkeypatch):
        monkeypatch.delenv("KEY_A", raising=False)
        monkeypatch.delenv("KEY_B", raising=False)
        fn = MagicMock()
        result = safe_fetch("TestProvider", fn, logger, needed_env=("KEY_A", "KEY_B"))
        fn.assert_not_called()
        assert result == []
