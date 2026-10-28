import asyncio
import os
from datetime import date, timedelta

import aiohttp
from aio_garmin_personal import GarminPersonalClient


async def main():
    key = os.environ["GARMIN_PERSONAL_API_KEY"]
    async with aiohttp.ClientSession() as session:
        client = GarminPersonalClient(session, key)
        ayer = date.today() - timedelta(days=1)
        summary = await client.async_get_daily_summary(ayer)
        print(summary)


asyncio.run(main())