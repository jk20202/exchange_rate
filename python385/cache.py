import logging
import time
from typing import Optional, Dict

from fetcher import fetch_all_rates

logger = logging.getLogger(__name__)

_cache: Dict[str, float] = {}
_cache_source: str = "none"
_cache_time: float = 0.0
_next_update: float = 0.0
_refresh_interval: float = 3600.0

INITIAL_RATES: Dict[str, float] = {
    "USD": 1.0,
    "CNY": 7.18,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.5,
    "KRW": 1360.0,
    "HKD": 7.82,
    "TWD": 32.5,
    "SGD": 1.34,
    "AUD": 1.53,
    "CAD": 1.37,
    "CHF": 0.88,
    "INR": 83.5,
    "RUB": 92.0,
    "THB": 36.0,
    "MYR": 4.72,
    "PHP": 56.5,
    "VND": 24500.0,
    "IDR": 15800.0,
    "BRL": 4.97,
    "MXN": 17.15,
    "NZD": 1.63,
    "SEK": 10.8,
    "NOK": 10.6,
    "DKK": 6.88,
    "ZAR": 18.5,
    "TRY": 32.0,
    "PLN": 4.02,
    "CZK": 22.8,
    "ILS": 3.72,
    "AED": 3.67,
    "SAR": 3.75,
}


def get_rates() -> Dict[str, float]:
    return _cache.copy()


def get_cache_info() -> Dict:
    now = time.time()
    age = now - _cache_time if _cache_time > 0 else -1
    return {
        "source": _cache_source,
        "age_seconds": round(age, 1),
        "currency_count": len(_cache),
        "next_update_in_seconds": round(max(0, _next_update - now), 1),
    }


def is_cache_stale() -> bool:
    return time.time() >= _next_update


async def refresh_rates() -> bool:
    global _cache, _cache_source, _cache_time, _next_update

    logger.info("开始刷新汇率数据...")
    rates, source, next_update = await fetch_all_rates()

    if rates and len(rates) > 5:
        _cache = rates
        _cache_source = source
        _cache_time = time.time()
        _next_update = next_update or (time.time() + _refresh_interval)
        logger.info(f"汇率刷新成功: {len(rates)} 个币种, 来源={source}")
        return True
    else:
        logger.warning("汇率刷新失败，保留旧缓存")
        _next_update = time.time() + 300
        return False


def init_cache():
    global _cache, _cache_source, _cache_time, _next_update
    _cache = INITIAL_RATES.copy()
    _cache_source = "hardcoded_fallback"
    _cache_time = time.time()
    _next_update = 0
    logger.info(f"初始化缓存: {len(_cache)} 个币种 (硬编码兜底数据)")
