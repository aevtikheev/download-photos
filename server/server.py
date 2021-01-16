import asyncio
import argparse
import shlex
import pathlib
import logging
import contextlib

import aiofiles
from aiohttp import web


CHUNK_SIZE = 150 * 1024

CMD_DEBUG_LOG = 'debug_log'
CMD_DELAY = 'delay'
CMD_PHOTOS_FOLDER = 'photos_folder'


logger = logging.getLogger()


class PhotosArchive:
    """Handlers for Photos Archive site."""
    def __init__(self, photos_folder, delay=0):
        self._delay = delay
        self._photos_folder = pathlib.Path(photos_folder)

    async def archivate(self, request):
        """Endpoint for zipped user's photos."""
        logger.debug('Hello')
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

    async def handle_index_page(self, request):
        """Main page."""
        async with aiofiles.open('server/index.html', mode='r') as index_file:
            index_contents = await index_file.read()
        return web.Response(text=str(index_contents), content_type='text/html')


def _parse_args():
    """Parse commandline arguments and return them as a dictionary."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug_log',
        action='store_true',
        default=False,
        dest=CMD_DEBUG_LOG,
        help='Enable debug logging'
    )
    parser.add_argument(
        '--delay',
        dest=CMD_DELAY,
        type=int,
        default=0,
        help='Time to wait between sending chunks of zip archive with photos'
    )
    parser.add_argument(
        '--photos_folder',
        dest=CMD_PHOTOS_FOLDER,
        type=str,
        required=True,
        help='Path to the folder where photos are stored'
    )

    return vars(parser.parse_args())


def main():
    args = _parse_args()

    log_level = logging.DEBUG if args[CMD_DEBUG_LOG] else logging.INFO
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log_level
    )

    photos_archive = PhotosArchive(
        photos_folder=args[CMD_PHOTOS_FOLDER],
        delay=args[CMD_DELAY]
    )
    app = web.Application()
    app.add_routes([
        web.get('/', photos_archive.handle_index_page),
        web.get('/archive/{archive_hash}/', photos_archive.archivate),
    ])
    web.run_app(app)


if __name__ == '__main__':
    main()
