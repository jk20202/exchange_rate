import asyncio
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SOURCES = [
    {
        "name": "ExchangeRate-API",
        "url": "https://open.er-api.com/v6/latest/USD",
        "parser": "_parse_er_api",
    },
    {
        "name": "Frankfurter",
        "url": "https://api.frankfurter.dev/v2/rates?base=USD",
        "parser": "_parse_frankfurter",
    },
]


def _parse_er_api(data: dict) -> dict[str, float]:
    rates = data.get("rates", {})
    return {k: float(v) for k, v in rates.items() if isinstance(v, (int, float))}


def _parse_frankfurter(data: list) -> dict[str, float]:
    result = {}
    if isinstance(data, list):
        for item in data:
            quote = item.get("quote")
            rate = item.get("rate")
            if quote and rate:
                result[quote] = float(rate)
    return result


async def fetch_from_source(client: httpx.AsyncClient, source: dict) -> Optional[dict[str, float]]:
    try:
        resp = await client.get(source["url"], timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        parser = globals().get(source["parser"])
        if parser:
            rates = parser(data)
            if rates:
                logger.info(f"[{source['name']}] 获取到 {len(rates)} 个币种汇率")
                return rates
    except Exception as e:
        logger.warning(f"[{source['name']}] 获取失败: {e}")
    return None


async def fetch_all_rates() -> tuple[dict[str, float], str, Optional[float]]:
    best_rates: dict[str, float] = {}
    best_source = "none"
    best_next_update: Optional[float] = None

    async with httpx.AsyncClient() as client:
        tasks = [fetch_from_source(client, s) for s in SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception) or result is None:
                continue
            source_name = SOURCES[i]["name"]
            if len(result) > len(best_rates):
                best_rates = result
                best_source = source_name

    if best_rates:
        best_rates["USD"] = 1.0
        best_next_update = time.time() + 3600

    return best_rates, best_source, best_next_update
