"""
Inventory - Inventario de recursos Azure a partir del índice.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InventoryGenerator:
    """Generador de inventario de recursos Azure."""

    def __init__(self, index_dir: Path, output_dir: Path):
        self.index_dir = Path(index_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> Dict[str, Any]:
        """Generar inventario desde index.json."""
        index_file = self.index_dir / "index.json"
        if not index_file.exists():
            logger.error("Índice no encontrado: %s", index_file)
            return {}

        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)

        resource_types = index.get("resource_types", {})
        total = index.get("resource_count", 0)
        # Ordenar por count descendente
        top_types = sorted(
            [{"type": k, "count": v} for k, v in resource_types.items()],
            key=lambda x: -x["count"],
        )[:50]

        inventory = {
            "total_resources": total,
            "resource_types_count": len(resource_types),
            "top_resource_types": top_types,
            "subscriptions": index.get("subscriptions", []),
        }

        out_file = self.output_dir / "inventory.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(inventory, f, indent=2)
        logger.info("Inventario guardado en: %s", out_file)
        return inventory
