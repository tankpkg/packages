#!/usr/bin/env python3
"""Search for products across multiple sources.

Usage:
    python3 search_products.py "wireless earbuds" [OPTIONS]

Sources (tried in order):
    1. Google Shopping via SerpAPI  (needs SERPAPI_API_KEY)
    2. Amazon search via amzpy      (free, no key needed)

Options:
    --max-results N    Maximum products to return (default: 8)
    --min-price N      Minimum price filter (USD)
    --max-price N      Maximum price filter (USD)
    --country CODE     Country code for results, e.g. us, uk, de (default: us)
    --source SOURCE    Force a source: serpapi, amazon, or auto (default: auto)
    --output FILE      Write JSON to file instead of stdout
    --pretty           Pretty-print JSON output

Environment Variables:
    SERPAPI_API_KEY     API key for SerpAPI (https://serpapi.com)
                       Free tier: 100 searches/month

Output: JSON array of product objects with fields:
    name, price, currency, rating, source, store, url, image, description
"""

import argparse
import json
import os
import sys
import re


def search_serpapi(query, max_results=8, min_price=None, max_price=None, country="us"):
    """Search Google Shopping via SerpAPI. Returns structured product data."""
    try:
        from serpapi import GoogleSearch
    except ImportError:
        try:
            from serpapi.google_search import GoogleSearch
        except ImportError:
            print(
                "ERROR: serpapi package not installed.\n"
                "Install with: pip install google-search-results\n"
                "Or use --source amazon for free Amazon search.",
                file=sys.stderr,
            )
            return None

    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        return None

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "gl": country,
        "num": max_results,
    }

    if min_price is not None:
        params["price_low"] = min_price
    if max_price is not None:
        params["price_high"] = max_price

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        print(f"SerpAPI error: {e}", file=sys.stderr)
        return None

    if "error" in results:
        print(f"SerpAPI error: {results['error']}", file=sys.stderr)
        return None

    shopping_results = results.get("shopping_results", [])
    products = []

    for item in shopping_results[:max_results]:
        price_str = item.get("extracted_price") or item.get("price", "")
        price = None
        if isinstance(price_str, (int, float)):
            price = float(price_str)
        elif isinstance(price_str, str):
            # Extract numeric price from string like "$29.99"
            match = re.search(r"[\d,]+\.?\d*", price_str.replace(",", ""))
            if match:
                price = float(match.group())

        product = {
            "name": item.get("title", ""),
            "price": price,
            "currency": "USD",
            "rating": item.get("rating"),
            "reviews_count": item.get("reviews"),
            "source": "google_shopping",
            "store": item.get("source", ""),
            "url": item.get("link", ""),
            "image": item.get("thumbnail", ""),
            "description": item.get("snippet", ""),
        }
        products.append(product)

    return products


def search_amazon(query, max_results=8, min_price=None, max_price=None, country="us"):
    """Search Amazon via amzpy. Free, no API key needed."""
    try:
        from amzpy import AmazonScraper
    except ImportError:
        print(
            "ERROR: amzpy package not installed.\n"
            "Install with: pip install amzpy\n"
            "This is a free Amazon scraper — no API key needed.",
            file=sys.stderr,
        )
        return None

    domain_map = {
        "us": "com",
        "uk": "co.uk",
        "de": "de",
        "fr": "fr",
        "it": "it",
        "es": "es",
        "ca": "ca",
        "jp": "co.jp",
        "au": "com.au",
        "in": "in",
    }
    domain = domain_map.get(country, "com")

    try:
        scraper = AmazonScraper()
        results = scraper.get_products(query, max_results=max_results)
    except Exception as e:
        print(f"Amazon search error: {e}", file=sys.stderr)
        return None

    if not results:
        return []

    products = []
    for item in results[:max_results]:
        price = item.get("price")
        if isinstance(price, str):
            match = re.search(r"[\d,]+\.?\d*", price.replace(",", ""))
            price = float(match.group()) if match else None

        if price is not None:
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue

        currency = item.get("currency", "USD")
        product = {
            "name": item.get("title", ""),
            "price": price,
            "currency": currency,
            "rating": item.get("rating"),
            "reviews_count": item.get("reviews_count"),
            "source": "amazon",
            "store": f"Amazon ({domain})",
            "url": item.get("url", ""),
            "image": item.get("image", ""),
            "description": "",
        }
        products.append(product)

    return products


def main():
    parser = argparse.ArgumentParser(
        description="Search for products across multiple sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Sources (tried in order):\n"
            "  1. Google Shopping via SerpAPI  (needs SERPAPI_API_KEY)\n"
            "  2. Amazon search via amzpy      (free, no key needed)\n"
            "\n"
            "Environment Variables:\n"
            "  SERPAPI_API_KEY  API key for SerpAPI (https://serpapi.com)\n"
        ),
    )
    parser.add_argument("query", help="Product search query")
    parser.add_argument(
        "--max-results", type=int, default=8, help="Max results (default: 8)"
    )
    parser.add_argument("--min-price", type=float, help="Minimum price filter")
    parser.add_argument("--max-price", type=float, help="Maximum price filter")
    parser.add_argument("--country", default="us", help="Country code (default: us)")
    parser.add_argument(
        "--source",
        choices=["auto", "serpapi", "amazon"],
        default="auto",
        help="Force a specific source (default: auto)",
    )
    parser.add_argument("--output", help="Write JSON to file instead of stdout")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = parser.parse_args()
    products = None
    source_used = None

    if args.source in ("auto", "serpapi"):
        if os.environ.get("SERPAPI_API_KEY"):
            products = search_serpapi(
                args.query,
                args.max_results,
                args.min_price,
                args.max_price,
                args.country,
            )
            if products is not None:
                source_used = "google_shopping"

    if products is None and args.source in ("auto", "amazon"):
        products = search_amazon(
            args.query, args.max_results, args.min_price, args.max_price, args.country
        )
        if products is not None:
            source_used = "amazon"

    if products is None:
        print(
            "No search source available. Set up one of:\n"
            "  1. export SERPAPI_API_KEY=your_key  (pip install google-search-results)\n"
            "  2. pip install amzpy               (free, no key needed)\n",
            file=sys.stderr,
        )
        sys.exit(1)

    output = {
        "query": args.query,
        "source": source_used,
        "count": len(products),
        "products": products,
    }

    indent = 2 if args.pretty else None
    json_str = json.dumps(output, indent=indent, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
