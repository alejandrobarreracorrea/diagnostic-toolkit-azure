# Well-Architected Scorecard - Azure

**Fecha:** {{ date }}

**Framework:** Azure Well-Architected Framework (versión {{ well_arch_version }})

---

## Resumen de puntuaciones

Evaluación por los 6 pilares del Well-Architected. Escala 1 (crítico) a 5 (excelente).

**Puntuación media:** {{ "%.1f" | format(average_score) }}/5.0

---

## Puntuación por pilar

{% for domain, score in domain_scores.items() %}

### {{ domain }}

**Puntuación: {{ score }}/5**

{% if score == 5 %}
✅ **Excelente** - Sin problemas significativos en este pilar.
{% elif score == 4 %}
✅ **Bueno** - Arquitectura sólida con mejoras menores.
{% elif score == 3 %}
⚠️ **Aceptable** - Áreas de mejora identificadas.
{% elif score == 2 %}
⚠️ **Necesita mejora** - Requiere atención.
{% else %}
❌ **Crítico** - Acción inmediata recomendada.
{% endif %}

{% endfor %}

---

## Criterios

Los scores se calculan a partir del evidence pack (cumplimiento de preguntas Well-Architected por pilar) y de las recomendaciones de Azure Advisor.

- **5:** Cumplimiento fuerte
- **4:** Cumplimiento mayoritario
- **3:** Riesgo moderado
- **2:** Brechas importantes
- **1:** Riesgo alto

---

**Referencia:** [Azure Well-Architected](https://learn.microsoft.com/en-us/azure/well-architected/).
