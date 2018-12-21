import asyncio


def ensure_future_with_log(cor, *, logger, message):

    def _done_callback(fut):
        try:
            fut.result()
        except Exception:
            logger.warn(message, exc_info=True)

    asyncio.ensure_future(cor) \
        .add_done_callback(_done_callback)


async def gather_with_log(coros, *, logger):
    task_results = await asyncio.gather(*coros, return_exceptions=True)
    for result in task_results:
        try:
            if isinstance(result, Exception):
                raise result
        except Exception:
            logger.warn('Error from asyncio.gather()', exc_info=True)
