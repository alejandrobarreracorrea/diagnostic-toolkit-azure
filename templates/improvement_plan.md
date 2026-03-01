# Plan de mejoras - Azure Well-Architected

**Fecha:** {{ date }}

**Framework:** Azure Well-Architected Framework (versión {{ well_arch_version }})

Las mejoras se estructuran en:

- **Pronta solución (30 días):** hallazgos de alto/medio impacto, quick wins.
- **Mayor complejidad (MRI):** resto de hallazgos y preguntas Well-Architected sin evidencia suficiente.

Fuentes: Azure Advisor y evidence pack (preguntas por pilar).

---

## 1. Pronta solución (30 días)

{% for finding in improvement_plan_pronta %}
### {{ finding.short_description or finding.description or finding.id }}

- **Dominio:** {{ finding.domain }}
- **Impacto:** {{ finding.impact }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}
- **Origen:** {{ finding.source }}

{% endfor %}
{% if not improvement_plan_pronta %}
*No se identificaron tareas de pronta solución en este diagnóstico.*
{% endif %}

---

## 2. Mejoras de mayor complejidad (MRI)

{% for finding in improvement_plan_mri %}
### {{ finding.title or finding.short_description or finding.description or finding.id }}

- **Dominio:** {{ finding.domain }}
- **Impacto:** {{ finding.impact }}
- **Descripción:** {{ finding.description }}
- **Recomendación:** {{ finding.recommendation }}
{% if finding.source %}- **Origen:** {{ finding.source }}{% endif %}

{% endfor %}
{% if not improvement_plan_mri %}
*No hay MRI en este diagnóstico.*
{% endif %}

---

## Notas

- Validar prioridades con el equipo técnico.
- Revisar dependencias entre mejoras.
- Re-evaluar tras implementar mejoras.

**Referencia:** [Azure Well-Architected](https://learn.microsoft.com/en-us/azure/well-architected/).
