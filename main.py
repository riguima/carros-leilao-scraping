import asyncio

from placas_scraping.browser import get_plates_of_year


async def main():
    for c in range(2011, 2024):
        plates = await get_plates_of_year(c)


if __name__ == '__main__':
    asyncio.run(main())
