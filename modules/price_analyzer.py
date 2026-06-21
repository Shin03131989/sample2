import statistics
from typing import List, Dict, Optional

# Platform fee rates
FEES = {
    "yahuoku": 0.088,       # 8.8% (Yahoo!プレミアム会員)
    "yahoo_flea": 0.05,     # 5%
    "ebay": 0.1325,         # 13.25% final value fee (most categories)
    "ebay_intl": 0.0165,    # +1.65% international buyer surcharge
}

CONDITION_ADJUSTMENTS = {
    "new": 0.0,
    "like_new": -0.05,
    "very_good": -0.15,
    "good": -0.25,
    "acceptable": -0.40,
}


def _stats(prices: List[float]) -> Dict:
    if not prices:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "stdev": None}
    return {
        "count": len(prices),
        "min": round(min(prices), 2),
        "max": round(max(prices), 2),
        "mean": round(statistics.mean(prices), 2),
        "median": round(statistics.median(prices), 2),
        "stdev": round(statistics.stdev(prices), 2) if len(prices) > 1 else 0,
    }


def _round_price(price: float, unit: int = 100) -> int:
    return int(round(price / unit) * unit)


class PriceAnalyzer:
    def analyze(self, ebay_data: Dict, yahoo_data: Dict, usd_to_jpy: float = 150) -> Dict:
        ebay_prices_usd = [item["price"] for item in ebay_data.get("prices", [])]
        ebay_prices_jpy = [p * usd_to_jpy for p in ebay_prices_usd]

        yahoo_prices_jpy = [item["price"] for item in yahoo_data.get("prices", [])]

        ebay_stats_usd = _stats(ebay_prices_usd)
        ebay_stats_jpy = _stats(ebay_prices_jpy)
        yahoo_stats = _stats(yahoo_prices_jpy)

        # Base price for JPY recommendations: prefer Yahoo sold data, fall back to eBay converted
        base_jpy = yahoo_prices_jpy if yahoo_prices_jpy else ebay_prices_jpy

        recommendations = self._build_recommendations(base_jpy, ebay_prices_usd, usd_to_jpy)

        return {
            "ebay": {
                "usd": ebay_stats_usd,
                "jpy": ebay_stats_jpy,
                "configured": ebay_data.get("configured", False),
                "error": ebay_data.get("error"),
                "total_count": ebay_data.get("total_count", 0),
                "period_days": ebay_data.get("period_days", 90),
                "prices_chart": [round(p, 2) for p in sorted(ebay_prices_usd)],
            },
            "yahoo": {
                "stats": yahoo_stats,
                "configured": yahoo_data.get("configured", False),
                "error": yahoo_data.get("error"),
                "note": yahoo_data.get("note", ""),
                "prices_chart": sorted(yahoo_prices_jpy),
            },
            "recommendations": recommendations,
            "usd_to_jpy": usd_to_jpy,
        }

    def _build_recommendations(
        self, base_jpy: List[float], base_usd: List[float], usd_to_jpy: float
    ) -> Optional[Dict]:
        if not base_jpy and not base_usd:
            return None

        if base_jpy:
            median_jpy = statistics.median(base_jpy)
        else:
            median_jpy = statistics.median(base_usd) * usd_to_jpy

        median_usd = median_jpy / usd_to_jpy

        yahuoku_fee = FEES["yahuoku"]
        flea_fee = FEES["yahoo_flea"]
        ebay_fee = FEES["ebay"] + FEES["ebay_intl"]

        return {
            "base_median_jpy": _round_price(median_jpy),
            "base_median_usd": round(median_usd, 2),
            "yahuoku": {
                "suggested": _round_price(median_jpy),
                "net": _round_price(median_jpy * (1 - yahuoku_fee)),
                "fee_pct": int(yahuoku_fee * 100),
                "fee_note": "Yahoo!プレミアム会員 8.8%（非会員 10%）",
            },
            "yahoo_flea": {
                "suggested": _round_price(median_jpy),
                "net": _round_price(median_jpy * (1 - flea_fee)),
                "fee_pct": int(flea_fee * 100),
                "fee_note": "販売手数料 5%",
            },
            "ebay": {
                "suggested_usd": round(median_usd, 2),
                "suggested_jpy": _round_price(median_jpy),
                "net_usd": round(median_usd * (1 - ebay_fee), 2),
                "net_jpy": _round_price(median_jpy * (1 - ebay_fee)),
                "fee_pct": round(ebay_fee * 100, 1),
                "fee_note": "落札手数料 13.25% + 海外バイヤー追加料 1.65%",
            },
            "condition_adjustments": {
                label: {
                    "yahuoku": _round_price(median_jpy * (1 + adj)),
                    "yahoo_flea": _round_price(median_jpy * (1 + adj)),
                    "ebay_usd": round(median_usd * (1 + adj), 2),
                }
                for label, adj in CONDITION_ADJUSTMENTS.items()
            },
        }
