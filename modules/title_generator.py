from typing import List, Dict

CONDITION_JP = {
    "new": "新品未使用",
    "like_new": "未使用に近い",
    "very_good": "美品",
    "good": "良品",
    "acceptable": "ジャンク",
}

CONDITION_EN = {
    "new": "Brand New",
    "like_new": "Like New",
    "very_good": "Excellent",
    "good": "Good",
    "acceptable": "For Parts",
}

YAHOO_MAX = 65
EBAY_MAX = 80


class TitleGenerator:
    def generate(
        self,
        keyword: str,
        brand: str,
        model: str,
        condition: str,
        category: str,
        features: List[str] = None,
        accessories: List[str] = None,
    ) -> Dict:
        features = features or []
        accessories = accessories or []

        yahoo_title = self._build_yahoo_title(keyword, brand, model, condition, features, accessories)
        ebay_title = self._build_ebay_title(keyword, brand, model, condition, features)

        return {
            "yahuoku": _wrap(yahoo_title, YAHOO_MAX),
            "yahoo_flea": _wrap(yahoo_title, YAHOO_MAX),
            "ebay": _wrap(ebay_title, EBAY_MAX),
        }

    def _build_yahoo_title(
        self,
        keyword: str,
        brand: str,
        model: str,
        condition: str,
        features: List[str],
        accessories: List[str],
    ) -> str:
        cond_word = CONDITION_JP.get(condition, "")
        has_accessories = bool(accessories)

        # Priority order: brand > keyword > model > condition > features > accessories note
        parts_priority = []
        if brand:
            parts_priority.append(brand)
        if keyword:
            # Avoid duplicating brand in keyword
            kw = keyword
            if brand and kw.lower().startswith(brand.lower()):
                kw = kw[len(brand):].strip()
            if kw:
                parts_priority.append(kw)
        if model:
            parts_priority.append(model)
        if cond_word:
            parts_priority.append(cond_word)

        # Build base title
        title = " ".join(parts_priority)

        # Append features if space allows
        for feat in features:
            candidate = f"{title} {feat}"
            if len(candidate) <= YAHOO_MAX:
                title = candidate
            else:
                break

        # Append accessories note if space allows
        if has_accessories:
            candidate = f"{title} 付属品あり"
            if len(candidate) <= YAHOO_MAX:
                title = candidate

        return title

    def _build_ebay_title(
        self,
        keyword: str,
        brand: str,
        model: str,
        condition: str,
        features: List[str],
    ) -> str:
        cond_word = CONDITION_EN.get(condition, "Used")

        parts = []
        if brand:
            parts.append(brand)
        if keyword:
            kw = keyword
            if brand and kw.lower().startswith(brand.lower()):
                kw = kw[len(brand):].strip()
            if kw:
                parts.append(kw)
        if model:
            parts.append(model)
        if cond_word:
            parts.append(cond_word)

        title = " ".join(parts)

        # Append features if space allows
        for feat in features:
            candidate = f"{title} {feat}"
            if len(candidate) <= EBAY_MAX:
                title = candidate
            else:
                break

        # Append Japan if space allows (helps international buyers find Japanese items)
        if "japan" not in title.lower():
            candidate = f"{title} Japan"
            if len(candidate) <= EBAY_MAX:
                title = candidate

        return title


def _wrap(title: str, max_len: int) -> Dict:
    truncated = title[:max_len] if len(title) > max_len else title
    return {
        "title": truncated,
        "length": len(truncated),
        "max_length": max_len,
        "is_valid": len(title) <= max_len,
        "original_length": len(title),
    }
