# pyright: ignore

import time


def build_fixture_cache_data():
    acme_ui = [
        {
            "name": "stateful-button",
            "type": "ui-component",
            "description": "Accessible button variants",
            "registry": "@acme/ui",
            "addCommandArgument": "@acme/ui/stateful-button",
        }
    ]

    motion_lab = [
        {
            "name": "split-text",
            "type": "animation",
            "description": "Kinetic text animation",
            "registry": "@motion-lab",
            "addCommandArgument": "@motion-lab/split-text",
        },
        {
            "name": "aurora-background",
            "type": "animation",
            "description": "Gradient background lights",
            "registry": "@motion-lab",
            "addCommandArgument": "@motion-lab/aurora-background",
        },
    ]

    forms_kit = [
        {
            "name": "smart-form",
            "type": "forms",
            "description": "Multi-step form builder",
            "registry": "@forms-kit",
            "addCommandArgument": "@forms-kit/smart-form",
        }
    ]

    iconverse = [
        {
            "name": "sparkle-icons",
            "type": "icons",
            "description": "SVG icon set",
            "registry": "@iconverse",
            "addCommandArgument": "@iconverse/sparkle-icons",
        }
    ]

    dashboard_pro = []
    for i in range(1, 31):
        name = f"admin-card-{i:02d}"
        dashboard_pro.append(
            {
                "name": name,
                "type": "dashboard",
                "description": "Admin card layout",
                "registry": "@dashboard-pro",
                "addCommandArgument": f"@dashboard-pro/{name}",
            }
        )

    sources = {
        "@acme/ui": acme_ui,
        "@motion-lab": motion_lab,
        "@forms-kit": forms_kit,
        "@iconverse": iconverse,
        "@dashboard-pro": dashboard_pro,
    }

    total = sum(len(items) for items in sources.values())

    return {
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_components": total,
        "sources": sources,
        "registries_source_url": "https://ui.shadcn.com/r/registries.json",
        "skipped_registries": [
            {"name": "@ai-chat/ui", "reason": "skip_keyword"},
            {"name": "@payments-kit", "reason": "skip_keyword"},
            {"name": "@broken-registry", "reason": "search_failed"},
        ],
    }
