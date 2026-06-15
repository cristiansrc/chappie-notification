"""Whitelist command validator adapter."""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class WhitelistCommandValidatorAdapter:
    """Validates commands against a whitelist YAML file."""

    def __init__(self, whitelist_path: str) -> None:
        """Initialize the validator.

        Args:
            whitelist_path: Path to the commands-whitelist.yaml file.
        """
        self._whitelist_path = whitelist_path
        self._allowed_patterns: list[str] = []
        self._denied_patterns: list[str] = []
        self._loaded = False
        self._load_whitelist()

    def _load_whitelist(self) -> None:
        """Load the whitelist from the YAML file.

        If the file is missing or invalid, denies all commands (fail-safe).
        """
        path = Path(self._whitelist_path)
        if not path.exists():
            logger.warning(
                "Whitelist file not found at %s - denying all commands",
                self._whitelist_path,
            )
            self._loaded = False
            return

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                logger.warning("Invalid whitelist format - denying all commands")
                self._loaded = False
                return

            self._allowed_patterns = data.get("allowed_commands", [])
            self._denied_patterns = data.get("denied_commands", [])
            self._loaded = True

            logger.info(
                "Whitelist loaded: %d allowed patterns, %d denied patterns",
                len(self._allowed_patterns),
                len(self._denied_patterns),
            )

        except Exception as e:
            logger.error(
                "Failed to load whitelist: %s - denying all commands",
                e,
            )
            self._loaded = False

    def is_allowed(self, command: str) -> bool:
        """Check if a command is allowed by the whitelist.

        Args:
            command: The command to validate.

        Returns:
            True if the command is allowed, False otherwise.
        """
        # Fail-safe: deny all if whitelist not loaded
        if not self._loaded:
            logger.warning("Whitelist not loaded - denying command: %s", command)
            return False

        # Strip whitespace
        command = command.strip()
        if not command:
            return False

        # Always deny sudo commands (first word is sudo or command starts with sudo)
        first_word = command.split()[0] if command.split() else ""
        if first_word == "sudo":
            logger.debug("Command denied (uses sudo): %s", command)
            return False

        # Check denied patterns first (they take precedence)
        for pattern in self._denied_patterns:
            if fnmatch.fnmatch(command, pattern):
                logger.debug(
                    "Command denied by pattern '%s': %s",
                    pattern,
                    command,
                )
                return False

        # Check allowed patterns
        for pattern in self._allowed_patterns:
            if fnmatch.fnmatch(command, pattern):
                return True

        logger.debug(
            "Command not matched by any allowed pattern: %s",
            command,
        )
        return False
