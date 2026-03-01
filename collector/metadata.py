"""
Metadata Collector - Recolección de metadatos de suscripción Azure.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class MetadataCollector:
    """Recolector de metadatos de suscripción(es) Azure."""

    def __init__(self, credential, subscription_ids: List[str]):
        self.credential = credential
        self.subscription_ids = subscription_ids

    def collect(self) -> Dict[str, Any]:
        """Recolectar metadatos de la suscripción Azure."""
        metadata = {
            "subscription_ids": self.subscription_ids,
            "subscriptions": [],
            "tenant_id": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            from azure.mgmt.subscription import SubscriptionClient
            client = SubscriptionClient(self.credential)
            for sub_id in self.subscription_ids:
                try:
                    sub = client.subscriptions.get(sub_id)
                    metadata["subscriptions"].append({
                        "id": sub.subscription_id,
                        "display_name": getattr(sub, "display_name", sub.subscription_id),
                        "state": getattr(sub, "state", None),
                    })
                    if getattr(sub, "tenant_id", None):
                        metadata["tenant_id"] = sub.tenant_id
                except Exception as e:
                    logger.warning(f"No se pudo obtener detalle de suscripción {sub_id}: {e}")
                    metadata["subscriptions"].append({"id": sub_id, "display_name": sub_id, "state": None})
        except Exception as e:
            logger.warning(f"Error recolectando metadatos de suscripción: {e}")

        return metadata
