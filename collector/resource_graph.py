"""
Resource Graph - Consultas KQL para inventario de recursos Azure.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Consulta base: recursos con tipo, grupo, ubicación
RESOURCES_QUERY = """
resources
| project id, name, type, resourceGroup, location, subscriptionId, tags
| order by type asc, name asc
"""

# Conteo por tipo
RESOURCE_COUNTS_QUERY = """
resources
| summarize count() by type
| order by count_ desc
"""


class ResourceGraphCollector:
    """Recolecta datos de Azure Resource Graph."""

    def __init__(self, credential, subscription_ids: List[str]):
        self.credential = credential
        self.subscription_ids = subscription_ids

    def collect_resources(self, query: str = None) -> Dict[str, Any]:
        """Ejecutar consulta KQL y devolver resultados."""
        from azure.mgmt.resourcegraph import ResourceGraphClient
        from azure.mgmt.resourcegraph.models import QueryRequest

        query = query or RESOURCES_QUERY
        client = ResourceGraphClient(self.credential)
        request = QueryRequest(
            subscriptions=self.subscription_ids,
            query=query,
        )
        try:
            result = client.resources(request)
            return {
                "success": True,
                "data": result.data,
                "total_records": result.total_records,
                "count": result.count,
                "truncated": result.result_truncated == "true",
            }
        except Exception as e:
            logger.exception("Error en Resource Graph: %s", e)
            return {"success": False, "error": str(e), "data": []}

    def collect_counts(self) -> Dict[str, Any]:
        """Recolectar conteos por tipo de recurso."""
        return self.collect_resources(RESOURCE_COUNTS_QUERY)
