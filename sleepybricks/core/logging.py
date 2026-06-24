"""Shared logging setup for sleepybricks."""

import logging


def configureLogging() -> None:
    """Configure application logging once.

    Returns:
        None.
    """

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    # The databricks SDK is chatty at INFO; keep CLI output focused on results.
    logging.getLogger("databricks.sdk").setLevel(logging.WARNING)
