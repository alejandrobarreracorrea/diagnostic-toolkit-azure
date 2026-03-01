"""
Data Indexer - Indexación de datos recolectados de Azure (Resource Graph + Advisor).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataIndexer:
    """Indexador de datos recolectados de Azure."""

    def __init__(self, raw_dir: Path, index_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def index_all(self) -> Dict[str, Any]:
        """Indexar recursos y recomendaciones de Advisor."""
        index = {
            "subscriptions": [],
            "resource_types": {},
            "resource_count": 0,
            "advisor_by_category": defaultdict(list),
            "advisor_total": 0,
        }

        if not self.raw_dir.exists():
            logger.warning("Directorio raw no existe: %s", self.raw_dir)
            self._save_index(index)
            return index

        # Metadatos
        meta_file = self.raw_dir / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                index["subscriptions"] = meta.get("subscriptions", [])
            except Exception as e:
                logger.warning("Error leyendo metadata: %s", e)

        # Resource Graph - conteos por tipo
        counts_file = self.raw_dir / "resource_graph_counts.json"
        if counts_file.exists():
            try:
                with open(counts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("success") and data.get("data"):
                    for row in data["data"]:
                        # KQL summarize count() by type -> type, count_
                        rtype = row.get("type") or row.get("Type") or ""
                        cnt = row.get("count_") or row.get("Count") or 0
                        if rtype:
                            index["resource_types"][rtype] = index["resource_types"].get(rtype, 0) + int(cnt)
                    index["resource_count"] = sum(index["resource_types"].values())
            except Exception as e:
                logger.warning("Error leyendo resource_graph_counts: %s", e)

        # Si no hay counts, intentar desde resources
        if not index["resource_types"]:
            res_file = self.raw_dir / "resource_graph_resources.json"
            if res_file.exists():
                try:
                    with open(res_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for row in data.get("data", []):
                        rtype = row.get("type") or ""
                        if rtype:
                            index["resource_types"][rtype] = index["resource_types"].get(rtype, 0) + 1
                    index["resource_count"] = len(data.get("data", []))
                except Exception as e:
                    logger.warning("Error leyendo resource_graph_resources: %s", e)

        # Advisor recommendations por categoría
        advisor_file = self.raw_dir / "advisor_recommendations.json"
        if advisor_file.exists():
            try:
                with open(advisor_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for rec in data.get("recommendations", []):
                    cat = rec.get("category") or "Other"
                    index["advisor_by_category"][cat].append(rec)
                    index["advisor_total"] += 1
            except Exception as e:
                logger.warning("Error leyendo advisor_recommendations: %s", e)

        # Convertir defaultdict a dict para JSON
        index["advisor_by_category"] = dict(index["advisor_by_category"])
        self._save_index(index)
        logger.info("Índice generado: %d tipos de recurso, %d recomendaciones", len(index["resource_types"]), index["advisor_total"])
        return index

    def _save_index(self, index: Dict):
        out = self.index_dir / "index.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, default=str)
