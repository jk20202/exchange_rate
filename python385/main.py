import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cache import get_rates, get_cache_info, is_cache_stale, refresh_rates, init_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="实时汇率转换 API",
    description="传入金额和货币代码，返回对应的美元金额。汇率每小时自动刷新，数据来自多个免费源聚合。",
    version="1.0.0",
)

scheduler = AsyncIOScheduler()


class ConvertRequest(BaseModel):
    amount: float
    currency: str

class ConvertResponse(BaseModel):
    original_amount: float
    original_currency: str
    usd_amount: float
    exchange_rate: float
    rate_source: str
    rate_age_seconds: float

class RateInfo(BaseModel):
    currency: str
    rate_to_usd: float


@app.on_event("startup")
async def startup():
    init_cache()
    await refresh_rates()

    scheduler.add_job(refresh_rates, "interval", minutes=60, id="refresh_rates")
    scheduler.add_job(_check_stale_refresh, "interval", minutes=5, id="check_stale")
    scheduler.start()
    logger.info("定时刷新任务已启动 (每60分钟刷新，每5分钟检查缓存是否过期)")


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


async def _check_stale_refresh():
    if is_cache_stale():
        logger.info("检测到缓存过期，触发刷新")
        await refresh_rates()


@app.get("/")
async def root():
    return {"message": "实时汇率转换 API 已运行", "docs": "/docs"}


@app.post("/convert", response_model=ConvertResponse)
async def convert_currency(req: ConvertRequest):
    currency = req.currency.upper()
    rates = get_rates()

    if currency == "USD":
        info = get_cache_info()
        return ConvertResponse(
            original_amount=req.amount,
            original_currency="USD",
            usd_amount=req.amount,
            exchange_rate=1.0,
            rate_source=info["source"],
            rate_age_seconds=info["age_seconds"],
        )

    if currency not in rates:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的货币代码: {currency}。支持的货币: {', '.join(sorted(rates.keys()))}",
        )

    rate = rates[currency]
    usd_amount = req.amount / rate
    info = get_cache_info()

    return ConvertResponse(
        original_amount=req.amount,
        original_currency=currency,
        usd_amount=round(usd_amount, 6),
        exchange_rate=rate,
        rate_source=info["source"],
        rate_age_seconds=info["age_seconds"],
    )


@app.get("/rates")
async def list_rates():
    rates = get_rates()
    info = get_cache_info()
    sorted_rates = dict(sorted(rates.items()))
    return {
        "base": "USD",
        "rates": sorted_rates,
        "source": info["source"],
        "currency_count": info["currency_count"],
        "rate_age_seconds": info["age_seconds"],
    }


@app.get("/rates/{currency}")
async def get_single_rate(currency: str):
    currency = currency.upper()
    rates = get_rates()
    if currency not in rates:
        raise HTTPException(status_code=404, detail=f"未找到货币: {currency}")
    info = get_cache_info()
    return {
        "base": "USD",
        "currency": currency,
        "rate": rates[currency],
        "source": info["source"],
        "rate_age_seconds": info["age_seconds"],
    }


@app.post("/refresh")
async def manual_refresh():
    success = await refresh_rates()
    if success:
        return {"message": "汇率刷新成功", **get_cache_info()}
    raise HTTPException(status_code=500, detail="汇率刷新失败，请稍后重试")


@app.get("/health")
async def health():
    info = get_cache_info()
    return {
        "status": "healthy" if info["age_seconds"] < 7200 else "stale",
        **info,
    }
