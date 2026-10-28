"""Baja sueno y actividades con el cliente oficial de Garmin.

Guarda raw_sleep.json y raw_activities.json, e imprime SOLO los nombres de los
campos (no tus valores) para que podamos armar las graficas.
"""
import json
from datetime import date, timedelta

from garmin_personal_api import (
    GarminPersonalApiClient,
    PersonalApiAuthenticator,
    resolve_api_key,
)

DIAS_SUENO = 90
MAX_PAGINAS_ACTIVIDADES = 5


def estructura(obj, ruta="", prof=0, salida=None):
    """Lista las rutas de campos con su tipo, sin mostrar valores."""
    if salida is None:
        salida = []
    if prof > 3:
        return salida
    if isinstance(obj, dict):
        for k, v in obj.items():
            r = f"{ruta}.{k}" if ruta else k
            salida.append(f"{r}: {type(v).__name__}")
            estructura(v, r, prof + 1, salida)
    elif isinstance(obj, list) and obj:
        estructura(obj[0], ruta + "[0]", prof + 1, salida)
    return salida


def primer_registro(datos):
    """Devuelve un registro de ejemplo, sea lista o diccionario con lista."""
    if isinstance(datos, list):
        return datos[0] if datos else None
    if isinstance(datos, dict):
        for v in datos.values():
            if isinstance(v, list) and v:
                return v[0]
    return datos


def main():
    with PersonalApiAuthenticator() as auth:
        token = auth.obtain_token(resolve_api_key())

    hoy = date.today()
    with GarminPersonalApiClient(token.access_token) as client:
        # --- Sueno: ventanas de 30 dias (el limite documentado es 31) ---
        trozos = []
        fin = hoy
        restante = DIAS_SUENO
        while restante > 0:
            largo = min(30, restante)
            ini = fin - timedelta(days=largo - 1)
            trozos.append(client.get_daily_sleep_summaries(ini.isoformat(), fin.isoformat()))
            fin = ini - timedelta(days=1)
            restante -= largo
        with open("raw_sleep.json", "w", encoding="utf-8") as f:
            json.dump(trozos, f, indent=1)
        print("Sueno guardado en raw_sleep.json")

        # --- Actividades: paginamos de 100 en 100 ---
        actividades = []
        desde = (hoy - timedelta(days=DIAS_SUENO)).isoformat()
        for pagina in range(MAX_PAGINAS_ACTIVIDADES):
            lote = client.search_activities(
                start=pagina * 100, limit=100,
                start_date=desde, end_date=hoy.isoformat(),
            )
            registros = lote if isinstance(lote, list) else (
                next((v for v in lote.values() if isinstance(v, list)), [])
                if isinstance(lote, dict) else []
            )
            actividades.extend(registros)
            if len(registros) < 100:
                break
        with open("raw_activities.json", "w", encoding="utf-8") as f:
            json.dump(actividades, f, indent=1)
        print(f"Actividades guardadas en raw_activities.json ({len(actividades)})")

    print("\n=== CAMPOS DE SUENO (un registro) ===")
    for linea in estructura(primer_registro(trozos[0])):
        print(linea)
    print("\n=== CAMPOS DE ACTIVIDADES (un registro) ===")
    if actividades:
        for linea in estructura(actividades[0]):
            print(linea)
    else:
        print("No hay actividades en este periodo.")


main()