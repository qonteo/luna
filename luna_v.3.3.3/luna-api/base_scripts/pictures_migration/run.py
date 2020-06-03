from functions import migratePictures, logger, checkConnection
import asyncio


async def main():
    logger.debug('Pictures migration starts')

    success, errors = await migratePictures()

    logger.debug(f'Migration complete.\nResults: \nsuccess: {success}; error: {errors}')


if __name__ == '__main__':
    checkConnection()
    asyncio.run(main())
