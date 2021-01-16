"""Photo Archive server application."""
import asyncio
import shlex
import logging
import contextlib
import pathlib

import aiofiles
from aiohttp import web

from settings import get_settings


CHUNK_SIZE = 150 * 1024


logger = logging.getLogger()


class PhotoArchive:
    """Route handlers for Photo Archive service."""

    def __init__(self, photos_folder: pathlib.Path, delay: int = 0) -> None:
        """
        :param photos_folder: Folder where photos are stored.
        :param delay: Delay (in seconds) between sending archive chunks. Used for testing.
        """

        self._delay = delay
        self._photos_folder = photos_folder

    async def archivate(self, request: web.Request) -> web.StreamResponse:
        """
        Endpoint for retrieving zipped user's photos.
         Zips folder with user's photos, then sends it to a client in chunks.
        """

        archive_hash = request.match_info.get('archive_hash')
        photos_path = self._photos_folder / archive_hash

        if not photos_path.exists():
            raise web.HTTPNotFound(text='Архив не существует или был удален')

        response = web.StreamResponse()
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = 'attachment'
        await response.prepare(request)

        zip_process = await asyncio.create_subprocess_exec(
            *shlex.split(f'zip -r -j - {photos_path}'),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            while not zip_process.stdout.at_eof():
                chunk = await zip_process.stdout.read(CHUNK_SIZE)
                logger.debug('Sending archive chunk ...')
                await response.write(chunk)
                await asyncio.sleep(self._delay)
        except asyncio.CancelledError:
            logger.debug('Connection terminated')
            raise
        finally:
            if zip_process.returncode is None:
                logger.debug('Killing zip process ...')
                with contextlib.suppress(ProcessLookupError):
                    zip_process.kill()
                await zip_process.communicate()
            return response

    async def handle_index_page(self, request: web.Request) -> web.Response:
        """Index page, used for testing."""

        async with aiofiles.open('photo_archive/index.html', mode='r') as index_file:
            index_contents = await index_file.read()
        return web.Response(text=str(index_contents), content_type='text/html')


def main() -> None:
    settings = get_settings()

    log_level = logging.DEBUG if settings.debug_log else logging.INFO
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log_level
    )

    photo_archive = PhotoArchive(
        photos_folder=settings.photos_folder,
        delay=settings.delay
    )

    logger.debug(f'Starting app with settings: {settings}')
    app = web.Application()
    app.add_routes([
        web.get('/', photo_archive.handle_index_page),
        web.get('/archive/{archive_hash}/', photo_archive.archivate),
    ])
    web.run_app(app)


if __name__ == '__main__':
    main()
