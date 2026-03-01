#!/usr/bin/env python3
"""
Azure Diagnostic Collector - Recolección de datos desde Azure.

Usa Resource Graph para inventario de recursos y Azure Advisor para
recomendaciones alineadas al Well-Architected Framework.
"""

import argparse
import json
import gzip
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import logging

from .metadata import MetadataCollector
from .resource_graph import ResourceGraphCollector
from .advisor import AdvisorCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_credential(tenant_id: Optional[str] = None):
    """Obtener credencial Azure (DefaultAzureCredential). Si se indica tenant, se usa ese tenant."""
    from azure.identity import DefaultAzureCredential
    tid = tenant_id or os.getenv("AZURE_TENANT_ID")
    if tid:
        return DefaultAzureCredential(tenant_id=tid)
    return DefaultAzureCredential()


def _project_root() -> Path:
    """Raíz del proyecto (donde está ecad_azure.py / collector/)."""
    return Path(__file__).resolve().parent.parent


def _subscription_ids_from_config() -> Optional[List[str]]:
    """Cargar subscription IDs desde subscriptions.yaml o config.yaml en la raíz del proyecto."""
    root = _project_root()
    for name in ("subscriptions.yaml", "subscriptions.yml", "config.yaml", "config.yml"):
        path = root / name
        if not path.exists():
            continue
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # subscription_ids: [ "id1", "id2" ]
            ids = data.get("subscription_ids")
            if ids and isinstance(ids, list):
                out = [str(s).strip() for s in ids if s]
                if out:
                    logger.info("Suscripciones cargadas desde %s: %d", path.name, len(out))
                    return out
            # subscriptions: [ { id: "id1", name: "..." }, ... ]
            subs = data.get("subscriptions")
            if subs and isinstance(subs, list):
                out = []
                for s in subs:
                    if isinstance(s, dict) and s.get("id"):
                        out.append(str(s["id"]).strip())
                    elif isinstance(s, str):
                        out.append(s.strip())
                if out:
                    logger.info("Suscripciones cargadas desde %s: %d", path.name, len(out))
                    return out
        except Exception as e:
            logger.warning("Error leyendo %s: %s", path, e)
    return None


def get_subscription_ids(
    subscriptions: Optional[List[str]] = None,
    use_config_file: bool = False,
) -> List[str]:
    """
    Obtener lista de subscription IDs.
    Orden: argumentos > env > (opcional) archivo config > listar todas del tenant.
    Por defecto, si no pasas nada ni env, se listan automáticamente todas las
    suscripciones a las que tiene acceso la credencial en el tenant actual.
    """
    if subscriptions:
        return subscriptions
    env = os.getenv("AZURE_SUBSCRIPTION_IDS") or os.getenv("AZURE_SUBSCRIPTION_ID")
    if env:
        return [s.strip() for s in env.split(",")]
    if use_config_file or os.getenv("ECAD_AZURE_USE_SUBSCRIPTIONS_FILE", "").lower() in ("1", "true", "yes"):
        from_config = _subscription_ids_from_config()
        if from_config:
            return from_config
    # Por defecto: listar todas las suscripciones del tenant (az login / credencial actual)
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.subscription import SubscriptionClient
        tid = os.getenv("AZURE_TENANT_ID")
        cred = DefaultAzureCredential(tenant_id=tid) if tid else DefaultAzureCredential()
        client = SubscriptionClient(cred)
        subs = list(client.subscriptions.list())
        if not subs:
            logger.warning("No se encontraron suscripciones en el tenant. Comprueba az login o AZURE_TENANT_ID.")
            return []
        ids = [s.subscription_id for s in subs]
        logger.info("Suscripciones listadas automáticamente en el tenant: %d", len(ids))
        return ids
    except Exception as e:
        logger.warning("No se pudieron listar suscripciones: %s", e)
        return []


class Collector:
    """Coordinador principal de recolección de datos Azure."""

    def __init__(
        self,
        output_dir: str,
        subscription_ids: Optional[List[str]] = None,
    ):
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.subscription_ids = subscription_ids or get_subscription_ids()
        self.credential = get_credential()
        self.stats = {
            "subscriptions": len(self.subscription_ids),
            "resources_collected": 0,
            "recommendations_collected": 0,
            "errors": [],
        }

    def collect(self):
        """Ejecutar recolección completa."""
        logger.info("Iniciando recolección Azure")
        logger.info("Suscripciones: %s", self.subscription_ids)

        # Metadatos
        meta_collector = MetadataCollector(self.credential, self.subscription_ids)
        metadata = meta_collector.collect()
        self._save_json("metadata.json", metadata)

        # Resource Graph - recursos
        rg = ResourceGraphCollector(self.credential, self.subscription_ids)
        resources_result = rg.collect_resources()
        if resources_result.get("success"):
            self.stats["resources_collected"] = resources_result.get("total_records") or len(resources_result.get("data", []))
        self._save_json("resource_graph_resources.json", resources_result)

        # Resource Graph - conteos por tipo
        counts_result = rg.collect_counts()
        self._save_json("resource_graph_counts.json", counts_result)

        # Advisor - recomendaciones
        advisor = AdvisorCollector(self.credential, self.subscription_ids)
        advisor_result = advisor.collect_recommendations()
        if advisor_result.get("success") is not False:
            self.stats["recommendations_collected"] = advisor_result.get("total", 0)
        self._save_json("advisor_recommendations.json", advisor_result)

        logger.info(
            "Recolección completada: %d recursos, %d recomendaciones",
            self.stats["resources_collected"],
            self.stats["recommendations_collected"],
        )
        return self.stats

    def _save_json(self, filename: str, data: Dict):
        path = self.raw_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description="Azure Diagnostic Collector")
    parser.add_argument("--output-dir", required=True, help="Directorio de salida")
    parser.add_argument("--subscriptions", help="IDs de suscripción separados por coma")
    args = parser.parse_args()
    subscriptions = None
    if args.subscriptions:
        subscriptions = [s.strip() for s in args.subscriptions.split(",")]
    collector = Collector(output_dir=args.output_dir, subscription_ids=subscriptions)
    collector.collect()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
