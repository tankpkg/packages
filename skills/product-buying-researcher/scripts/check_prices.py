#!/usr/bin/env python3
"""Check current prices for a product across multiple retailers.

Usage:
    python3 check_prices.py "Sony WH-1000XM5" [OPTIONS]
    python3 check_prices.py --url "https://amazon.com/dp/B0C8..." [OPTIONS]

Modes:
    Query mode:  Searches for the product and returns prices from all retailers
    URL mode:    Scrapes a specific product page for its current price

Sources (tried in order):
    1. Google Shopping via SerpAPI  (needs SERPAPI_API_KEY) — best multi-retailer
    2. Amazon via amzpy             (free, no key needed) — Amazon-only
    3. Direct URL scraping          (free) — single page, needs price-parser

Options:
    --url URL          Scrape a specific product URL for its price
    --max-results N    Max retailers to check (default: 10)
    --country CODE     Country code (default: us)
    --output FILE      Write JSON to file
    --pretty           Pretty-print JSON

Environment Variables:
    SERPAPI_API_KEY     API key for SerpAPI (https://serpapi.com)
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse


def check_via_serpapi(query, max_results=10, country="us"):
    """Search Google Shopping for multi-retailer price comparison."""
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

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "gl": country,
        "num": max_results,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        print(f"SerpAPI error: {e}", file=sys.stderr)
        return None

    if "error" in results:
        print(f"SerpAPI error: {results['error']}", file=sys.stderr)
        return None

    prices = []
    for item in results.get("shopping_results", [])[:max_results]:
        price = item.get("extracted_price")
        if isinstance(price, str):
            match = re.search(r"[\d,]+\.?\d*", price.replace(",", ""))
            price = float(match.group()) if match else None

        prices.append(
            {
                "store": item.get("source", "Unknown"),
                "price": price,
                "currency": "USD",
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "in_stock": True,
            }
        )

    return prices


def check_via_amazon(query, max_results=10, country="us"):
    """Check Amazon prices via amzpy."""
    try:
        from amzpy import AmazonScraper
    except ImportError:
        return None

    try:
        scraper = AmazonScraper()
        results = scraper.get_products(query, max_results=max_results)
    except Exception as e:
        print(f"Amazon scraper error: {e}", file=sys.stderr)
        return None

    if not results:
        return []

    prices = []
    for item in results[:max_results]:
        price = item.get("price")
        if isinstance(price, str):
            match = re.search(r"[\d,]+\.?\d*", price.replace(",", ""))
            price = float(match.group()) if match else None

        prices.append(
            {
                "store": "Amazon",
                "price": price,
                "currency": item.get("currency", "USD"),
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "in_stock": True,
            }
        )

    return prices


def scrape_url_price(url):
    """Scrape a single product page URL for its price using requests + price-parser."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests not installed. pip install requests", file=sys.stderr)
        return None

    try:
        from price_parser import Price
    except ImportError:
        print(
            "WARNING: price-parser not installed. pip install price-parser\n"
            "Falling back to regex price extraction.",
            file=sys.stderr,
        )
        Price = None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}", file=sys.stderr)
        return None

    html = resp.text
    domain = urlparse(url).netloc

    price_value = None
    currency = "USD"

    if Price:
        # price-parser: find price patterns in raw HTML
        price_patterns = re.findall(r"[\$\£\€][\d,]+\.?\d*", html)
        price_patterns += re.findall(r"[\d,]+\.?\d*\s*(?:USD|EUR|GBP)", html)
        if price_patterns:
            parsed = Price.fromstring(price_patterns[0])
            if parsed.amount is not None:
                price_value = float(parsed.amount)
                currency = parsed.currency or "USD"
    else:
        # Regex fallback: dollar prices
        matches = re.findall(r"\$[\d,]+\.?\d*", html)
        if matches:
            match = re.search(r"[\d,]+\.?\d*", matches[0].replace(",", ""))
            if match:
                price_value = float(match.group())

    # Try to extract title from <title> tag
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    title = title_match.group(1).strip() if title_match else ""
    title = re.sub(r"\s+", " ", title)[:200]

    return {
        "store": domain,
        "price": price_value,
        "currency": currency,
        "url": url,
        "title": title,
        "in_stock": None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Check prices for a product across multiple retailers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", help="Product name to search for")
    parser.add_argument("--url", help="Scrape a specific product page URL")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Max retailers (default: 10)"
    )
    parser.add_argument("--country", default="us", help="Country code (default: us)")
    parser.add_argument("--output", help="Write JSON to file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = parser.parse_args()

    if not args.query and not args.url:
        parser.error("Provide a product name or --url")

    if args.url:
        result = scrape_url_price(args.url)
        prices = [result] if result else []
        source_used = "direct_scrape"
        query = args.url
    else:
        query = args.query
        prices = None
        source_used = None

        if os.environ.get("SERPAPI_API_KEY"):
            prices = check_via_serpapi(query, args.max_results, args.country)
            if prices is not None:
                source_used = "google_shopping"

        if prices is None:
            prices = check_via_amazon(query, args.max_results, args.country)
            if prices is not None:
                source_used = "amazon"

        if prices is None:
            print(
                "No price source available. Options:\n"
                "  1. export SERPAPI_API_KEY=your_key  (pip install google-search-results)\n"
                "  2. pip install amzpy               (free, no key needed)\n"
                "  3. Use --url to scrape a specific product page\n",
                file=sys.stderr,
            )
            sys.exit(1)

    valid_prices = [p for p in prices if p.get("price") is not None]
    valid_prices.sort(key=lambda p: p["price"])

    output = {
        "query": query,
        "source": source_used,
        "count": len(prices),
        "lowest_price": valid_prices[0]["price"] if valid_prices else None,
        "highest_price": valid_prices[-1]["price"] if valid_prices else None,
        "prices": prices,
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
