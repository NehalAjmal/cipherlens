"""Centralized logging configuration for CipherLens.

Every module in cipherlens/ uses this logger — no print() allowed.
See ARCHITECTURE.md §5 and AI_RULES.md rule 14.

Usage:
    from cipherlens.utils.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("message")
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for the given module name.

    Creates a stderr handler with a standard format on first call for
    each name; subsequent calls return the existing logger.

    Args:
        name: The module name (typically ``__name__``).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
