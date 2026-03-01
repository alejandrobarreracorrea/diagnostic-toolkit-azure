#!/usr/bin/env python3
"""
Report Generator - Generación de reportes para Azure Well-Architected.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from jinja2 import Template

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    from evidence import WELL_ARCH_VERSION, WELL_ARCH_DOC_URL
except ImportError:
    WELL_ARCH_VERSION = "2024"
    WELL_ARCH_DOC_URL = "https://learn.microsoft.com/en-us/azure/well-architected/"


class ReportGenerator:
    """Generador de reportes para Azure Well-Architected."""

    def __init__(self, run_dir: str, templates_dir: Path):
        self.run_dir = Path(run_dir)
        self.templates_dir = Path(templates_dir)
        self.output_dir = self.run_dir / "outputs" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self):
        """Generar todos los reportes."""
        data = self._load_data()
        self._generate_executive_summary(data)
        self._generate_findings_report(data)
        self._generate_scorecard(data)
        self._generate_improvement_plan(data)
        logger.info("Reportes generados en: %s", self.output_dir)

    def _load_data(self) -> Dict:
        data = {}
        run = self.run_dir
        # Index
        idx_file = run / "index" / "index.json"
        data["index"] = {}
        if idx_file.exists():
            try:
                with open(idx_file, "r", encoding="utf-8") as f:
                    data["index"] = json.load(f)
            except Exception as e:
                logger.warning("Error cargando índice: %s", e)
        # Inventory (outputs/inventory.json)
        inv_file = run / "outputs" / "inventory.json"
        data["inventory"] = {}
        if inv_file.exists():
            try:
                with open(inv_file, "r", encoding="utf-8") as f:
                    data["inventory"] = json.load(f)
            except Exception as e:
                logger.warning("Error cargando inventario: %s", e)
        # Findings (list)
        find_file = run / "outputs" / "findings.json"
        data["findings"] = []
        if find_file.exists():
            try:
                with open(find_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                data["findings"] = raw if isinstance(raw, list) else raw.get("findings", [])
            except Exception as e:
                logger.warning("Error cargando hallazgos: %s", e)
        # Evidence pack
        ev_file = run / "outputs" / "evidence" / "evidence_pack.json"
        data["evidence_pack"] = {}
        if ev_file.exists():
            try:
                with open(ev_file, "r", encoding="utf-8") as f:
                    data["evidence_pack"] = json.load(f)
            except Exception as e:
                logger.warning("Error cargando evidence pack: %s", e)
        # Metadata
        meta_file = run / "raw" / "metadata.json"
        data["metadata"] = {}
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data["metadata"] = json.load(f)
            except Exception as e:
                logger.warning("Error cargando metadata: %s", e)
        return data

    def _generate_executive_summary(self, data: Dict):
        tpl = self.templates_dir / "executive_summary.md"
        if not tpl.exists():
            logger.warning("Template no encontrado: %s", tpl)
            return
        inv = data.get("inventory", {})
        subs = data.get("metadata", {}).get("subscriptions", inv.get("subscriptions", []))
        sub_ids = [s.get("subscription_id", s) if isinstance(s, dict) else s for s in subs]
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "subscription_ids": sub_ids[:5],
            "subscriptions_count": len(subs),
            "total_resources": inv.get("total_resources", 0),
            "resource_types_count": inv.get("resource_types_count", 0),
            "findings_count": len(data.get("findings", [])),
            "top_resource_types": inv.get("top_resource_types", [])[:10],
            "well_arch_version": (data.get("evidence_pack") or {}).get("metadata", {}).get("well_arch_version", WELL_ARCH_VERSION),
        }
        with open(tpl, "r", encoding="utf-8") as f:
            out = Template(f.read()).render(**context)
        (self.output_dir / "executive_summary.md").write_text(out, encoding="utf-8")
        logger.info("Resumen ejecutivo generado")

    def _generate_findings_report(self, data: Dict):
        tpl = self.templates_dir / "findings_report.md"
        if not tpl.exists():
            logger.warning("Template no encontrado: %s", tpl)
            return
        findings = data.get("findings", [])
        by_domain = {}
        by_severity = {"High": 0, "Medium": 0, "Low": 0, "Info": 0}
        for f in findings:
            dom = f.get("domain", "Other")
            by_domain.setdefault(dom, []).append(f)
            sev = f.get("impact", "Medium")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_findings": len(findings),
            "findings_by_severity": by_severity,
            "findings_by_domain": by_domain,
            "all_findings": findings,
        }
        with open(tpl, "r", encoding="utf-8") as f:
            out = Template(f.read()).render(**context)
        (self.output_dir / "findings_report.md").write_text(out, encoding="utf-8")
        logger.info("Reporte de hallazgos generado")

    def _scores_from_evidence_pack(self, evidence_pack: Dict) -> Dict[str, int]:
        domain_scores = {}
        pillars = evidence_pack.get("pillars", {})
        for pillar_name, pillar_data in pillars.items():
            questions = pillar_data.get("well_architected_questions", [])
            if not questions:
                domain_scores[pillar_name] = 3
                continue
            total = len(questions)
            compliant = sum(1 for q in questions if q.get("status") == "compliant")
            domain_scores[pillar_name] = max(1, min(5, round(1 + 4 * compliant / total))) if total else 3
        return domain_scores

    def _generate_scorecard(self, data: Dict):
        tpl = self.templates_dir / "scorecard.md"
        if not tpl.exists():
            logger.warning("Template no encontrado: %s", tpl)
            return
        evidence_pack = data.get("evidence_pack", {})
        domains = [
            "Operational Excellence", "Security", "Reliability",
            "Cost Optimization", "Performance Efficiency", "Sustainability",
        ]
        if evidence_pack.get("pillars"):
            domain_scores = self._scores_from_evidence_pack(evidence_pack)
        else:
            domain_scores = {d: 3 for d in domains}
        for d in domains:
            if d not in domain_scores:
                domain_scores[d] = 3
        avg = sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "domain_scores": domain_scores,
            "average_score": avg,
            "well_arch_version": evidence_pack.get("metadata", {}).get("well_arch_version", WELL_ARCH_VERSION),
        }
        with open(tpl, "r", encoding="utf-8") as f:
            out = Template(f.read()).render(**context)
        (self.output_dir / "scorecard.md").write_text(out, encoding="utf-8")
        logger.info("Scorecard generado")

    def _generate_improvement_plan(self, data: Dict):
        tpl = self.templates_dir / "improvement_plan.md"
        if not tpl.exists():
            logger.warning("Template no encontrado: %s", tpl)
            return
        findings = data.get("findings", [])
        # Pronta: impacto High o Medium, máximo 20
        pronta = [f for f in findings if f.get("impact") in ("High", "Medium")][:20]
        mri = [f for f in findings if f.get("impact") not in ("High", "Medium") or f not in pronta][:30]
        # Añadir ítems desde evidence (preguntas no cumplidas)
        evidence_pack = data.get("evidence_pack", {})
        for pillar_name, pillar_data in (evidence_pack.get("pillars") or {}).items():
            for q in pillar_data.get("well_architected_questions", []):
                if q.get("status") != "review":
                    continue
                mri.append({
                    "id": q.get("id", ""),
                    "title": (q.get("question", ""))[:80] + ("..." if len(q.get("question", "")) > 80 else ""),
                    "domain": pillar_name,
                    "impact": "Medium",
                    "description": "Pregunta Well-Architected sin evidencia suficiente.",
                    "recommendation": "Revisar evidencias del pilar y documentar o implementar mejores prácticas.",
                    "source": "Evidence Pack",
                })
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "well_arch_version": evidence_pack.get("metadata", {}).get("well_arch_version", WELL_ARCH_VERSION),
            "improvement_plan_pronta": pronta,
            "improvement_plan_mri": mri,
        }
        with open(tpl, "r", encoding="utf-8") as f:
            out = Template(f.read()).render(**context)
        (self.output_dir / "improvement_plan.md").write_text(out, encoding="utf-8")
        logger.info("Plan de mejoras generado")


def main():
    parser = argparse.ArgumentParser(description="Azure Report Generator")
    parser.add_argument("run_dir", help="Directorio del run")
    parser.add_argument("--templates", default=None, help="Directorio de templates (default: templates/ en proyecto)")
    args = parser.parse_args()
    templates_dir = Path(args.templates) if args.templates else Path(__file__).resolve().parent.parent / "templates"
    gen = ReportGenerator(args.run_dir, templates_dir)
    gen.generate_all()
    return 0


if __name__ == "__main__":
    exit(main() or 0)
