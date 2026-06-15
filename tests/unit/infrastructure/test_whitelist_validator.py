"""Unit tests for WhitelistCommandValidatorAdapter."""

import tempfile
from pathlib import Path

import pytest
import yaml

from chappie_notification.infrastructure.adapters.whitelist_validator_adapter import (
    WhitelistCommandValidatorAdapter,
)


@pytest.fixture
def whitelist_file() -> str:
    """Create a temporary whitelist file for testing."""
    whitelist_data = {
        "allowed_commands": [
            "systemctl *",
            "ls *",
            "cat *",
            "git *",
            "docker *",
            "echo *",
            "python* *",
        ],
        "denied_commands": [
            "rm *",
            "dd *",
            "shutdown *",
            "reboot *",
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(whitelist_data, f)
        return f.name


@pytest.fixture
def validator(whitelist_file: str) -> WhitelistCommandValidatorAdapter:
    return WhitelistCommandValidatorAdapter(whitelist_path=whitelist_file)


class TestWhitelistCommandValidatorAdapter:
    """Tests for WhitelistCommandValidatorAdapter."""

    def test_should_allow_allowed_command(self, validator: WhitelistCommandValidatorAdapter) -> None:
        assert validator.is_allowed("systemctl poweroff") is True
        assert validator.is_allowed("ls -la /home") is True
        assert validator.is_allowed("cat /etc/hosts") is True
        assert validator.is_allowed("git status") is True
        assert validator.is_allowed("echo hello") is True

    def test_should_deny_denied_command(self, validator: WhitelistCommandValidatorAdapter) -> None:
        assert validator.is_allowed("rm -rf /") is False
        assert validator.is_allowed("dd if=/dev/zero of=/dev/sda") is False
        assert validator.is_allowed("shutdown now") is False
        assert validator.is_allowed("reboot") is False

    def test_should_deny_sudo_commands(self, validator: WhitelistCommandValidatorAdapter) -> None:
        assert validator.is_allowed("sudo ls") is False
        assert validator.is_allowed("sudo systemctl restart nginx") is False

    def test_should_deny_empty_command(self, validator: WhitelistCommandValidatorAdapter) -> None:
        assert validator.is_allowed("") is False
        assert validator.is_allowed("   ") is False

    def test_should_deny_unlisted_command(self, validator: WhitelistCommandValidatorAdapter) -> None:
        assert validator.is_allowed("vim /etc/hosts") is False
        assert validator.is_allowed("curl https://example.com") is False

    def test_should_deny_all_when_file_missing(self) -> None:
        validator = WhitelistCommandValidatorAdapter(
            whitelist_path="/nonexistent/path.yaml"
        )
        assert validator.is_allowed("ls") is False
        assert validator.is_allowed("echo hello") is False

    def test_should_pattern_match_with_wildcard(self, validator: WhitelistCommandValidatorAdapter) -> None:
        assert validator.is_allowed("python3 script.py") is True
        assert validator.is_allowed("python -m pytest") is True

    def test_should_allow_sudo_as_argument(self, validator: WhitelistCommandValidatorAdapter) -> None:
        # "sudo" as argument to echo should be allowed (not a sudo command)
        assert validator.is_allowed("echo sudo") is True
