"""Start Cumulus."""
import argparse
import logging
import sys

from cumulus.config import CumulusConfig
from .const import REQUIRED_PYTHON_VER
from .core import run


def validate_python() -> None:
    """
    Validate that the right Python version is running.
    """
    if sys.version_info[:3] < REQUIRED_PYTHON_VER:
        logging.error(
            "Home Assistant requires at least Python "
            f"{REQUIRED_PYTHON_VER[0]}.{REQUIRED_PYTHON_VER[1]}.{REQUIRED_PYTHON_VER[2]}"
        )
        sys.exit(1)


def setup_logging(level: str) -> None:
    logging.basicConfig(stream=sys.stdout, level=level.upper())


def get_arguments() -> argparse.Namespace:
    """
    Get parsed passed in arguments.
    """
    parser = argparse.ArgumentParser(
        description="Cumulus: Free Home Cloud."
    )

    parser.add_argument(
        "-c",
        "--config",
        default="/data",
        help="Directory that contains the Cumulus configuration"
    )
    return parser.parse_args()


def main() -> int:
    """
    Start Cumulus.
    """
    args = get_arguments()
    config = CumulusConfig(args.config)

    setup_logging(config.log_level)
    validate_python()

    logging.debug(f"Loaded config={config}")
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
