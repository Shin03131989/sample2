import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

YAHOO_SHOPPING_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"


class YahooAPI:
    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id
        self.configured = bool(app_id)

    def get_market_prices(self, query: str) -> dict:
        if not self.configured:
            return {
                "configured": False,
                "error": "Yahoo App ID が設定されていません。.env ファイルに YAHOO_APP_ID を設定してください。",
                "prices": [],
            }

        params = {
            "appid": self.app_id,
            "query": query,
            "hits": 50,
            "sort": "-sold",
            "results": 1,
        }

        try:
            resp = requests.get(YAHOO_SHOPPING_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            hits = data.get("hits", [])
            prices = []
            for hit in hits:
                price = hit.get("price")
                if price and price > 0:
                    prices.append({
                        "price": float(price),
                        "currency": "JPY",
                        "title": hit.get("name", ""),
                        "store": hit.get("store", {}).get("name", ""),
                    })

            return {
                "configured": True,
                "prices": prices,
                "total_count": data.get("totalResultsAvailable", 0),
                "currency": "JPY",
                "note": "Yahooショッピングの現在出品価格（販売済み価格ではありません）",
            }

        except requests.exceptions.Timeout:
            return {"configured": True, "error": "Yahoo API タイムアウト", "prices": []}
        except Exception as e:
            logger.error("Yahoo API error: %s", e)
            return {"configured": True, "error": str(e), "prices": []}
