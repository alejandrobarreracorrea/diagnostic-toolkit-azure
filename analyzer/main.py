#!/usr/bin/env python3
"""
Analyzer - Indexación, inventario y hallazgos para un run de Azure.
"""

import argparse
import json
import logging
from pathlib import Path

from analyzer.indexer import DataIndexer
from analyzer.inventory import InventoryGenerator
from analyzer.findings import get_findings_from_advisor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class Analyzer:
    """Analizador de datos recolectados de Azure."""

    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.raw_dir = self.run_dir / "raw"
        self.index_dir = self.run_dir / "index"
        self.output_dir = self.run_dir / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self):
        """Ejecutar indexación, inventario y hallazgos."""
        logger.info("Analizando run: %s", self.run_dir)
        indexer = DataIndexer(self.raw_dir, self.index_dir)
        index = indexer.index_all()

        inv_gen = InventoryGenerator(self.index_dir, self.output_dir)
        inv_gen.generate()

        findings = get_findings_from_advisor(index)
        findings_file = self.output_dir / "findings.json"
        with open(findings_file, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2, default=str)
        logger.info("Hallazgos guardados: %d en %s", len(findings), findings_file)


def main():
    parser = argparse.ArgumentParser(description="Azure Diagnostic Analyzer")
    parser.add_argument("run_dir", help="Directorio del run (ej. runs/run-xxx)")
    args = parser.parse_args()
    a = Analyzer(args.run_dir)
    a.analyze()
    return 0


if __name__ == "__main__":
    exit(main() or 0)
