# Azure Well-Architected Diagnostic Toolkit

Herramienta de diagnóstico para evaluar cargas de trabajo en Azure según el **Azure Well-Architected Framework**. Recolecta inventario vía **Azure Resource Graph**, recomendaciones de **Azure Advisor** (alineadas a los 5 pilares oficiales + Sustainability como guía) y genera evidencias y reportes para revisión Well-Architected.

## Requisitos

- Python 3.8+
- Credenciales Azure (Azure CLI login, Managed Identity, o variables de entorno para Service Principal)
- Permisos de lectura en la(s) suscripción(es): Resource Graph, Advisor, Subscription (lectura)

## Instalación

```bash
cd diagnostic-toolkit-azure
pip install -r requirements.txt
```

## Autenticación

El tool usa **DefaultAzureCredential** (Azure Identity), que prueba varios métodos en orden. Puedes usar **Azure CLI** (`az login`), **Managed Identity** en Azure, o **Service Principal** mediante variables de entorno.

### Con Service Principal

1. **Crear el Service Principal** (si aún no existe):

   ```bash
   az ad sp create-for-rbac --name "ecad-azure-diagnostic" --role Reader --scopes /subscriptions/<SUBSCRIPTION_ID>
   ```

   Salida ejemplo (guarda estos valores):

   ```json
   {
     "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "password": "secret-value",
     "tenant": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
   }
   ```

   Para acceso a **todas las suscripciones del tenant**, asigna el rol a nivel tenant o a cada suscripción. Ejemplo para una suscripción: `--scopes /subscriptions/<SUBSCRIPTION_ID>`. Para varias, repite la asignación o usa un grupo de gestión.

2. **Permisos necesarios:** el SP debe tener al menos **Reader** en las suscripciones que quieras analizar (sirve para Resource Graph, Advisor y Subscription).

3. **Definir variables de entorno** y ejecutar:

   ```bash
   export AZURE_CLIENT_ID="appId-del-paso-1"
   export AZURE_TENANT_ID="tenant-del-paso-1"
   export AZURE_CLIENT_SECRET="password-del-paso-1"

   python3 ecad_azure.py full
   ```

   No hagas `az login`; DefaultAzureCredential usará el Service Principal. Opcionalmente restringe suscripciones:

   ```bash
   export AZURE_SUBSCRIPTION_IDS="id1,id2"
   python3 ecad_azure.py full
   ```

4. **Seguridad:** no subas el secret al repo. Usa un `.env` local (y añádelo a `.gitignore`), variables de tu CI/CD o Azure Key Vault / secret manager.

**Resumen de variables para Service Principal:**

| Variable | Descripción |
|----------|-------------|
| `AZURE_CLIENT_ID` | Application (client) ID del SP |
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `AZURE_CLIENT_SECRET` | Secret del SP |

Con estas tres definidas, el toolkit autentica con el Service Principal sin usar `az login`.

## Guía paso a paso

### 1. Instalar y preparar

```bash
cd diagnostic-toolkit-azure
pip install -r requirements.txt
```

### 2. Elegir cómo indicar suscripciones

El orden de resolución es: **argumento** → **variable de entorno** → **archivo (si está activado)** → **listar todas en el tenant (por defecto)**.

---

#### Opción A — Por defecto: listar todas las suscripciones del tenant

No configures nada. Entra en el tenant y ejecuta; el tool listará automáticamente todas las suscripciones a las que tiene acceso tu credencial.

```bash
az login
python3 ecad_azure.py full
```

O por pasos:

```bash
az login
python3 ecad_azure.py collect
# Anota el run_dir que imprime (ej. runs/run-20250129-123456)
python3 ecad_azure.py analyze runs/run-20250129-123456
python3 ecad_azure.py evidence runs/run-20250129-123456
python3 ecad_azure.py reports runs/run-20250129-123456
```

---

#### Opción B — Usar un tenant concreto (varios tenants)

Si tu identidad tiene acceso a más de un tenant y quieres fijar uno:

```bash
export AZURE_TENANT_ID="guid-del-tenant"
python3 ecad_azure.py full
```

La credencial y el listado de suscripciones se resuelven en ese tenant.

---

#### Opción C — Suscripciones por argumento

Para analizar solo unas suscripciones en esta ejecución:

```bash
python3 ecad_azure.py full --subscriptions "id1,id2,id3"
# o solo recolectar
python3 ecad_azure.py collect --subscriptions "id1,id2"
```

---

#### Opción D — Suscripciones por variable de entorno

Útil para scripts o CI sin pasar argumentos:

```bash
export AZURE_SUBSCRIPTION_ID="una-suscripcion"
# o varias
export AZURE_SUBSCRIPTION_IDS="id1,id2,id3"
python3 ecad_azure.py full
```

---

#### Opción E — Suscripciones desde archivo YAML

Para dejar fija la lista en el repositorio (por ejemplo por entorno):

1. Copia el ejemplo y edita los IDs:

   ```bash
   cp subscriptions.yaml.example subscriptions.yaml
   # Edita subscriptions.yaml
   ```

2. Formato con solo IDs:

   ```yaml
   subscription_ids:
     - "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
     - "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
   ```

   O con nombres (opcional):

   ```yaml
   subscriptions:
     - id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
       name: "Producción"
     - id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
       name: "Desarrollo"
   ```

3. Activa el archivo y ejecuta:

   ```bash
   ECAD_AZURE_USE_SUBSCRIPTIONS_FILE=1 python3 ecad_azure.py full
   ```

---

### 3. Comandos disponibles

| Comando | Descripción |
|--------|-------------|
| `python3 ecad_azure.py full` | Recolectar + analizar + evidence + reportes (todo en uno). |
| `python3 ecad_azure.py collect [--run-dir DIR]` | Solo recolectar (Resource Graph + Advisor + metadata). |
| `python3 ecad_azure.py analyze <run_dir>` | Indexar, inventario y hallazgos. |
| `python3 ecad_azure.py evidence <run_dir>` | Generar evidence pack Well-Architected. |
| `python3 ecad_azure.py reports <run_dir>` | Generar reportes en Markdown. |

Si no indicas `--run-dir` en `collect` o `full`, se crea un directorio `runs/run-YYYYMMDD-HHMMSS`.

## Estructura de un run

- `raw/`: salida del collector  
  - `metadata.json` – suscripciones  
  - `resource_graph_resources.json` / `resource_graph_counts.json` – inventario Resource Graph  
  - `advisor_recommendations.json` – recomendaciones Azure Advisor  
- `index/index.json` – índice (tipos de recurso, recomendaciones por categoría)  
- `outputs/inventory.json` – inventario resumido  
- `outputs/findings.json` – hallazgos desde Advisor  
- `outputs/evidence/evidence_pack.json` – evidencias por pilar Well-Architected  
- `outputs/reports/` – reportes en Markdown (resumen ejecutivo, scorecard, hallazgos, plan de mejoras)

## Referencias

- [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/)
- [Azure Advisor](https://learn.microsoft.com/en-us/azure/advisor/)
- [Azure Resource Graph](https://learn.microsoft.com/en-us/azure/resource-graph/)
- [Azure Security Benchmark (ASB) v3](https://learn.microsoft.com/en-us/security/benchmark/azure/) – controles referenciados en `evidence/azure_security_benchmark_controls.json`

## Notas

- No existe un JSON público de preguntas del Well-Architected Review de Azure (el assessment es interactivo en Learn/Portal); las preguntas en `evidence/well_architected_questions_azure.json` están adaptadas para uso interno.
- Sustainability se incluye como pilar en evidencias y reportes por alineación con prácticas de diseño; en la documentación oficial aparece como guía/workload, no como sexto pilar en la matriz de Advisor.
