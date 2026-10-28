import asyncio
import os
from datetime import date

import aiohttp
from aio_garmin_personal import GarminPersonalClient


async def main():
    key = os.environ["GARMIN_PERSONAL_API_KEY"]
    async with aiohttp.ClientSession() as session:
        client = GarminPersonalClient(session, key)
        summary = await client.async_get_daily_summary(date.today())
        if summary is None:
            print("Conexion OK, pero no hay resumen para hoy todavia.")
        else:
            print("Pasos:", summary.total_steps)
            print("Calorias totales:", summary.total_kilocalories)
            print("Calorias activas:", summary.active_kilocalories)


asyncio.run(main())