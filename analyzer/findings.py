"""
Findings - Hallazgos a partir de recomendaciones de Azure Advisor.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_findings_from_advisor(index: Dict) -> List[Dict]:
    """Convertir recomendaciones de Advisor en hallazgos para reportes."""
    findings = []
    advisor_by_cat = index.get("advisor_by_category", {})
    category_to_pillar = {
        "Cost": "Cost Optimization",
        "Security": "Security",
        "HighAvailability": "Reliability",
        "OperationalExcellence": "Operational Excellence",
        "Performance": "Performance Efficiency",
    }
    for category, recs in advisor_by_cat.items():
        pillar = category_to_pillar.get(category, category)
        for rec in recs:
            desc = rec.get("short_description") or "Recomendación de Azure Advisor"
            findings.append({
                "id": rec.get("id") or rec.get("name") or "",
                "domain": pillar,
                "category": category,
                "impact": rec.get("impact", "Medium"),
                "description": desc,
                "short_description": desc,
                "recommendation": rec.get("remediation") or "Revisar en Azure Portal > Advisor",
                "source": "Azure Advisor",
            })
    return findings
