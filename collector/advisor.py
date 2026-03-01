"""
Advisor - Recomendaciones de Azure Advisor (Well-Architected por pilar).
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Categorías de Advisor = pilares Well-Architected
ADVISOR_CATEGORIES = [
    "Cost",
    "Security",
    "HighAvailability",  # Reliability
    "OperationalExcellence",
    "Performance",
]


class AdvisorCollector:
    """Recolecta recomendaciones de Azure Advisor."""

    def __init__(self, credential, subscription_ids: List[str]):
        self.credential = credential
        self.subscription_ids = subscription_ids

    def collect_recommendations(self) -> Dict[str, Any]:
        """Listar recomendaciones para cada suscripción."""
        from azure.mgmt.advisor import AdvisorManagementClient

        all_recommendations = []
        errors = []

        for sub_id in self.subscription_ids:
            try:
                client = AdvisorManagementClient(self.credential, sub_id)
                recs = client.recommendations.list()
                for rec in recs:
                    item = {
                        "subscription_id": sub_id,
                        "id": getattr(rec, "id", None),
                        "name": getattr(rec, "name", None),
                        "category": getattr(rec, "category", None),
                        "impact": getattr(rec, "impact", None),
                        "short_description": getattr(rec.short_description, "problem", None) if getattr(rec, "short_description", None) else None,
                        "resource_metadata": getattr(rec, "resource_metadata", None),
                        "remediation": getattr(rec, "remediation", None),
                    }
                    all_recommendations.append(item)
            except Exception as e:
                logger.warning("Error listando recomendaciones para %s: %s", sub_id, e)
                errors.append({"subscription_id": sub_id, "error": str(e)})

        return {
            "success": len(errors) < len(self.subscription_ids),
            "recommendations": all_recommendations,
            "total": len(all_recommendations),
            "errors": errors,
        }
