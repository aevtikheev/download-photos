"""Settings for Photo Archive app."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from environs import Env


DEFAULT_DEBUG_LOG = False
DEFAULT_DELAY = 0


class ConfigurationError(Exception):
    """Exception for app configuration errors."""


@dataclass
class Settings:
    """App settings."""

    debug_log: bool
    delay: int
    photos_folder: Path

    def __str__(self):
        return (
            f'debug_log: {self.debug_log}, '
            f'delay: {self.delay}, '
            f'photos_folder: {self.photos_folder} '
        )


def _parse_cmd_args() -> argparse.Namespace:
    """Parse commandline arguments and return them as a dictionary."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug_log',
        action='store_true',
        dest='debug_log',
        default=DEFAULT_DEBUG_LOG,
        help='Enable debug logging',
    )
    parser.add_argument(
        '--delay',
        dest='delay',
        type=int,
        default=DEFAULT_DELAY,
        help='Time to wait between sending chunks of zip archive with photos',
    )
    parser.add_argument(
        '--photos_folder',
        dest='photos_folder',
        type=str,
        help='Path to the folder where photos are stored',
    )

    return parser.parse_args()


def _read_cmd_args(cmd_args: argparse.Namespace) -> Settings:
    """
    Extracts app settings from parsed commandline arguments
     and converts them to settings dataclass.
    """

    photos_folder = Path(cmd_args.photos_folder)
    debug_log = cmd_args.debug_log
    delay = cmd_args.delay

    return Settings(
        debug_log=debug_log,
        delay=delay,
        photos_folder=Path(photos_folder)
    )


def _read_env_vars() -> Settings:
    """
    Extracts app settings from environment variables
     and converts them to settings dataclass.
    """

    env = Env()
    env.read_env()
    photos_folder = env('PHOTOS_FOLDER', None)
    if photos_folder is None:
        raise ConfigurationError('Path to photos is not specified')
    photos_folder = Path(photos_folder)
    debug_log = env.bool('DEBUG_LOG', DEFAULT_DEBUG_LOG)
    delay = env.int('DELAY', DEFAULT_DELAY)

    return Settings(
        debug_log=debug_log,
        delay=delay,
        photos_folder=Path(photos_folder)
    )


def get_settings() -> Settings:
    """Read application settings from commandline or environment variables."""

    cmd_args = _parse_cmd_args()
    return _read_cmd_args(cmd_args) if cmd_args.photos_folder else _read_env_vars()
