#!/usr/bin/env python3
# pyright: ignore
"""
search-components — Offline-first shadcn registry search.

Downloads registry catalogs from shadcn CLI on first run and caches locally.
Refreshes automatically every 24 hours. Searches are instant and offline.

Usage:
    python search-components.py button
    python search-components.py "text animation"
    python search-components.py hero --install registry-name:component-name
    python search-components.py --refresh
    python search-components.py --stats
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_FILE = CACHE_DIR / "all-registries-components.json"
CACHE_MAX_AGE_SECONDS = 86400  # 24 hours
PULL_SCRIPT = Path(__file__).parent / "pull-all-registries.py"


# ── Cache management ─────────────────────────────────────────────────


def _cache_is_fresh() -> bool:
    if not CACHE_FILE.exists():
        return False
    age = time.time() - CACHE_FILE.stat().st_mtime
    return age < CACHE_MAX_AGE_SECONDS


def _load_cache() -> dict:
    with open(CACHE_FILE) as f:
        raw = json.load(f)

    if "sources" in raw:
        return raw

    sources: dict[str, list[dict]] = {}
    for item in raw.get("items", []):
        registry = item.get("registry", "unknown")
        sources.setdefault(registry, []).append(item)

    return {
        "last_updated": raw.get("generatedAt", ""),
        "total_components": raw.get("totalItems", 0),
        "sources": sources,
        "skipped_registries": raw.get("registriesSkipped", []),
    }


def _save_cache(data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def refresh_cache(quiet: bool = False) -> dict:
    if not quiet:
        print("  Downloading registry catalogs...")

    cmd = [sys.executable, str(PULL_SCRIPT), "--output", str(CACHE_FILE)]
    if quiet:
        cmd.append("--quiet")
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        print("  ⚠ pull-all-registries.py failed", file=sys.stderr)

    if CACHE_FILE.exists():
        return _load_cache()

    empty = {
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_components": 0,
        "sources": {},
        "skipped_registries": [],
    }
    _save_cache(empty)
    return empty


def get_cache() -> dict:
    if _cache_is_fresh():
        return _load_cache()
    return refresh_cache()


# ── Search ───────────────────────────────────────────────────────────


def search(
    query: str,
    cache: dict,
    group_filter: str | None = None,
    tag_filter: str | None = None,
) -> list[dict]:
    q = query.lower() if query else ""
    results = []

    for _registry, components in cache.get("sources", {}).items():
        for comp in components:
            if group_filter:
                groups = comp.get("groups", [])
                if group_filter not in groups:
                    continue

            if tag_filter:
                tags = comp.get("tags", [])
                if tag_filter not in tags:
                    continue

            if q:
                name_lower = str(comp.get("name", "")).lower()
                desc_lower = str(comp.get("description", "")).lower()
                type_lower = str(comp.get("type", "")).lower()
                registry_lower = str(comp.get("registry", "")).lower()
                tags_lower = " ".join(comp.get("tags", [])).lower()

                if not (
                    q in name_lower
                    or q in desc_lower
                    or q in type_lower
                    or q in registry_lower
                    or q in tags_lower
                ):
                    continue

            results.append(comp)

    return results


# ── Install ──────────────────────────────────────────────────────────


def _matches_install_spec(component: dict, name: str) -> bool:
    comp_name = str(component.get("name", "")).lower()
    comp_add = str(component.get("addCommandArgument", "")).lower()
    name_lower = name.lower()

    if name_lower == comp_name:
        return True
    if name_lower == comp_add:
        return True
    if comp_add and comp_add.endswith(f"/{name_lower}"):
        return True
    return False


def install_component(spec: str, cache: dict) -> None:
    if ":" not in spec:
        print("Error: format must be 'registry:component-name'", file=sys.stderr)
        print(
            "  Example: @acme/ui:button-primary",
            file=sys.stderr,
        )
        sys.exit(1)

    registry, name = spec.split(":", 1)
    registry = registry.strip()
    name = name.strip()

    for comp in cache.get("sources", {}).get(registry, []):
        if _matches_install_spec(comp, name):
            add_arg = comp.get("addCommandArgument", "")
            if not add_arg:
                print(
                    f"Error: '{comp.get('name', name)}' has no install command.",
                    file=sys.stderr,
                )
                sys.exit(1)

            cmd = ["npx", "shadcn@latest", "add", str(add_arg)]
            print(f"\n  Installing {comp.get('name', name)} from {registry}...")
            print(f"  $ {' '.join(cmd)}\n")
            subprocess.run(cmd, check=False)
            return

    available = ", ".join(sorted(cache.get("sources", {}).keys())) or "none"
    print(f"Error: Unknown registry or component '{registry}:{name}'.", file=sys.stderr)
    print(f"  Registries: {available}", file=sys.stderr)
    sys.exit(1)


# ── Display ──────────────────────────────────────────────────────────


def format_results(results: list[dict], query: str, cache: dict) -> str:
    lines: list[str] = []

    if results:
        lines.append(f"\n{'=' * 72}")
        lines.append(f"  MATCHED COMPONENTS for '{query}'  ({len(results)} found)")
        lines.append(f"{'=' * 72}\n")

        by_registry: dict[str, list[dict]] = {}
        for r in results:
            by_registry.setdefault(r.get("registry", "unknown"), []).append(r)

        for registry, comps in by_registry.items():
            lines.append(f"  ── {registry} ({len(comps)}) ──")
            for c in comps[:25]:
                name = c.get("name", "")
                description = c.get("description", "")
                comp_type = c.get("type", "")
                add_arg = c.get("addCommandArgument", "")

                header = f"    {name}"
                if comp_type:
                    header += f"  [{comp_type}]"
                lines.append(header)

                if description:
                    wrapped = textwrap.fill(
                        description,
                        width=64,
                        initial_indent="      ",
                        subsequent_indent="      ",
                    )
                    lines.append(wrapped)

                groups = c.get("groups", [])
                tags = c.get("tags", [])
                if groups:
                    lines.append(f"      Groups: {', '.join(groups)}")
                if tags:
                    lines.append(f"      Tags: {', '.join(tags[:10])}")

                if add_arg:
                    lines.append(f"      Install: npx shadcn@latest add {add_arg}")
                lines.append("")

            if len(comps) > 25:
                lines.append(
                    f"    ... and {len(comps) - 25} more. Narrow your search.\n"
                )

    registry_count = len(cache.get("sources", {}))
    lines.append(f"{'─' * 72}")
    lines.append(
        f"  Total: {len(results)} cached matches across {registry_count} registries"
    )
    if results:
        lines.append(
            "  Install: python search-components.py --install <registry>:<name>"
        )

    return "\n".join(lines)


def format_stats(cache: dict) -> str:
    lines = [f"\n{'=' * 56}", "  CACHE STATS", f"{'=' * 56}\n"]
    lines.append(f"  Last updated: {cache.get('last_updated', 'never')}")
    lines.append(f"  Total cached: {cache.get('total_components', 0)} components\n")

    for registry, comps in cache.get("sources", {}).items():
        lines.append(f"    {registry:<24} {len(comps):>6} components")

    skipped = cache.get("skipped_registries", [])
    if skipped:
        lines.append("\n  Skipped registries:")
        for entry in skipped[:10]:
            lines.append(
                f"    {entry.get('name', 'unknown')} ({entry.get('reason', '')})"
            )
        if len(skipped) > 10:
            lines.append(f"    ... and {len(skipped) - 10} more")

    lines.append(f"\n  Cache file: {CACHE_FILE}")
    lines.append(f"  Max age:    {CACHE_MAX_AGE_SECONDS // 3600}h")
    return "\n".join(lines)


# ── Group & Tag listing ──────────────────────────────────────────────


def _collect_groups(cache: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _registry, components in cache.get("sources", {}).items():
        for comp in components:
            for g in comp.get("groups", ["other"]):
                counts[g] = counts.get(g, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _collect_tags(cache: dict, top_n: int = 50) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _registry, components in cache.get("sources", {}).items():
        for comp in components:
            for t in comp.get("tags", []):
                counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1])[:top_n])


def _format_groups(cache: dict) -> str:
    groups = _collect_groups(cache)
    lines = [f"\n{'=' * 56}", "  GROUPS", f"{'=' * 56}\n"]
    for g, count in groups.items():
        lines.append(f"    {g:<24} {count:>5} components")
    lines.append(f"\n  Use: python search-components.py --group <group-name>")
    return "\n".join(lines)


def _format_tags(cache: dict) -> str:
    tags = _collect_tags(cache, top_n=80)
    lines = [f"\n{'=' * 56}", "  TOP TAGS", f"{'=' * 56}\n"]
    for t, count in tags.items():
        lines.append(f"    {t:<24} {count:>5}")
    unique = len(
        {
            t
            for comps in cache.get("sources", {}).values()
            for comp in comps
            for t in comp.get("tags", [])
        }
    )
    lines.append(f"\n  Total unique tags: {unique}")
    lines.append(f"  Use: python search-components.py --tag <tag-name>")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline-first shadcn registry search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Sources:
              - registries.json from ui.shadcn.com
              - shadcn CLI search for each registry (paged)

            Examples:
              %(prog)s button
              %(prog)s "text animation" --json
              %(prog)s hero --install @acme/ui:hero-parallax
              %(prog)s --group animation
              %(prog)s button --group forms
              %(prog)s --tag glassmorphism
              %(prog)s --groups
              %(prog)s --tags
              %(prog)s --refresh
              %(prog)s --stats
        """
        ),
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search keyword (matches name, description, type, registry, tags)",
    )
    parser.add_argument(
        "--install",
        "-i",
        metavar="REGISTRY:NAME",
        help="Install component (e.g., @acme/ui:hero-parallax)",
    )
    parser.add_argument(
        "--refresh", "-r", action="store_true", help="Force re-download all catalogs"
    )
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--sources", action="store_true", help="List all registries")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--group",
        "-g",
        metavar="GROUP",
        help="Filter by group (e.g., animation, buttons, cards, marketing-blocks)",
    )
    parser.add_argument(
        "--tag",
        "-t",
        metavar="TAG",
        help="Filter by tag (e.g., hover, glassmorphism, 3d, parallax)",
    )
    parser.add_argument(
        "--groups", action="store_true", help="List all available groups"
    )
    parser.add_argument("--tags", action="store_true", help="List all available tags")

    args = parser.parse_args()

    if args.sources:
        cache = get_cache()
        lines = ["\n  Registries (offline search + install):"]
        for registry in sorted(cache.get("sources", {}).keys()):
            lines.append(f"    {registry}")

        skipped = cache.get("skipped_registries", [])
        if skipped:
            lines.append("\n  Skipped registries:")
            for entry in skipped[:10]:
                lines.append(f"    {entry.get('name', 'unknown')}")
            if len(skipped) > 10:
                lines.append(f"    ... and {len(skipped) - 10} more")

        print("\n".join(lines))
        return

    if args.refresh:
        refresh_cache()
        return

    cache = get_cache()

    if args.groups:
        print(_format_groups(cache))
        return

    if args.tags:
        print(_format_tags(cache))
        return

    if args.stats:
        print(format_stats(cache))
        return

    if args.install:
        install_component(args.install, cache)
        return

    if not args.query and not args.group and not args.tag:
        parser.print_help()
        sys.exit(1)

    results = search(
        args.query or "", cache, group_filter=args.group, tag_filter=args.tag
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, args.query, cache))


if __name__ == "__main__":
    main()
