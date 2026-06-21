import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

FINDING_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"


class EbayAPI:
    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id
        self.configured = bool(app_id)

    def get_completed_prices(self, keywords: str, days: int = 90) -> dict:
        if not self.configured:
            return {
                "configured": False,
                "error": "eBay App ID が設定されていません。.env ファイルに EBAY_APP_ID を設定してください。",
                "prices": [],
            }

        end_time_from = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": keywords,
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "itemFilter(1).name": "EndTimeFrom",
            "itemFilter(1).value": end_time_from,
            "sortOrder": "EndTimeSoonest",
            "paginationInput.entriesPerPage": "100",
        }

        try:
            resp = requests.get(FINDING_API_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            root = data.get("findCompletedItemsResponse", [{}])[0]
            if root.get("ack", [""])[0] not in ("Success", "Warning"):
                error_msg = root.get("errorMessage", [{}])[0].get("error", [{}])[0].get("message", ["Unknown error"])[0]
                return {"configured": True, "error": f"eBay API エラー: {error_msg}", "prices": []}

            items = root.get("searchResult", [{}])[0].get("item", [])
            total = int(root.get("paginationOutput", [{}])[0].get("totalEntries", ["0"])[0])

            prices = []
            for item in items:
                selling = item.get("sellingStatus", [{}])[0]
                price_node = selling.get("currentPrice", [{}])[0]
                price = float(price_node.get("__value__", 0))
                currency = price_node.get("@currencyId", "USD")
                title = item.get("title", [""])[0]
                end_time = item.get("listingInfo", [{}])[0].get("endTime", [""])[0]

                if price > 0:
                    prices.append({
                        "price": price,
                        "currency": currency,
                        "title": title,
                        "end_time": end_time,
                    })

            return {
                "configured": True,
                "prices": prices,
                "total_count": total,
                "currency": "USD",
                "period_days": days,
            }

        except requests.exceptions.Timeout:
            return {"configured": True, "error": "eBay API タイムアウト", "prices": []}
        except Exception as e:
            logger.error("eBay API error: %s", e)
            return {"configured": True, "error": str(e), "prices": []}
