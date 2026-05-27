# 实时汇率转换 API

基于 FastAPI 开发的实时汇率转换 API，支持多数据源聚合，本地缓存，定时更新。

## 支持的 Python 版本

Python 3.8 及以上版本

## 功能特性

- 🎯 **多数据源聚合**：同时从 ExchangeRate-API 和 Frankfurter 拉取汇率，自动选最优源
- 💎 **本地缓存**：内存存储汇率，毫秒级响应
- 🔄 **定时更新**：每小时自动刷新汇率，确保数据时效
- 📊 **健康监控**：实时检查数据源状态，自动降级
- 📦 **开箱即用**：内置 30+ 常用货币作为兜底

## 快速开始

### 1. 安装依赖

```bash
cd exchange_rate
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / MacOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 上运行

## API 接口文档

访问 `http://localhost:8000/docs` 查看完整的 Swagger 文档

### 接口列表

| 接口 | 方法 | 说明 | 请求示例 |
|------|------|------|----------|
| `/convert` | POST | 货币转美元 | `{"amount": 1000, "currency": "CNY"}` |
| `/rates` | GET | 获取所有汇率 | — |
| `/rates/{currency}` | GET | 获取单个货币汇率 | `/rates/CNY` |
| `/refresh` | POST | 手动刷新汇率 | — |
| `/health` | GET | 健康检查 | — |

### 转换接口示例

**请求：**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000, "currency": "CNY"}'
```

**响应：**
```json
{
    "original_amount": 1000.0,
    "original_currency": "CNY",
    "usd_amount": 147.086813,
    "exchange_rate": 6.798706,
    "rate_source": "ExchangeRate-API",
    "rate_age_seconds": 12.3
}
```

## 支持的主要货币

| 货币代码 | 名称 |
|----------|------|
| USD | 美元 |
| CNY | 人民币 |
| EUR | 欧元 |
| GBP | 英镑 |
| JPY | 日元 |
| KRW | 韩元 |
| HKD | 港币 |
| TWD | 新台币 |
| SGD | 新加坡元 |
| AUD | 澳元 |
| CAD | 加元 |
| CHF | 瑞士法郎 |
| INR | 印度卢比 |
| RUB | 俄罗斯卢布 |
| ... | 还有 150+ 货币 |

## 项目结构

```
exchange_rate/
├── main.py          # FastAPI 主程序
├── fetcher.py       # 数据源获取模块
├── cache.py         # 缓存管理模块
├── requirements.txt # 依赖列表
└── README.md        # 项目文档
```

## 数据源说明

| 数据源 | 更新频率 | 币种数量 | 说明 |
|--------|----------|----------|------|
| ExchangeRate-API | 每日更新 | 160+ | 免费公开 API，无 Key |
| Frankfurter | 每日更新 | 160+ | 开源数据 API，基于各国央行数据 |

## 常见问题

**Q：汇率不是实时更新吗？**

A：免费数据源通常每日更新一次，API 每 1 小时同步一次新数据。

**Q：如何实现真正的小时级更新？**

A：可以升级到 ExchangeRate-API Pro（$10/月），或者付费数据源。

## License

MIT
