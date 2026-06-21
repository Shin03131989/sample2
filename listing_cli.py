#!/usr/bin/env python3
"""
出品サポートCLI - Claude Code Web から直接呼び出すためのスクリプト
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from modules.ebay_api import EbayAPI
from modules.yahoo_api import YahooAPI
from modules.price_analyzer import PriceAnalyzer
from modules.title_generator import TitleGenerator
from modules.listing_generator import ListingGenerator


def run(args):
    features = [f.strip() for f in args.features.split(",") if f.strip()] if args.features else []
    accessories = [a.strip() for a in args.accessories.split(",") if a.strip()] if args.accessories else []

    print("=" * 60)
    print(f"  出品サポート: {args.brand} {args.keyword} {args.model}".strip())
    print("=" * 60)

    # ── 価格相場 ────────────────────────────────────────────────
    print("\n【価格相場分析】")
    ebay_data = EbayAPI(os.getenv("EBAY_APP_ID")).get_completed_prices(args.keyword or args.brand)
    yahoo_data = YahooAPI(os.getenv("YAHOO_APP_ID")).get_market_prices(args.keyword or args.brand)
    analysis = PriceAnalyzer().analyze(ebay_data, yahoo_data, args.rate)

    ebay = analysis["ebay"]
    yahoo = analysis["yahoo"]

    if ebay.get("configured") and not ebay.get("error") and ebay["usd"].get("count", 0) > 0:
        s = ebay["usd"]
        j = ebay["jpy"]
        print(f"  eBay 過去90日実売 ({s['count']}件):")
        print(f"    最安 ${s['min']:.2f}  最高 ${s['max']:.2f}  中央値 ${s['median']:.2f}")
        print(f"    円換算(×{args.rate}) 中央値 ¥{j['median']:,.0f}")
    elif not ebay.get("configured"):
        print("  eBay: APIキー未設定（.envにEBAY_APP_IDを設定すると実売価格を取得できます）")
    else:
        print(f"  eBay: {ebay.get('error', 'データなし')}")

    if yahoo.get("configured") and not yahoo.get("error") and yahoo["stats"].get("count", 0) > 0:
        s = yahoo["stats"]
        print(f"  Yahoo出品価格参考 ({s['count']}件現在出品):")
        print(f"    最安 ¥{s['min']:,.0f}  最高 ¥{s['max']:,.0f}  中央値 ¥{s['median']:,.0f}")
    elif not yahoo.get("configured"):
        print("  Yahoo: APIキー未設定（.envにYAHOO_APP_IDを設定すると参考価格を取得できます）")
    else:
        print(f"  Yahoo: {yahoo.get('error', 'データなし')}")

    rec = analysis.get("recommendations")
    if rec:
        print("\n【推奨出品価格（相場中央値ベース）】")
        y = rec["yahuoku"]
        f = rec["yahoo_flea"]
        e = rec["ebay"]
        print(f"  ヤフオク!    ¥{y['suggested']:,}  → 手数料{y['fee_pct']}%後 約¥{y['net']:,}")
        print(f"  ヤフーフリマ ¥{f['suggested']:,}  → 手数料{f['fee_pct']}%後 約¥{f['net']:,}")
        print(f"  eBay         ${e['suggested_usd']:.2f} → 手数料約{e['fee_pct']}%後 約${e['net_usd']:.2f}")

        print("\n  コンディション別目安:")
        labels = {"new": "新品未使用", "like_new": "未使用に近い", "very_good": "美品",
                  "good": "良品", "acceptable": "ジャンク"}
        adj = rec["condition_adjustments"]
        for key, lbl in labels.items():
            v = adj[key]
            print(f"    {lbl:<12} ヤフオク ¥{v['yahuoku']:,}  eBay ${v['ebay_usd']:.2f}")
    else:
        print("\n  ※ APIキーを設定すると推奨価格が表示されます")

    # ── タイトル ────────────────────────────────────────────────
    titles = TitleGenerator().generate(
        args.keyword, args.brand, args.model,
        args.condition, args.category, features, accessories
    )
    print("\n【出品タイトル】")
    for platform, label in [("yahuoku", "ヤフオク!"), ("yahoo_flea", "ヤフーフリマ"), ("ebay", "eBay")]:
        t = titles[platform]
        warn = " ⚠ 上限超過" if not t["is_valid"] else ""
        print(f"  {label} [{t['length']}/{t['max_length']}文字{warn}]")
        print(f"    {t['title']}")

    # ── 出品詳細文 ───────────────────────────────────────────────
    listings = ListingGenerator().generate(
        args.keyword, args.brand, args.model, args.condition, args.category,
        analysis, args.description, features, accessories, args.defects
    )

    print("\n【出品詳細文】")
    for platform, label in [("yahuoku", "ヤフオク!"), ("yahoo_flea", "ヤフーフリマ"), ("ebay", "eBay")]:
        lst = listings[platform]
        print(f"\n  ── {label} ──")
        print(lst["description"])
        if lst["tips"]:
            print(f"\n  ▶ 出品のコツ:")
            for tip in lst["tips"]:
                print(f"    ・{tip}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="フリマ・オークション出品サポートCLI")
    parser.add_argument("--keyword",     default="", help="商品キーワード（必須）")
    parser.add_argument("--brand",       default="", help="ブランド名")
    parser.add_argument("--model",       default="", help="型番・モデル")
    parser.add_argument("--condition",   default="very_good",
                        choices=["new", "like_new", "very_good", "good", "acceptable"],
                        help="コンディション (default: very_good)")
    parser.add_argument("--category",    default="", help="カテゴリ")
    parser.add_argument("--description", default="", help="商品説明")
    parser.add_argument("--features",    default="", help="特徴（カンマ区切り）")
    parser.add_argument("--accessories", default="", help="付属品（カンマ区切り）")
    parser.add_argument("--defects",     default="", help="傷・汚れの詳細")
    parser.add_argument("--rate",        type=float, default=150.0, help="ドル円レート (default: 150)")

    args = parser.parse_args()

    if not args.keyword and not args.brand:
        parser.error("--keyword または --brand を指定してください")

    run(args)


if __name__ == "__main__":
    main()
