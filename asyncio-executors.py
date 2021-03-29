import asyncio
import concurrent.futures
import contextlib
import time

import httpx
import requests

URL = "http://downloads.local/zoom_0.mp4"


def cpu_bound():
    return sum(x * x for x in range(10 ** 7))


def io_bound():
    with open("/dev/urandom", encoding="latin1") as rb:
        for x in range(1000):
            rb.read(1000000)


def sync_download():
    print("Downloading ...")
    response = requests.get(URL)
    print("Done", response.status_code)


async def async_download():
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
        print("Downloading ...")
        response = await client.get(URL)
        print("Done", response.status_code)


@contextlib.contextmanager
def timeit(name):
    print(f"Run '{name}' ...")
    t1 = time.perf_counter()
    yield
    t2 = time.perf_counter()
    print(f"Processed '{name}' within {t2-t1:.03f}s")


async def aio_main(func):
    with timeit("aio"):
        await asyncio.gather(*(func() for _ in range(10)))


async def straight_main(func):
    # Processed within 12.161s
    loop = asyncio.get_event_loop()

    with timeit("straight"):
        await asyncio.gather(*(loop.run_in_executor(None, func) for _ in range(10)))


async def process_pool_main(func):
    # Processed within 4.668s
    loop = asyncio.get_event_loop()

    with timeit("process pool"), concurrent.futures.ProcessPoolExecutor() as executor:
        aws = [loop.run_in_executor(executor, func) for _ in range(10)]
        await asyncio.gather(*aws)


async def thread_pool_main(func):
    # Processed within 29.141s
    loop = asyncio.get_event_loop()

    with timeit("thread pool"), concurrent.futures.ThreadPoolExecutor() as executor:
        aws = [loop.run_in_executor(executor, func) for _ in range(10)]
        await asyncio.gather(*aws)


if __name__ == "__main__":
    func = io_bound
    # asyncio.run(aio_main(async_download))
    asyncio.run(straight_main(func))
    asyncio.run(process_pool_main(func))
    asyncio.run(thread_pool_main(func))
