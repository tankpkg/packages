#!/usr/bin/env python3
"""Enrich existing product data with live prices and images.

Usage:
    python3 enrich_data.py /tmp/product-research/data.json [OPTIONS]

Reads a data.json file (as produced by the product-buying-researcher skill),
then for each product:
  1. Searches for current prices across retailers
  2. Updates buy links with live prices
  3. Adds product images if missing

Sources (tried in order):
    1. Google Shopping via SerpAPI  (needs SERPAPI_API_KEY) — prices + images
    2. Amazon via amzpy             (free) — Amazon prices + images

Options:
    --dry-run          Show what would change without modifying the file
    --output FILE      Write enriched data to a different file
    --pretty           Pretty-print JSON output

Environment Variables:
    SERPAPI_API_KEY     API key for SerpAPI (https://serpapi.com)
"""

import argparse
import json
import os
import re
import sys


def search_product_data(product_name, source="auto"):
    """Search for a product and return price/image data from available sources."""
    results = {"prices": {}, "image": None}

    if source in ("auto", "serpapi") and os.environ.get("SERPAPI_API_KEY"):
        serpapi_data = _search_serpapi(product_name)
        if serpapi_data:
            return serpapi_data

    if source in ("auto", "amazon"):
        amazon_data = _search_amazon(product_name)
        if amazon_data:
            return amazon_data

    return results


def _search_serpapi(product_name):
    try:
        from serpapi import GoogleSearch
    except ImportError:
        try:
            from serpapi.google_search import GoogleSearch
        except ImportError:
            return None

    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        return None

    try:
        search = GoogleSearch(
            {
                "engine": "google_shopping",
                "q": product_name,
                "api_key": api_key,
                "num": 5,
            }
        )
        data = search.get_dict()
    except Exception as e:
        print(f"  SerpAPI error for '{product_name}': {e}", file=sys.stderr)
        return None

    shopping = data.get("shopping_results", [])
    if not shopping:
        return None

    prices = {}
    image = None

    for item in shopping[:5]:
        store = item.get("source", "Unknown")
        price = item.get("extracted_price")
        if isinstance(price, str):
            match = re.search(r"[\d,]+\.?\d*", price.replace(",", ""))
            price = float(match.group()) if match else None
        link = item.get("link", "")

        if price is not None:
            prices[store] = {"price": price, "url": link}

        if not image and item.get("thumbnail"):
            image = item["thumbnail"]

    return {"prices": prices, "image": image}


def _search_amazon(product_name):
    try:
        from amzpy import AmazonScraper
    except ImportError:
        return None

    try:
        scraper = AmazonScraper()
        results = scraper.get_products(product_name, max_results=3)
    except Exception as e:
        print(f"  Amazon error for '{product_name}': {e}", file=sys.stderr)
        return None

    if not results:
        return None

    prices = {}
    image = None

    for item in results[:3]:
        price = item.get("price")
        if isinstance(price, str):
            match = re.search(r"[\d,]+\.?\d*", price.replace(",", ""))
            price = float(match.group()) if match else None

        if price is not None:
            prices["Amazon"] = {"price": price, "url": item.get("url", "")}

        if not image and item.get("image"):
            image = item["image"]
            break

    return {"prices": prices, "image": image}


def enrich_product(product, dry_run=False):
    """Enrich a single product with live data. Returns (product, changes_list)."""
    name = product.get("name", "Unknown")
    changes = []

    live_data = search_product_data(name)
    if not live_data or (not live_data["prices"] and not live_data["image"]):
        return product, changes

    if live_data["image"] and not product.get("image"):
        if not dry_run:
            product["image"] = live_data["image"]
        changes.append(f"Added image")

    if live_data["prices"]:
        buy_links = product.get("buyLinks", [])
        existing_stores = {link.get("store", "").lower() for link in buy_links}

        for store, price_info in live_data["prices"].items():
            if store.lower() in existing_stores:
                for link in buy_links:
                    if link.get("store", "").lower() == store.lower():
                        old_price = link.get("price")
                        new_price = price_info["price"]
                        if old_price != new_price:
                            if not dry_run:
                                link["price"] = f"${new_price:.2f}"
                            changes.append(
                                f"Updated {store} price: ${old_price} -> ${new_price:.2f}"
                            )
                        break
            else:
                new_link = {
                    "store": store,
                    "url": price_info["url"],
                    "price": f"${price_info['price']:.2f}",
                }
                if not dry_run:
                    buy_links.append(new_link)
                changes.append(f"Added {store} at ${price_info['price']:.2f}")

        if not dry_run:
            product["buyLinks"] = buy_links

    return product, changes


def main():
    parser = argparse.ArgumentParser(
        description="Enrich product data with live prices and images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("data_file", help="Path to data.json")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying"
    )
    parser.add_argument("--output", help="Write to a different file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = parser.parse_args()

    if not os.path.exists(args.data_file):
        print(f"Error: {args.data_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    products = data.get("products", [])
    if not products:
        print("No products found in data file.", file=sys.stderr)
        sys.exit(1)

    print(f"Enriching {len(products)} products...", file=sys.stderr)

    total_changes = 0
    for i, product in enumerate(products):
        name = product.get("name", f"Product {i + 1}")
        print(f"  [{i + 1}/{len(products)}] {name}...", file=sys.stderr)

        product, changes = enrich_product(product, dry_run=args.dry_run)
        if changes:
            for change in changes:
                print(f"    {change}", file=sys.stderr)
            total_changes += len(changes)
        else:
            print(f"    No changes", file=sys.stderr)

    if args.dry_run:
        print(f"\nDry run: {total_changes} changes would be made.", file=sys.stderr)
    else:
        output_path = args.output or args.data_file
        indent = 2 if args.pretty else None
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        print(
            f"\n{total_changes} changes applied. Written to {output_path}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
