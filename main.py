"""GUI entry point for RotorDyn Calculator."""

import logging.config
import sys

# When running as a PyInstaller bundle, uvicorn's custom formatter classes
# may fail to import. Override with a simple config before anything else.
if getattr(sys, "frozen", False):
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(levelname)s: %(message)s",
            },
            "access": {
                "format": "%(levelname)s: %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    })

from rotordyn.gui.app import run

if __name__ == "__main__":
    run()
