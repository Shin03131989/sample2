import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from modules.ebay_api import EbayAPI
from modules.yahoo_api import YahooAPI
from modules.price_analyzer import PriceAnalyzer
from modules.title_generator import TitleGenerator
from modules.listing_generator import ListingGenerator

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze_prices():
    data = request.get_json(force=True)
    keyword = data.get("keyword", "").strip()
    usd_to_jpy = float(data.get("usd_to_jpy", 150))

    if not keyword:
        return jsonify({"success": False, "error": "キーワードを入力してください"}), 400

    ebay_api = EbayAPI(os.getenv("EBAY_APP_ID"))
    yahoo_api = YahooAPI(os.getenv("YAHOO_APP_ID"))

    ebay_data = ebay_api.get_completed_prices(keyword)
    yahoo_data = yahoo_api.get_market_prices(keyword)

    analyzer = PriceAnalyzer()
    analysis = analyzer.analyze(ebay_data, yahoo_data, usd_to_jpy)

    return jsonify({"success": True, "analysis": analysis})


@app.route("/api/generate", methods=["POST"])
def generate_listing():
    data = request.get_json(force=True)

    keyword = data.get("keyword", "").strip()
    brand = data.get("brand", "").strip()
    model = data.get("model", "").strip()
    condition = data.get("condition", "good")
    category = data.get("category", "")
    description = data.get("description", "").strip()
    defects = data.get("defects", "").strip()
    price_analysis = data.get("price_analysis") or {}

    raw_features = data.get("features", "")
    raw_accessories = data.get("accessories", "")
    features = [f.strip() for f in raw_features.splitlines() if f.strip()] if isinstance(raw_features, str) else raw_features
    accessories = [a.strip() for a in raw_accessories.splitlines() if a.strip()] if isinstance(raw_accessories, str) else raw_accessories

    if not keyword and not brand:
        return jsonify({"success": False, "error": "商品名またはブランドを入力してください"}), 400

    title_gen = TitleGenerator()
    titles = title_gen.generate(keyword, brand, model, condition, category, features, accessories)

    listing_gen = ListingGenerator()
    listings = listing_gen.generate(
        keyword, brand, model, condition, category,
        price_analysis, description, features, accessories, defects,
    )

    return jsonify({"success": True, "titles": titles, "listings": listings})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
