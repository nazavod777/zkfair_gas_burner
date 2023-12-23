import asyncio
from itertools import cycle
from sys import stderr

from better_proxy import Proxy
from loguru import logger

from core import start_burner

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    tasks: list = [
        asyncio.create_task(coro=start_burner(private_key=private_key,
                                              proxy=next(proxies_cycled),
                                              semaphore=semaphore)) for private_key in private_keys
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    with open(file='private_keys.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        private_keys: list[str] = [row.strip() if row.strip().startswith('0x') else f'0x{row.strip()}' for row in file]

    with open(file='proxies.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        proxies_list: list[str] = [Proxy.from_str(proxy=row.strip()).as_url for row in file]

    logger.info(f'Загружено {len(private_keys)} Private-Keys | {len(proxies_list)} Proxies')

    threads: int = int(input('\nThreads: '))
    print()

    proxies_cycled: cycle = cycle(proxies_list)
    semaphore: asyncio.Semaphore = asyncio.Semaphore(value=threads)

    asyncio.run(main())

    logger.success('Работа успешно завершена')
    input('\nPress Enter to Exit..')
