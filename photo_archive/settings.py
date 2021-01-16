"""Settings for Photo Archive app."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from environs import Env


ARG_DEBUG_LOG = 'debug_log'
ARG_DELAY = 'delay'
ARG_PHOTOS_FOLDER = 'photos_folder'


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


def _parse_cmd_args() -> dict:
    """Parse commandline arguments and return them as a dictionary."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug_log',
        action='store_true',
        dest=ARG_DEBUG_LOG,
        help='Enable debug logging'
    )
    parser.add_argument(
        '--delay',
        dest=ARG_DELAY,
        type=int,
        help='Time to wait between sending chunks of zip archive with photos'
    )
    parser.add_argument(
        '--photos_folder',
        dest=ARG_PHOTOS_FOLDER,
        type=str,
        help='Path to the folder where photos are stored'
    )

    return vars(parser.parse_args())


def get_settings() -> Settings:
    """Read application settings from commandline or environment variables."""

    default_debug_log = False
    default_delay = 0

    cmd_args = _parse_cmd_args()
    if any(cmd_args.values()):
        if not cmd_args[ARG_PHOTOS_FOLDER]:
            raise ConfigurationError('Path to photos is not specified')
        photos_folder = Path(cmd_args[ARG_PHOTOS_FOLDER])
        debug_log = cmd_args[ARG_DEBUG_LOG] if cmd_args[ARG_DEBUG_LOG] else default_debug_log
        delay = cmd_args[ARG_DELAY] if cmd_args[ARG_DELAY] else default_delay
    else:
        env = Env()
        env.read_env()
        photos_folder = env('PHOTOS_FOLDER', None)
        if photos_folder is None:
            raise ConfigurationError('Path to photos is not specified')
        photos_folder = Path(photos_folder)
        debug_log = env.bool('DEBUG_LOG', default_debug_log)
        delay = env.int('DELAY', default_delay)

    return Settings(
        debug_log=debug_log,
        delay=delay,
        photos_folder=Path(photos_folder)
    )
