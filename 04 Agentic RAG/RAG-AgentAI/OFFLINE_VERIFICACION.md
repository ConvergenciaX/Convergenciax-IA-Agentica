# ✅ CHECKLIST — Verificación de Operación Offline

**Objetivo:** Validar que RAG-AgentAI corre 100% localmente sin contactar HuggingFace.

---

## 📋 Fase 1: Preparación (CON internet)

### ✓ Instalación
- [ ] `python -m venv` o `env-llm-ia` activado
- [ ] `pip install -r requirements.txt --only-binary :all:` completado sin errores
- [ ] `python validate_smoke_test.py` pasa 38/38 tests

### ✓ Descargar modelos de Docling (1.5 GB)
```powershell
python scripts/download_local_models.py
```
- [ ] Script ejecutado sin errores
- [ ] Carpeta `./models/docling/` creada
- [ ] Archivos descargados (~1.5 GB)
- [ ] Log: "✅ SUCCESS! Modelos guardados en: ..."

### ✓ Pre-cachear modelos de EasyOCR (opcional, 500 MB)
```powershell
# En la UI: subir un PDF con imágenes
python app.py
# Sube PDF → esperar 30-60 seg en primera ejecución
```
- [ ] Primera carga lenta (OCR descargando)
- [ ] Carpeta `./models/easyocr/` creada (después de primera ejecución con OCR)
- [ ] Segundo documento procesa más rápido (modelos cacheados)

---

## 🔧 Fase 2: Verificación de Configuración

### ✓ config.ini — Sección [document_processor]
```powershell
Get-Content config.ini | Select-String -Pattern "\[document_processor\]" -A 10
```
- [ ] `docling_artifacts_path = ./models/docling`
- [ ] `do_ocr = true` (o false si prefieres)
- [ ] `docling_ocr_models_path = ./models/easyocr`

### ✓ config/settings.py — Nuevas propiedades
```powershell
Get-Content config/settings.py | Select-String -Pattern "DOCLING_ARTIFACTS_PATH|DOCLING_DO_OCR|DOCLING_OCR_MODELS_PATH"
```
- [ ] Propiedades `DOCLING_ARTIFACTS_PATH` existe
- [ ] Propiedad `DOCLING_DO_OCR` existe
- [ ] Propiedad `DOCLING_OCR_MODELS_PATH` existe

### ✓ app.py — Variables de entorno offline
```powershell
Get-Content app.py | Select-String -Pattern "HF_HUB_OFFLINE|TRANSFORMERS_OFFLINE"
```
- [ ] `os.environ.setdefault("HF_HUB_OFFLINE", "1")` al inicio
- [ ] `os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")` al inicio
- [ ] Logs imprimen: "Modo offline: HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1"

### ✓ document_processor/file_handler.py — Docling con artifacts_path explícito
```powershell
Get-Content document_processor/file_handler.py | Select-String -Pattern "artifacts_path|PdfPipelineOptions|EasyOcrOptions"
```
- [ ] `self.converter` creado en `__init__` (no en cada `_process_file`)
- [ ] `PdfPipelineOptions` con `artifacts_path=settings.DOCLING_ARTIFACTS_PATH`
- [ ] `EasyOcrOptions` con `download_enabled=False`
- [ ] Logs: "✓ Docling pipeline configurado para operación offline"

---

## 🌐 Fase 3: Verificación de Operación (SIN internet)

### ✓ Desconectar la red
```powershell
# Windows 10/11:
# - Opción 1: Desenchufar WiFi / desconectar ethernet
# - Opción 2: Activar modo avión
# - Opción 3: Usar firewall (netsh advfirewall)
```
- [ ] Red desconectada (verificar: `ipconfig` no muestra gateway)

### ✓ Arrancar Ollama
```powershell
ollama serve
```
- [ ] Ollama activo en `http://localhost:11434`
- [ ] Modelos disponibles: `ollama list`

### ✓ Arrancar ChromaDB
```powershell
chroma run --host localhost --port 8000 --path ./chroma_data --log-path ./chroma.log
```
- [ ] ChromaDB activo en `http://localhost:8000`
- [ ] No hay logs de "Connection refused" o "Connection timeout"

### ✓ Arrancar app.py
```powershell
python app.py
```
- [ ] Logs muestran:
  - "Modo offline: HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1" ✓
  - "✓ Docling pipeline configurado para operación offline" ✓
  - "Listening on http://127.0.0.1:5020" ✓
- [ ] No hay errores de conexión a HuggingFace
- [ ] No hay timeouts de 30+ segundos al iniciar

### ✓ Procesar un documento
```powershell
# En navegador: http://127.0.0.1:5020
# Sube: un PDF sin procesar antes (nuevo para este test)
```
- [ ] PDF sube sin errores
- [ ] Logs: "Processing file: document.pdf"
- [ ] Logs: "Procesados N fragmentos de documento"
- [ ] Logs: "✓ Vector store (Chroma) created successfully"
- [ ] **NO aparecen estos errores:**
  - ❌ "OSError: download_path doesn't exist"
  - ❌ "Cannot download from HuggingFace"
  - ❌ "Connection timeout" (>5 segundos)
  - ❌ "snapshot_download"

### ✓ Hacer una pregunta
```powershell
# En UI: ingresa una pregunta en español
# Espera respuesta
```
- [ ] Respuesta generada en <30 segundos
- [ ] Logs: "Paso 1: check_relevance"
- [ ] Logs: "Paso 2: research"
- [ ] Logs: "Paso 3: verification"
- [ ] Logs: "Pipeline completado exitosamente"
- [ ] Respuesta visible en UI

### ✓ Monitorear red (Resource Monitor)
```powershell
# Windows Task Manager → Performance → Resource Monitor → Network
# O: wmic logicaldisk get name; netstat -an | findstr ESTABLISHED
```
- [ ] Conexiones activas **SOLO a:**
  - ✅ 127.0.0.1:11434 (Ollama)
  - ✅ 127.0.0.1:8000 (ChromaDB)
  - ✅ 127.0.0.1:5020 (Gradio)
- [ ] **NO aparecen conexiones a:**
  - ❌ huggingface.co
  - ❌ cdn.huggingface.co
  - ❌ api.huggingface.co
  - ❌ Ningún host externo

---

## 🔍 Fase 4: Validación Técnica

### ✓ Archivos de modelos existen
```powershell
Get-ChildItem -Recurse ./models/ -File | Measure-Object
```
- [ ] `./models/docling/` contiene >50 archivos
- [ ] `./models/easyocr/` existe (si procesaste OCR)

### ✓ ChromaDB almacenó datos
```powershell
Get-ChildItem -Recurse ./chroma_data/ -File | Measure-Object
```
- [ ] `./chroma_data/` contiene archivos .parquet y .bin
- [ ] Tamaño > 0 (confirma que ChromaDB guardó vectores)

### ✓ Logs muestran operación correcta
```powershell
Get-Content -Path logs/rag_agentai.log | Select-String -Pattern "offline|download|artifact" -n | head -20
```
- [ ] Logs contienen "offline mode" o "Docling pipeline configurado"
- [ ] **NO contienen:** "snapshot_download", "downloading from", "Connection refused"

### ✓ Modo offline es respetado (test negativo)
```powershell
# Renombra o borra ./models/docling/ temporalmente
Rename-Item ./models/docling ./models/docling_backup

# Intenta procesar un PDF sin internet
python app.py  # Debe FALLAR rapidamente con error offline

# Restaura
Rename-Item ./models/docling_backup ./models/docling
```
- [ ] **Con modo offline activo:** Error inmediato (no intenta red)
- [ ] **Sin modo offline:** Esperaría timeout 30+ segundos (confirmando que offline mode funciona)

---

## 📊 Resultado esperado

Si **todos** los checkpoints pasan:

✅ **RAG-AgentAI está 100% offline**
- Documentos se procesan localmente (Docling + modelos cacheados)
- Embeddings generados localmente (Ollama)
- Búsquedas en vector store local (ChromaDB)
- LLM responde localmente (Ollama)
- **Cero llamadas salientes a HuggingFace, OpenAI, o cloud**
- **Soberanía total del dato y la IA**

---

## 🐛 Si algún checkpoint falla

### Síntoma: "OSError: artifacts_path no existe"
**Causa:** `./models/docling/` no está poblado
**Fix:** 
```powershell
python scripts/download_local_models.py
```

### Síntoma: "Docling intenta descargar de HuggingFace"
**Causa:** `artifacts_path` no está siendo pasado a `PdfPipelineOptions`
**Fix:** Verificar que `document_processor/file_handler.py:__init__` tiene:
```python
pipeline_options = PdfPipelineOptions(
    artifacts_path=settings.DOCLING_ARTIFACTS_PATH,  ← Este parámetro
    ...
)
```

### Síntoma: Timeout de 30+ segundos al procesar documento
**Causa:** Docling está intentando contactar HuggingFace a pesar de offline mode
**Fix:**
1. Verificar `HF_HUB_OFFLINE=1` está en `app.py` al inicio
2. Verificar `artifacts_path` apunta a carpeta correcta
3. Verificar `config.ini` tiene ruta correcta

### Síntoma: ChromaDB no recibe datos
**Causa:** Conectividad local (localhost:8000)
**Fix:** Verificar ChromaDB está corriendo y accesible:
```powershell
curl http://localhost:8000/api/v2/heartbeat
# Esperado: {}  (HTTP 200)
```

---

## 📋 Resumen final

**Firma de auditoría (después de pasar todos los checkpoints):**

```
Fecha: 2026-09-06
Usuario: ___________
Entorno: Windows 11, env-llm-ia Python 3.13
Red: ☐ Desconectada  ☐ Con firewall

✅ Docling offline (modelos cacheados): SÍ
✅ EasyOCR offline (modelos pre-descargados): SÍ
✅ Ollama local (puerto 11434): SÍ
✅ ChromaDB local (puerto 8000): SÍ
✅ Variables offline (HF_HUB_OFFLINE=1): SÍ
✅ Cero conexiones externas detectadas: SÍ

RESULTADO: 🔒 RAG-AgentAI es 100% OFFLINE
```

---

**Documento de validación:** Este checklist demuestra que RAG-AgentAI cumple con
los requisitos de operación offline y soberanía de datos del proyecto (skill `ia-dev-fullstack`).

Para más detalles técnicos, ver **OPERACION_OFFLINE.md**.
