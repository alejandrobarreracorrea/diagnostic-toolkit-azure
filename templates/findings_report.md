# Reporte de Hallazgos - Azure Well-Architected Diagnostic

**Fecha:** {{ date }}

---

## Resumen

- **Total de Hallazgos:** {{ total_findings }}
- **Por Impacto:**
  - **High:** {{ findings_by_severity.get('High', 0) }}
  - **Medium:** {{ findings_by_severity.get('Medium', 0) }}
  - **Low:** {{ findings_by_severity.get('Low', 0) }}
  - **Info:** {{ findings_by_severity.get('Info', 0) }}

---

## Hallazgos por Dominio (Pilar)

{% for domain, domain_findings in findings_by_domain.items() %}

### {{ domain }}

{% for finding in domain_findings %}
#### {{ finding.short_description or finding.description or finding.id }} ({{ finding.id or finding.recommendation_id }})

- **Impacto:** {{ finding.impact }}
- **Categoría:** {{ finding.category }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}
- **Origen:** {{ finding.source }}

{% endfor %}

{% endfor %}

---

## Tabla resumen

| ID | Dominio | Impacto | Descripción |
|----|---------|---------|-------------|
{% for finding in all_findings %}| {{ finding.id or finding.recommendation_id }} | {{ finding.domain }} | {{ finding.impact }} | {{ (finding.short_description or finding.description or '')[:60] }}... |
{% endfor %}

---

**Fuente:** Azure Advisor. Revisar en Azure Portal > Advisor para detalles y remediación.
