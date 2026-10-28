import asyncio
import dataclasses
import json
import os
from datetime import date, timedelta

import aiohttp
from aio_garmin_personal import GarminPersonalClient

DIAS = 30


async def main():
    key = os.environ["GARMIN_PERSONAL_API_KEY"]
    filas = []
    async with aiohttp.ClientSession() as session:
        client = GarminPersonalClient(session, key)
        for i in range(DIAS, 0, -1):
            dia = date.today() - timedelta(days=i)
            try:
                s = await client.async_get_daily_summary(dia)
            except Exception as e:
                print(dia, "error:", type(e).__name__)
                continue
            if s is None:
                print(dia, "sin datos")
                continue
            fila = dataclasses.asdict(s)
            fila["calendar_date"] = dia.isoformat()
            # quitamos datos que no hacen falta
            for campo in ("user_profile_id", "display_name", "last_sync"):
                fila.pop(campo, None)
            filas.append(fila)
            print(dia, "ok")
            await asyncio.sleep(0.5)

    with open("garmin_data.json", "w") as f:
        json.dump(filas, f, indent=1)
    print("Guardados", len(filas), "dias en garmin_data.json")


asyncio.run(main())
