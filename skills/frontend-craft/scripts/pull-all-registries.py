#!/usr/bin/env python3
"""
pull-all-registries — Download all shadcn registry components into one JSON file.

Uses concurrent workers to pull registries in parallel.

Usage:
    python pull-all-registries.py
    python pull-all-registries.py --registry-limit 5 --workers 16
    python pull-all-registries.py --proxy http://user:pass@host:port
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REGISTRIES_URL = "https://ui.shadcn.com/r/registries.json"
DEFAULT_OUTPUT = Path(__file__).parent / ".cache" / "all-registries-components.json"

SKIP_KEYWORDS = {
    "ai ",
    "chat",
    "chatbot",
    "chatgpt",
    "gpt",
    "llm",
    "assistant",
    "livekit",
    "mcp",
    "agent",
    "auth",
    "login",
    "oauth",
    "sso",
    "identity",
    "clerk",
    "payment",
    "payments",
    "stripe",
    "billing",
    "checkout",
    "invoice",
    "paykit",
    "crypto",
    "nft",
    "blockchain",
    "web3",
    "abstract",
    "home assistant",
    "sound effect",
    "slide deck",
    "notebook",
    "status page",
    "social media",
    "media player",
    "onboard",
    "token",
    "nuqs",
    "paste",
    "inertia",
    "cms",
    "casino",
    "betting",
    "gambling",
    "medical",
    "healthcare",
    "legal",
    "real estate",
    "mortgage",
    "travel",
}

# Explicit registry names to skip — low quality, dead, or junk per research.
SKIP_REGISTRIES = {
    "@abui",
    "@aevr",
    "@aliimam",
    "@animbits",
    "@arc",
    "@baselayer",
    "@better-upload",
    "@cardcn",
    "@chamaac",
    "@darx",
    "@einui",
    "@fab-ui",
    "@glass-ui",
    "@gooseui",
    "@hextaui",
    "@hooks",
    "@kanpeki",
    "@lumiui",
    "@lytenyte",
    "@moleculeui",
    "@mui-treasury",
    "@optics",
    "@phucbm",
    "@prosekit",
    "@pureui",
    "@react-aria",
    "@roiui",
    "@satoriui",
    "@scrollxui",
    "@shadcn-map",
    "@shadcn-space",
    "@shadcndesign",
    "@shadcraft",
    "@shadcnui-blocks",
    "@shadcnuikit",
    "@skiper-ui",
    "@solaceui",
    "@sona-ui",
    "@spectrumui",
    "@supabase",
    "@systaliko-ui",
    "@tailwind-admin",
    "@thegridcn",
    "@typedora-ui",
    "@uicapsule",
    "@wds",
}


def _fetch_json(url: str, proxy_url: str | None = None, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": "tank-skill/1.0"})
    try:
        if proxy_url:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            )
            resp = opener.open(req, timeout=timeout)
        else:
            resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        print(f"  ⚠ fetch {url}: {e}", file=sys.stderr)
        return None


def _should_skip(registry: dict) -> tuple[bool, str]:
    name = registry.get("name", "").strip()
    if name in SKIP_REGISTRIES:
        return True, f"registry:{name}"
    combined = (name + " " + registry.get("description", "")).lower()
    for kw in SKIP_KEYWORDS:
        if kw in combined:
            return True, f"keyword:{kw.strip()}"
    return False, ""


def _pull_one_registry(
    name: str, page_limit: int, proxy_env: dict
) -> tuple[str, list[dict] | None]:
    """Pull all pages for a single registry. Returns (name, items_or_None)."""
    offset = 0
    items: list[dict] = []

    while True:
        cmd = [
            "npx",
            "shadcn@latest",
            "search",
            name,
            "-l",
            str(page_limit),
            "-o",
            str(offset),
        ]
        env = {**os.environ, **proxy_env}
        try:
            proc = subprocess.run(
                cmd, text=True, capture_output=True, check=False, env=env, timeout=90
            )
        except subprocess.TimeoutExpired:
            return name, None

        if proc.returncode != 0 or not proc.stdout.strip():
            return (name, None) if not items else (name, items)

        try:
            data = json.loads(proc.stdout.strip())
        except json.JSONDecodeError:
            return (name, None) if not items else (name, items)

        if not isinstance(data, dict):
            return (name, None) if not items else (name, items)

        page_items = data.get("items", [])
        if not isinstance(page_items, list):
            break

        for item in page_items:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            item_name = item.get("name", "").lower()
            if (
                "example" in item_name
                or "demo" in item_name
                or any(
                    item_name.endswith(s) or item_name.startswith(s)
                    for s in ("-docs", "-test", "-spec", "docs-")
                )
                or item_name in ("docs", "index", "utils", "style", "ui")
            ):
                continue
            items.append(
                {
                    "registry": item.get("registry", name),
                    "name": item.get("name", ""),
                    "type": item.get("type", ""),
                    "description": item.get("description", ""),
                    "addCommandArgument": item.get("addCommandArgument", ""),
                }
            )

        pagination = data.get("pagination", {})
        if not pagination.get("hasMore", data.get("hasMore", False)) or not page_items:
            break
        offset += page_limit

    return name, items


GROUP_KEYWORDS: dict[str, list[str]] = {
    "icons": [
        "icon",
        "icons",
        "lucide",
        "heroicon",
        "heroicons",
        "arrow",
        "arrows",
        "folder",
        "folders",
    ],
    "maps": ["map", "maps", "globe", "world-map", "mapbox", "leaflet"],
    "rich-text-editors": [
        "editor",
        "editors",
        "rich-text",
        "wysiwyg",
        "plate",
        "tiptap",
        "prosemirror",
        "plugin",
    ],
    "charts": [
        "chart",
        "charts",
        "graph",
        "sparkline",
        "histogram",
        "gantt",
        "contribution-graph",
        "recharts",
        "heatmap",
    ],
    "tables": ["table", "tables", "datagrid", "data-grid", "data-table"],
    "forms": [
        "form",
        "forms",
        "input",
        "textarea",
        "select",
        "checkbox",
        "radio",
        "combobox",
        "datepicker",
        "date-picker",
        "switch",
        "toggle",
        "slider",
        "upload",
        "file-upload",
        "field",
        "picker",
        "color-picker",
        "color-area",
        "color-swatch",
        "color-wheel",
    ],
    "buttons": ["button", "buttons"],
    "cards": ["card", "cards", "bento"],
    "dialogs": [
        "dialog",
        "dialogs",
        "modal",
        "modals",
        "sheet",
        "drawer",
        "alert-dialog",
        "popover",
    ],
    "navigation": [
        "nav",
        "navbar",
        "sidebar",
        "menu",
        "menubar",
        "breadcrumb",
        "tabs",
        "dock",
        "pagination",
        "stepper",
        "command",
        "toolbar",
    ],
    "marketing-blocks": [
        "hero",
        "pricing",
        "testimonial",
        "testimonials",
        "cta",
        "call-to-action",
        "footer",
        "landing",
        "feature-section",
        "stats",
        "logo-cloud",
        "faq",
        "logo",
        "contact",
        "comparator",
        "about",
    ],
    "animation": [
        "animated",
        "animation",
        "motion",
        "transition",
        "parallax",
        "marquee",
        "stagger",
        "magnet",
        "confetti",
        "typewriter",
        "aurora",
        "spotlight",
        "beam",
        "effect",
        "hover-effect",
        "reveal",
        "liquid",
        "morph",
    ],
    "backgrounds": [
        "background",
        "backgrounds",
        "gradient",
        "particles",
        "noise",
        "mesh",
        "aurora-background",
        "beams",
        "shader",
        "chrome",
    ],
    "carousel": ["carousel", "carousels", "slideshow", "swiper"],
    "layout": [
        "layout",
        "layouts",
        "grid",
        "container",
        "section",
        "divider",
        "spacer",
        "separator",
        "resizable",
        "collapsible",
        "accordion",
        "aspect-ratio",
        "scroll-area",
        "scroll",
        "empty",
        "aspect",
    ],
    "feedback": [
        "toast",
        "notification",
        "alert",
        "progress",
        "skeleton",
        "spinner",
        "loader",
        "loading",
        "badge",
        "sonner",
        "status",
        "banner",
    ],
    "avatar": ["avatar", "avatars"],
    "text": [
        "text",
        "heading",
        "typography",
        "label",
        "title",
        "blockquote",
        "kbd",
        "code-block",
        "code",
    ],
    "media": ["image", "video", "audio", "media", "gallery", "lightbox", "zoom"],
    "calendar": ["calendar", "date", "time", "schedule", "timeline"],
    "tooltip": ["tooltip", "tooltips"],
    "cursor": ["cursor"],
    "theme": ["theme", "themes", "color-theme", "palette"],
    "auth-pages": [
        "login",
        "sign-in",
        "signup",
        "register",
        "forgot-password",
        "verify",
        "otp",
    ],
    "list": ["list", "sortable-list"],
    "retro-pixel": [
        "pixel",
        "retro",
        "8bit",
        "8-bit",
        "nes",
        "arcade",
        "bitcn",
        "retroui",
        "pixelact",
    ],
}


def _classify(item: dict) -> list[str]:
    name = item.get("name", "").lower().replace("-", " ").replace("_", " ")
    desc = item.get("description", "").lower().replace("-", " ").replace("_", " ")
    words = set((name + " " + desc).split())
    matched = [g for g, kws in GROUP_KEYWORDS.items() if any(kw in words for kw in kws)]
    return matched or ["other"]


def _build_group_index(items: list[dict]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for item in items:
        for g in item.get("groups", ["other"]):
            index.setdefault(g, []).append(item["addCommandArgument"])
    return {g: sorted(set(cmds)) for g, cmds in index.items()}


TAG_TAXONOMY: dict[str, list[str]] = {
    "hover": ["hover", "interactive", "mouse"],
    "click": ["click", "interactive"],
    "drag": ["drag", "draggable", "dnd"],
    "sortable": ["sortable", "drag", "reorder"],
    "scroll": ["scroll", "scroll-driven"],
    "sticky": ["sticky", "scroll-driven"],
    "magnetic": ["magnetic", "cursor-effect"],
    "cursor": ["cursor-effect", "mouse"],
    "expandable": ["expandable", "collapsible"],
    "collapsible": ["collapsible", "expandable"],
    "animated": ["animated", "motion", "transition"],
    "animation": ["animated", "motion"],
    "motion": ["animated", "motion"],
    "gradient": ["gradient", "color-effect"],
    "glow": ["glow", "neon", "light-effect"],
    "glowing": ["glow", "neon", "light-effect"],
    "neon": ["neon", "glow", "light-effect"],
    "shimmer": ["shimmer", "light-effect"],
    "shine": ["shine", "light-effect"],
    "sparkles": ["sparkle", "particle"],
    "blur": ["blur", "glassmorphism"],
    "glass": ["glassmorphism", "blur"],
    "3d": ["3d", "perspective", "depth"],
    "perspective": ["perspective", "3d"],
    "tilt": ["tilt", "3d", "mouse"],
    "parallax": ["parallax", "scroll-driven"],
    "ripple": ["ripple", "click-effect"],
    "confetti": ["confetti", "particle"],
    "particles": ["particle", "background-effect"],
    "beam": ["beam", "light-effect"],
    "meteors": ["meteor", "particle"],
    "orbit": ["orbit", "circular"],
    "pulse": ["pulse", "attention"],
    "wave": ["wave", "organic"],
    "morph": ["morph", "shape-shift"],
    "flip": ["flip", "transition"],
    "rotate": ["rotate", "spin"],
    "reveal": ["reveal", "entrance"],
    "fade": ["fade", "entrance"],
    "slide": ["slide", "entrance"],
    "marquee": ["marquee", "infinite", "ticker"],
    "typewriter": ["typewriter", "text-effect"],
    "typing": ["typing", "text-effect"],
    "aurora": ["aurora", "ambient"],
    "spotlight": ["spotlight", "light-effect"],
    "noise": ["noise", "texture"],
    "liquid": ["liquid", "fluid"],
    "pixel": ["pixel", "retro", "8bit"],
    "retro": ["retro", "vintage"],
    "button": ["button", "cta", "clickable"],
    "input": ["input", "form-control"],
    "textarea": ["textarea", "form-control"],
    "select": ["select", "dropdown", "form-control"],
    "checkbox": ["checkbox", "form-control"],
    "radio": ["radio", "form-control"],
    "switch": ["switch", "toggle", "form-control"],
    "slider": ["slider", "range", "form-control"],
    "form": ["form", "form-control"],
    "upload": ["upload", "file", "form-control"],
    "combobox": ["combobox", "autocomplete"],
    "card": ["card", "container", "content-block"],
    "dialog": ["dialog", "modal", "overlay"],
    "modal": ["modal", "dialog", "overlay"],
    "sheet": ["sheet", "drawer", "slide-over"],
    "drawer": ["drawer", "sheet", "slide-over"],
    "popover": ["popover", "floating", "overlay"],
    "tooltip": ["tooltip", "hover-info"],
    "toast": ["toast", "notification", "feedback"],
    "alert": ["alert", "feedback", "status"],
    "badge": ["badge", "label", "status-indicator"],
    "avatar": ["avatar", "user", "profile-image"],
    "skeleton": ["skeleton", "loading", "placeholder"],
    "spinner": ["spinner", "loading"],
    "progress": ["progress", "loading"],
    "table": ["table", "data-display", "tabular"],
    "chart": ["chart", "data-visualization"],
    "calendar": ["calendar", "date", "scheduling"],
    "timeline": ["timeline", "chronological"],
    "accordion": ["accordion", "collapsible"],
    "tabs": ["tabs", "navigation", "segmented"],
    "carousel": ["carousel", "slider", "gallery"],
    "gallery": ["gallery", "images", "grid"],
    "navbar": ["navbar", "navigation", "header"],
    "sidebar": ["sidebar", "navigation"],
    "menu": ["menu", "navigation", "dropdown"],
    "breadcrumb": ["breadcrumb", "navigation"],
    "dock": ["dock", "navigation", "macos-style"],
    "command": ["command-palette", "search"],
    "icon": ["icon", "graphic", "symbol"],
    "image": ["image", "media"],
    "video": ["video", "media"],
    "map": ["map", "geography", "location"],
    "globe": ["globe", "3d", "map"],
    "editor": ["editor", "rich-text", "wysiwyg"],
    "hero": ["hero", "landing-page", "above-fold"],
    "pricing": ["pricing", "landing-page", "saas"],
    "testimonial": ["testimonial", "social-proof"],
    "cta": ["cta", "conversion", "landing-page"],
    "footer": ["footer", "layout"],
    "feature": ["feature", "landing-page", "showcase"],
    "stats": ["stats", "metrics", "dashboard"],
    "faq": ["faq", "support"],
    "login": ["login", "auth"],
    "product": ["product", "e-commerce"],
    "cart": ["cart", "e-commerce", "shopping"],
    "checkout": ["checkout", "e-commerce"],
    "grid": ["grid", "layout", "responsive"],
    "bento": ["bento-grid", "grid", "layout"],
    "masonry": ["masonry", "grid", "layout"],
    "theme": ["theme", "customization"],
}

_TAG_STOP = frozenset(
    "a an the and or of in on at to for is it with by as from that this be are "
    "was has not but all can had her one our out its you do no so up if".split()
)

_VALUABLE_DESC = frozenset(
    "accessible responsive dark light minimal modern clean premium interactive "
    "customizable configurable headless animated smooth elegant creative playful "
    "professional mobile desktop fullscreen inline floating fixed sticky draggable "
    "sortable resizable collapsible expandable searchable filterable editable".split()
)


def _generate_tags(item: dict) -> list[str]:
    name = item.get("name", "")
    desc = item.get("description", "")
    registry = item.get("registry", "")
    groups = item.get("groups", [])

    tags: set[str] = set()

    tags.update(g for g in groups if g != "other")
    tags.add(registry.lstrip("@").replace("/", "-"))

    text = (name + " " + desc).lower().replace("-", " ").replace("_", " ")
    words = set(text.split())
    for kw, kw_tags in TAG_TAXONOMY.items():
        if kw in words:
            tags.update(kw_tags)

    for part in name.lower().replace("-", " ").replace("_", " ").split():
        if len(part) > 2 and part not in _TAG_STOP and not part.isdigit():
            tags.add(part)

    for w in desc.lower().replace("-", " ").replace(",", "").replace(".", "").split():
        if w in _VALUABLE_DESC:
            tags.add(w)

    if len(tags) < 5:
        desc_words = [
            w for w in desc.lower().split() if len(w) > 3 and w not in _TAG_STOP
        ]
        for w in desc_words:
            tags.add(w)
            if len(tags) >= 5:
                break

    tags.discard("other")
    return sorted(tags) or [registry.lstrip("@"), "component"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull all shadcn registry components into one JSON file (parallel).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s                              # pull everything
              %(prog)s --registry-limit 5           # first 5 registries only
              %(prog)s --workers 24                 # 24 parallel workers
              %(prog)s --proxy http://u:p@host:port # use HTTP proxy
        """),
    )
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--page-limit", type=int, default=100)
    parser.add_argument("--registry-limit", type=int, default=-1, help="-1=all")
    parser.add_argument("--workers", "-w", type=int, default=16)
    parser.add_argument("--include-skipped", action="store_true")
    parser.add_argument(
        "--proxy", default=None, help="HTTP proxy URL (http://user:pass@host:port)"
    )
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()
    proxy_url = args.proxy or os.environ.get("HTTP_PROXY")
    proxy_env = {"HTTP_PROXY": proxy_url, "HTTPS_PROXY": proxy_url} if proxy_url else {}

    if not args.quiet:
        print("  Fetching registries.json...", flush=True)

    registries = _fetch_json(REGISTRIES_URL, proxy_url=proxy_url)
    if not isinstance(registries, list):
        print("Error: could not fetch registries.json", file=sys.stderr)
        sys.exit(1)

    to_pull: list[str] = []
    skipped: list[dict] = []
    for reg in registries:
        if not isinstance(reg, dict):
            continue
        name = reg.get("name", "").strip()
        if not name:
            continue
        if not args.include_skipped:
            skip, reason = _should_skip(reg)
            if skip:
                skipped.append({"name": name, "reason": reason})
                continue
        to_pull.append(name)

    if args.registry_limit >= 0:
        to_pull = to_pull[: args.registry_limit]

    if not args.quiet:
        print(
            f"  Pulling {len(to_pull)} registries with {args.workers} workers (skipped {len(skipped)})...",
            flush=True,
        )

    all_items: list[dict] = []
    failed: list[str] = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(_pull_one_registry, name, args.page_limit, proxy_env): name
            for name in to_pull
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                _, items = future.result()
            except Exception as e:
                failed.append(name)
                if not args.quiet:
                    print(f"    ✗ {name}: {e}", flush=True)
                continue

            if items is None:
                failed.append(name)
                skipped.append({"name": name, "reason": "search_failed"})
                if not args.quiet:
                    print(f"    ✗ {name} FAILED", flush=True)
            else:
                all_items.extend(items)
                if not args.quiet:
                    print(f"    ✓ {name}: {len(items)}", flush=True)

    for item in all_items:
        item["groups"] = _classify(item)
        item["tags"] = _generate_tags(item)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    groups = _build_group_index(all_items)

    result = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": REGISTRIES_URL,
        "totalRegistriesSeen": len(registries),
        "registriesRetained": len(to_pull) - len(failed),
        "registriesSkipped": skipped,
        "totalItems": len(all_items),
        "groupCounts": {
            g: len(v) for g, v in sorted(groups.items(), key=lambda x: -len(x[1]))
        },
        "groups": groups,
        "items": all_items,
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    if not args.quiet:
        print(
            f"\n  ✓ {len(all_items)} items from {len(to_pull) - len(failed)} registries → {output_path}"
        )
        print(f"    Skipped: {len(skipped)} | Failed: {len(failed)}")


if __name__ == "__main__":
    main()
