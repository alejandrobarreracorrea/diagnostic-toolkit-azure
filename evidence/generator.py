#!/usr/bin/env python3
"""
Evidence Pack Generator - Evidencias para Azure Well-Architected Review.

Genera evidencias por pilar a partir del índice (recursos + Advisor).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from evidence import WELL_ARCH_VERSION, WELL_ARCH_DOC_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PILLARS = [
    "Operational Excellence",
    "Security",
    "Reliability",
    "Cost Optimization",
    "Performance Efficiency",
    "Sustainability",
]

# Mapeo categoría Advisor -> pilar
ADVISOR_CATEGORY_TO_PILLAR = {
    "Cost": "Cost Optimization",
    "Security": "Security",
    "HighAvailability": "Reliability",
    "OperationalExcellence": "Operational Excellence",
    "Performance": "Performance Efficiency",
}


class EvidenceGenerator:
    """Generador de evidence pack para Azure Well-Architected."""

    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.raw_dir = self.run_dir / "raw"
        self.index_dir = self.run_dir / "index"
        self.output_dir = self.run_dir / "outputs" / "evidence"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        questions_file = Path(__file__).parent / "well_architected_questions_azure.json"
        mapping_file = Path(__file__).parent / "question_resource_mapping.json"
        self.well_architected_questions = {}
        self.question_resource_mapping = {}
        if questions_file.exists():
            with open(questions_file, "r", encoding="utf-8") as f:
                self.well_architected_questions = json.load(f)
        if mapping_file.exists():
            with open(mapping_file, "r", encoding="utf-8") as f:
                self.question_resource_mapping = json.load(f)

    def generate(self):
        """Generar evidence pack completo."""
        logger.info("Generando evidence pack para Azure Well-Architected Framework")
        index_file = self.index_dir / "index.json"
        if not index_file.exists():
            logger.error("Índice no encontrado: %s", index_file)
            return

        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)

        evidence_pack = {
            "metadata": {
                "run_dir": str(self.run_dir),
                "generated_at": datetime.utcnow().isoformat(),
                "subscriptions": index.get("subscriptions", []),
                "well_arch_version": WELL_ARCH_VERSION,
                "well_arch_url": WELL_ARCH_DOC_URL,
            },
            "pillars": {},
        }

        for pillar in PILLARS:
            logger.info("Generando evidencias para: %s", pillar)
            evidence_pack["pillars"][pillar] = self._generate_pillar_evidence(pillar, index)

        out_file = self.output_dir / "evidence_pack.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(evidence_pack, f, indent=2, default=str)
        logger.info("Evidence pack guardado en: %s", out_file)

    def _generate_pillar_evidence(self, pillar: str, index: Dict) -> Dict:
        """Generar evidencias para un pilar."""
        pillar_key = pillar.lower().replace(" ", "_")
        if pillar_key == "cost_optimization":
            pillar_key = "cost_optimization"
        elif pillar_key == "performance_efficiency":
            pillar_key = "performance_efficiency"
        elif pillar_key == "operational_excellence":
            pillar_key = "operational_excellence"

        evidence = []
        resource_types = index.get("resource_types", {})

        # Evidencia por tipos de recurso relacionados al pilar
        mapping = self.question_resource_mapping.get(pillar_key, {})
        for qid, qmap in mapping.items():
            types = qmap.get("resource_types", [])
            for rtype in types:
                count = resource_types.get(rtype, 0)
                if count > 0:
                    evidence.append({
                        "category": "resource",
                        "resource_type": rtype,
                        "count": count,
                        "question_id": qid,
                    })

        # Recomendaciones de Advisor para este pilar
        advisor_by_cat = index.get("advisor_by_category", {})
        for adv_cat, pillar_name in ADVISOR_CATEGORY_TO_PILLAR.items():
            if pillar_name != pillar:
                continue
            recs = advisor_by_cat.get(adv_cat, [])
            for rec in recs[:50]:  # límite por categoría
                evidence.append({
                    "category": "advisor",
                    "impact": rec.get("impact"),
                    "short_description": rec.get("short_description"),
                    "recommendation_id": rec.get("id"),
                })

        # Preguntas Well-Architected con estado sugerido
        questions_config = self.well_architected_questions.get(pillar_key, {})
        well_arch_questions = []
        for qid, qdata in questions_config.items():
            related_types = (mapping.get(qid) or {}).get("resource_types", [])
            has_evidence = any(resource_types.get(t, 0) > 0 for t in related_types)
            well_arch_questions.append({
                "id": qid,
                "question": qdata.get("question", ""),
                "best_practices": qdata.get("best_practices", []),
                "evidence_present": has_evidence,
                "status": "compliant" if has_evidence else "review",
            })

        return {
            "evidence": evidence,
            "well_architected_questions": well_arch_questions,
            "summary": f"{len(evidence)} evidencias, {len(well_arch_questions)} preguntas Well-Architected.",
        }
