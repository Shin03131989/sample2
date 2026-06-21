from typing import Dict, List

CONDITION_DISPLAY_JP = {
    "new": "新品・未使用",
    "like_new": "未使用に近い（目立った傷や汚れなし）",
    "very_good": "目立った傷や汚れなし",
    "good": "多少の傷や汚れあり",
    "acceptable": "傷や汚れあり（ジャンク・現状品）",
}

CONDITION_DISPLAY_EN = {
    "new": "New",
    "like_new": "Like New",
    "very_good": "Very Good",
    "good": "Good",
    "acceptable": "Acceptable / For Parts",
}


class ListingGenerator:
    def generate(
        self,
        keyword: str,
        brand: str,
        model: str,
        condition: str,
        category: str,
        price_analysis: Dict,
        description: str = "",
        features: List[str] = None,
        accessories: List[str] = None,
        defects: str = "",
    ) -> Dict:
        features = features or []
        accessories = accessories or []
        item_name = " ".join(filter(None, [brand, keyword, model]))

        return {
            "yahuoku": self._yahuoku(item_name, condition, description, features, accessories, defects, price_analysis),
            "yahoo_flea": self._yahoo_flea(item_name, condition, description, features, accessories, defects, price_analysis),
            "ebay": self._ebay(keyword, brand, model, condition, description, features, accessories, defects, price_analysis),
        }

    def _yahuoku(self, item_name, condition, description, features, accessories, defects, analysis):
        cond = CONDITION_DISPLAY_JP.get(condition, "中古品")
        rec = (analysis.get("recommendations") or {}).get("yahuoku", {})
        lines = []
        lines.append(f"■商品名\n{item_name}")
        lines.append(f"\n■状態\n{cond}")

        if description:
            lines.append(f"\n■商品説明\n{description}")

        if features:
            lines.append("\n■特徴・セールスポイント")
            lines += [f"・{f}" for f in features]

        if accessories:
            lines.append("\n■付属品")
            lines += [f"・{a}" for a in accessories]
        else:
            lines.append("\n■付属品\n記載のあるもの以外は付属しません")

        if defects:
            lines.append(f"\n■傷・汚れの詳細\n{defects}")

        lines.append("\n■注意事項")
        lines.append("・中古品のため、完璧をお求めの方はご遠慮ください")
        lines.append("・写真でご確認の上、ご入札ください")
        lines.append("・落札後のキャンセルはお断りしております")
        lines.append("・ノークレーム・ノーリターンでお願いします")

        tips = [
            "カテゴリを正確に設定すると検索表示が改善されます",
            "写真は最大10枚（正面・背面・側面・傷箇所を必ず撮影）",
            "開始価格を1円にすると注目度が上がりますが、即決価格も設定を推奨",
            "送料込みにすると検索結果で優遇される場合があります",
            "出品期間は7日間が標準、土日終了で入札が増えやすい傾向があります",
        ]
        if rec:
            tips.insert(0, f"推奨出品価格：¥{rec.get('suggested', 0):,}（手数料{rec.get('fee_pct', 0)}%控除後 約¥{rec.get('net', 0):,}）")

        return {"description": "\n".join(lines), "tips": tips}

    def _yahoo_flea(self, item_name, condition, description, features, accessories, defects, analysis):
        cond = CONDITION_DISPLAY_JP.get(condition, "中古品")
        rec = (analysis.get("recommendations") or {}).get("yahoo_flea", {})
        lines = []
        lines.append(item_name)
        lines.append(f"\n状態：{cond}")

        if description:
            lines.append(f"\n{description}")

        if features:
            lines.append("\n【特徴】")
            lines += [f"・{f}" for f in features]

        if accessories:
            lines.append("\n【付属品】")
            lines += [f"・{a}" for a in accessories]
        else:
            lines.append("\n【付属品】\n本体のみ（記載以外の付属品はありません）")

        if defects:
            lines.append(f"\n【状態の詳細】\n{defects}")

        lines.append("\n【お取引について】")
        lines.append("・プロフィールをお読みの上、ご購入ください")
        lines.append("・写真をよくご確認の上、ご購入をお願いします")
        lines.append("・中古品のため、完璧をお求めの方はご遠慮ください")
        lines.append("・購入後のキャンセルはお断りしております")

        tips = [
            "プロフィールに支払い・発送ポリシーを記載すると安心感が増します",
            "写真は明るい場所で白背景を使用すると映えます（最大10枚）",
            "ヤフネコ!パック（ネコポス・宅急便コンパクト）を使うと送料が安定します",
            "値下げ交渉に備えて希望額より5〜10%高めに設定するのも一手です",
            "コメントへの返信は素早く行うと成約率が上がります",
        ]
        if rec:
            tips.insert(0, f"推奨出品価格：¥{rec.get('suggested', 0):,}（手数料{rec.get('fee_pct', 0)}%控除後 約¥{rec.get('net', 0):,}）")

        return {"description": "\n".join(lines), "tips": tips}

    def _ebay(self, keyword, brand, model, condition, description, features, accessories, defects, analysis):
        cond_en = CONDITION_DISPLAY_EN.get(condition, "Used")
        item_name_en = " ".join(filter(None, [brand, keyword, model]))
        rec = (analysis.get("recommendations") or {}).get("ebay", {})

        lines = []
        lines.append(f"<h2>{item_name_en} | {cond_en} | Ships from Japan</h2>")

        if description:
            lines.append(f"<p>{description}</p>")

        lines.append("<h3>Item Specifications</h3>")
        lines.append("<table>")
        if brand:
            lines.append(f"<tr><th>Brand</th><td>{brand}</td></tr>")
        if model:
            lines.append(f"<tr><th>Model</th><td>{model}</td></tr>")
        lines.append(f"<tr><th>Condition</th><td>{cond_en}</td></tr>")
        lines.append("<tr><th>Country/Region of Manufacture</th><td>Japan</td></tr>")
        for feat in features:
            lines.append(f"<tr><th></th><td>{feat}</td></tr>")
        lines.append("</table>")

        if accessories:
            lines.append("<h3>What's in the Box</h3><ul>")
            lines += [f"<li>{a}</li>" for a in accessories]
            lines.append("</ul>")
        else:
            lines.append("<h3>What's in the Box</h3><p>Item only (no additional accessories unless specified)</p>")

        if defects:
            lines.append(f"<h3>Condition Notes</h3><p>{defects}</p>")

        lines.append("<h3>Shipping &amp; Handling</h3>")
        lines.append("<p>All items ship from Japan. We use Japan Post EMS or ePacket for reliable, trackable international delivery. "
                     "Tracking numbers are provided for all shipments. Please allow 7–21 business days for delivery.</p>")
        lines.append("<p><strong>Note:</strong> Buyers are responsible for any import duties, customs fees, or local taxes.</p>")

        lines.append("<h3>Payment</h3>")
        lines.append("<p>We accept PayPal and eBay-managed payments. Payment is expected within 3 days of purchase.</p>")

        lines.append("<h3>Returns</h3>")
        lines.append("<p>We accept returns within 30 days if the item is not as described. "
                     "Please contact us before opening a return case.</p>")

        lines.append("<p><em>All photos show the actual item you will receive. "
                     "Please review all photos carefully before purchasing.</em></p>")

        tips = [
            "Item Specifics（商品詳細情報）を必ず埋めてください—検索順位に直結します",
            "写真は最大12枚、推奨1600×1200px以上（白背景 or 無地背景）",
            "eBay Global Shipping Program (GSP) を利用すると海外発送リスクを軽減できます",
            "コンディションは eBay 規定の5段階（New / Like New / Very Good / Good / Acceptable）で正確に設定",
            "プロモーテッドリスティング（広告）で露出度を上げることができます（費用は落札時のみ）",
            "返品受付（30日）を設定すると検索結果で上位表示されやすくなります",
        ]
        if rec:
            tips.insert(0, f"推奨出品価格：${rec.get('suggested_usd', 0):.2f} USD"
                          f"（手数料約{rec.get('fee_pct', 0)}%控除後 約${rec.get('net_usd', 0):.2f}）")

        return {"description": "\n".join(lines), "tips": tips}
