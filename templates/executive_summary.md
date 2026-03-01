# Executive Summary - Azure Well-Architected Diagnostic

**Fecha:** {{ date }}  
**Suscripciones:** {{ subscriptions_count }}  
**Framework evaluado:** Azure Well-Architected Framework (versión {{ well_arch_version }})

---

## Resumen Ejecutivo

Este reporte presenta los hallazgos del diagnóstico arquitectónico realizado en la suscripción(es) Azure. El análisis se realizó mediante Azure Resource Graph y Azure Advisor.

### Métricas Principales

- **Suscripciones evaluadas:** {{ subscriptions_count }}
- **Total de recursos:** {{ total_resources }}
- **Tipos de recurso distintos:** {{ resource_types_count }}
- **Hallazgos (Azure Advisor):** {{ findings_count }}

### Top tipos de recurso

{% for r in top_resource_types %}
- **{{ r.type }}**: {{ r.count }} recursos
{% endfor %}

---

## Conclusiones

Este diagnóstico proporciona:

1. **Inventario**: Recursos y tipos desde Resource Graph
2. **Evidencias Well-Architected**: Datos para los 6 pilares
3. **Recomendaciones**: Azure Advisor alineado a pilares (Cost, Security, High Availability, Operational Excellence, Performance)
4. **Plan de mejoras**: Priorización según impacto

### Próximos pasos

1. Revisar reporte de hallazgos y scorecard
2. Ejecutar revisión Well-Architected usando el evidence pack
3. Priorizar acciones según el plan de mejoras
4. Implementar recomendaciones de Azure Advisor

---

**Referencia:** [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/).
