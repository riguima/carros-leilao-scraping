import asyncio

from datetime import datetime

from carros_leilao_scraping.browser import get_plates_of_year


async def main():
    for c in range(2011, datetime.now().year + 1):
        await get_plates_of_year(c)


if __name__ == '__main__':
    asyncio.run(main())
