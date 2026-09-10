# SETUP — RAG-AgentAI: Guía de Preparación del Entorno

**Versión:** 1.0  
**Python:** 3.13 (env-llm-ia)  
**Actualizado:** 2026-09-05

---

## 🎯 Resumen ejecutivo

Antes de ejecutar RAG-AgentAI, necesitas:

1. **Python 3.13** en `C:\workspace-vc\env-llm-ia`
2. **Docker** con Chroma corriendo en puerto 8000
3. **Ollama** con dos modelos descargados
4. **Dependencias Python** instaladas

Este documento te guía paso a paso. Tiempo estimado: **15-20 minutos** (depende de velocidad de descarga).

---

## 📖 Guía de lectura recomendada

**Primer uso (si es la primera vez):**
1. ✅ **Este archivo (SETUP.md)** — Instala y verifica todo
2. 📊 **[FLUJO_COMPLETO.md](FLUJO_COMPLETO.md)** — Entiende qué sucede en cada fase
3. 👁️ **[MONITORING_GUIDE.md](MONITORING_GUIDE.md)** — Observa en vivo cómo funciona

**Uso regular (después de setup):**
1. 📖 **[MANUAL.md](MANUAL.md)** — Cómo usar la app
2. ⚙️ **[README.md](README.md)** — Referencia rápida de config

**Profundizar:**
- 🏗️ **[ARCHITECTURE_DETAILED.md](ARCHITECTURE_DETAILED.md)** — Decisiones de diseño
- 💾 **[CHROMA_VECTORIZATION.md](CHROMA_VECTORIZATION.md)** — Deep-dive en embeddings

---

## ✅ Prerequisitos verificados

- ✅ Windows 11
- ✅ **Ollama** instalado y accesible (`ollama` comando disponible)
- ✅ **Python 3.13** en `C:\workspace-vc\env-llm-ia`
- ✅ **ChromaDB** (opción A: nativo en Windows vía `pip`, opción B: Docker)

**Si NO tienes Ollama y Python 3.13, instálalos primero. ChromaDB se instala en el Paso 2.**

---

## Paso 1: Verificar Python 3.13

```powershell
# Abre PowerShell (como administrador)
C:\workspace-vc\env-llm-ia\Scripts\python.exe --version
# Esperado: Python 3.13.x
```

Si obtienes error, instala el environment:
```powershell
python -m venv C:\workspace-vc\env-llm-ia
```

---

## Paso 2: Instalar dependencias Python

### Opción A: Instalación automática (recomendado si hay errores)

```powershell
# 1. Navega a la carpeta del proyecto
cd C:\Claude\dev-ia\RAG-AgentAI

# 2. Ejecuta el script de instalación fix
powershell -ExecutionPolicy Bypass -File INSTALL_FIX.ps1

# Esto instala con modo "wheels-only" para evitar compilación
# Tarda 3-5 minutos
```

### Opción B: Instalación manual

```powershell
# 1. Navega a la carpeta del proyecto
cd C:\Claude\dev-ia\RAG-AgentAI

# 2. Activa el environment
C:\workspace-vc\env-llm-ia\Scripts\activate

# 3. Limpia caché de pip (importante)
pip cache purge

# 4. Instala requirements.txt
pip install -r requirements.txt --only-binary :all:

# Tarda 3-5 minutos (descarga torch, docling, etc.)
```

**Esperado al final:**
```
Successfully installed langchain-0.3.16 langchain-community-0.3.16 ... (25+ paquetes)
```

### ⚠️ Si falla con "pandas compilation error"

**SOLUCIÓN:** Usamos INSTALL_FIX.ps1 que:
- Elimina pandas (no se usa en el código)
- Usa mode `--only-binary` para evitar compilación Cython
- Tiene fallback automático

```powershell
powershell -ExecutionPolicy Bypass -File INSTALL_FIX.ps1
```

---

## Paso 2.5: Pre-descargar modelos de Docling (Operación Offline) ⭐

**IMPORTANTE:** Docling y EasyOCR necesitan modelos pre-descargados para que RAG-AgentAI
funcione **100% offline** sin contactar HuggingFace en runtime. Este paso se hace
**UNA SOLA VEZ** y cachea los modelos localmente.

### 2.5.A: Descargar modelos de layout/tablas de Docling

```powershell
# 1. Asegúrate de tener internet disponible
# 2. Navega a la carpeta del proyecto
cd C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\04 Agentic RAG\RAG-AgentAI

# 3. Ejecuta el script de descarga (UNA SOLA VEZ, ~5-10 minutos)
python scripts/download_local_models.py

# Esperado:
# ✅ SUCCESS!
#    Modelos guardados en: C:\workspace-vc\...\models\docling
#    Tamaño: ~1.5 GB
```

**¿Qué sucede?**
- Se descargan modelos de layout, detección de tablas, ensamblaje de página
- Se cachean en `./models/docling/` (dentro del proyecto)
- A partir de ahora, Docling NUNCA contactará HuggingFace

### 2.5.B: Pre-cachear modelos de EasyOCR (OCR en imágenes)

EasyOCR descarga sus modelos automáticamente en el primer uso. Para pre-cachearlo
**con internet disponible**, antes de desconectar la red:

```powershell
# 1. Asegúrate de que config.ini tiene:
#    [document_processor]
#    do_ocr = true

# 2. Descarga un PDF de ejemplo con IMÁGENES (gráficos, tablas, etc.)
#    (Cualquier PDF de este proyecto sirve: google-2024-environmental-report.pdf, etc.)

# 3. Sube el PDF en la UI (http://127.0.0.1:5020)
#    - Verá logs: "Processing file: google-2024-environmental-report.pdf"
#    - La primera ejecución tarda ~30-60 seg (EasyOCR descarga modelos)
#    - Los modelos se guardan en ./models/easyocr/

# 4. Cuando termine, los modelos están cacheados localmente ✓

# 5. OPCIONAL: para operación offline estricta, edita config.ini:
#    [document_processor]
#    download_enabled = false  (comentado, o falso según parámetro futuro)
#    (Esto hace que Docling falle rápido en modo offline si faltan modelos,
#     en vez de esperar timeout)
```

**Resultado esperado después de procesar un PDF con OCR:**
```
./models/easyocr/
├── craft_mlt_25k.onnx          (detector de texto)
├── ...
└── (otros modelos de idioma/detección)
```

### 2.5.C: Verificar que todo está listo para offline

```powershell
# Verifica que ambas carpetas de modelos existen
Get-ChildItem ./models/

# Esperado:
# Mode  Name
# ----  ----
# d----  docling   ← layout, tablas, etc.
# d----  easyocr   ← OCR models (si ya procesaste un PDF con OCR)
```

**LISTO PARA OPERACIÓN OFFLINE:** A partir de aquí, RAG-AgentAI corre 100% localmente
sin contactar HuggingFace, incluso si desconectas la red.

---

## Paso 3: Iniciar ChromaDB (Base de Datos Vectorial)

ChromaDB es la base de datos donde se guardan los embeddings de tus documentos. **Tienes 2 opciones:**

### 3.A: Opción Recomendada - ChromaDB Nativo en Windows (sin Docker)

```powershell
# 1. Ya está en requirements.txt (se instaló en Paso 2)
# 2. Ejecuta ChromaDB directamente:
chroma run --host localhost --port 8000 --path ./chroma_data

# Esperado:
# Starting Chroma using DirectClient.
# Chroma is running at http://localhost:8000
```

**Ventajas:**
- ✅ Sin Docker/WSL
- ✅ Más rápido
- ✅ Datos en `./chroma_data/` (fácil de respaldar)

**Verificar que funciona:**
```powershell
# En otra terminal:
curl http://localhost:8000/api/v2/heartbeat
# Respuesta esperada: {}  (HTTP 200)
```

---

### 3.B: Alternativa - ChromaDB en Docker (requiere Docker)

Si prefieres usar Docker (más pesado):

```powershell
# Opción B1: Primera vez (descargar imagen)
docker run -d -p 8000:8000 chromadb/chroma:latest

# Opción B2: Si ya existe contenedor
docker start <container_id>
```

**Verificar:**
```powershell
curl http://localhost:8000/api/v2/heartbeat
```

---

**Nota:** ChromaDB usa API v2 (v1 está deprecada). Config en `config.ini`:
```ini
[chroma]
host = localhost
port = 8000
```

---

## Paso 4: Descargar modelos en Ollama

Necesitas dos modelos:

1. **mxbai-embed-large** (670 MB) — para convertir texto a vectores
2. **qwen2.5:7b-instruct-q4_K_M** (4.7 GB) — para responder preguntas

### 4.1 Verificar que Ollama está corriendo

```powershell
# Debería devolver versión de Ollama
ollama -v

# Y ver el status:
curl http://localhost:11434/api/tags
```

### 4.2 Descargar los modelos

```powershell
# 1. Descargar embedding model (670 MB, ~2-3 min)
ollama pull mxbai-embed-large

# 2. Descargar LLM text model (4.7 GB, ~15-20 min con conexión normal)
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Verificar que están instalados
ollama list
# Debería mostrar:
# mxbai-embed-large           670 MB
# qwen2.5:7b-instruct-q4_K_M  4.7 GB
```

**Nota sobre modelos alternativos:**
- Si tienes GPU RTX A4500 (16 GB), puedes usar `qwen2.5:14b-instruct-q4_K_M` (mejor calidad)
- Si tienes GPU RTX 3050 (6 GB), mantén `qwen2.5:7b-instruct-q4_K_M`
- Si quieres pruebas rápidas: usa `qwen2.5:3b-instruct` (1.3 GB, más rápido pero menos preciso)

Actualiza los nombres de modelos en **`config.ini`** sección `[ollama]` si cambias.

---

## Paso 5: Configurar config.ini

Abre **`config.ini`** en tu editor favorito y verifica:

```ini
[ollama]
base_url = http://localhost:11434        # URL de Ollama (cambiar si es remoto)
text_model = qwen2.5:7b-instruct-q4_K_M # Modelo que descargaste en Paso 4
temperature = 0.1                        # 0.0 = determinístico, 1.0 = creativo

[embeddings]
embedding_model = mxbai-embed-large     # Coincide con lo que descargaste

[chroma]
host = localhost                         # Debe coincidir con donde corre Docker
port = 8000                              # Puerto Docker
collection_name = rag_agentai_documents  # Nombre de la colección (se crea automáticamente)

[gradio]
server_port = 5020                       # Puerto web (http://127.0.0.1:5020)
```

**Importante:** Si Ollama está en una máquina diferente (ej. `http://convergenciax02:11434`), actualiza `base_url`.

---

## Paso 6: Validar que todo funciona (Smoke Test)

```powershell
# Desde C:\Claude\dev-ia\RAG-AgentAI con env activado:
python validate_smoke_test.py

# Esperado: Todos los checks ✓
# ✓ Config loads OK
# ✓ Settings loaded
# ✓ Ollama connectivity OK
# ✓ Chroma connectivity OK
# ✓ All components instantiate OK
# ✓ Smoke test PASSED
```

Si algo falla, ve a **Troubleshooting** abajo.

---

## Paso 7: Crear la base de datos Chroma (primera vez)

La BD se crea automáticamente cuando cargas documentos. Pero puedes pre-crearla vacía:

```powershell
# Activar env
C:\workspace-vc\env-llm-ia\Scripts\activate

# Ejecutar script de inicialización
python -c "from retriever.builder import RetrieverBuilder; RetrieverBuilder().build_empty_retriever()"

# O simplemente: carga un documento en la UI (Paso 9)
```

La colección **`rag_agentai_documents`** se crea en Chroma automáticamente.

---

## 🚀 Paso 8: Ejecutar la aplicación

```powershell
# Con env-llm-ia activado:
python app.py

# Esperado:
# INFO:     Uvicorn running on http://127.0.0.1:5020
```

Abre el navegador:
```
http://127.0.0.1:5020
```

---

## 📚 Paso 9: Probar con documentos de ejemplo

1. En la UI, selecciona un ejemplo del menú **"Cargar Ejemplo"**
2. Haz una pregunta relacionada (ej. "¿Cuál es la eficiencia PUE en 2022?")
3. Presiona **"Enviar"**
4. Espera **10-30 segundos** (depende del modelo y GPU)
5. Verás:
   - **Respuesta:** Generada desde los documentos
   - **Reporte de Verificación:** Dice si la respuesta está soportada

---

## 🔧 Troubleshooting

### "Cannot connect to Ollama"
```
Error: httpx._exceptions.ConnectError: Unable to connect to http://localhost:11434

Soluciones:
1. Verifica que Ollama está corriendo: ollama list
2. Si no, inicia: ollama serve (en otra terminal)
3. Si es remoto, actualiza base_url en config.ini
4. Verifica firewall (puerto 11434 debe estar abierto)
```

### "Cannot connect to Chroma"
```
Error: Connection refused: ('localhost', 8000)

Soluciones:
1. Verifica que Docker está corriendo: docker ps
2. Verifica que Chroma está en puerto 8000:
   curl http://localhost:8000/api/v1
3. Si no, arranca Docker Chroma:
   docker run -d -p 8000:8000 chromadb/chroma:latest
```

### "Model not found: qwen2.5:7b-instruct-q4_K_M"
```
Error: model 'qwen2.5:7b-instruct-q4_K_M' not found

Soluciones:
1. Descarga el modelo:
   ollama pull qwen2.5:7b-instruct-q4_K_M
2. Espera a que termine (puede ser 15-20 min)
3. Verifica: ollama list
```

### "ModuleNotFoundError: No module named 'torch'" o "pandas compilation error"
```
Error durante pip install requirements.txt:
  ninja: build stopped: subcommand failed
  error: metadata-generation-failed × Encountered error while generating package metadata

Causa: pandas o torch intentan compilar desde código fuente (Cython)

SOLUCIÓN RÁPIDA:
1. Usa INSTALL_FIX.ps1:
   powershell -ExecutionPolicy Bypass -File INSTALL_FIX.ps1

SOLUCIÓN MANUAL:
1. Limpia caché:
   pip cache purge

2. Instala con --only-binary (solo wheels precompilados):
   pip install -r requirements.txt --only-binary :all:

3. Si sigue fallando, verifica que usas Python 3.13:
   C:\workspace-vc\env-llm-ia\Scripts\python.exe --version
   # Debe mostrar: Python 3.13.x

4. Si todo falla, reinstala el environment:
   python -m venv C:\workspace-vc\env-llm-ia
   C:\workspace-vc\env-llm-ia\Scripts\activate
   pip install -r requirements.txt --only-binary :all:
```

### "Application starts but UI is blank or slow"
```
Soluciones:
1. Abre la consola del navegador (F12) y busca errores
2. Revisa logs/rag_agentai.log
3. Si el modelo es lento: reduce vector_search_k en config.ini (de 10 a 5)
4. Si Ollama es lento: aumenta keep_alive en config.ini
```

---

## 📊 Verificación de recursos (opcional)

Antes de ejecutar, asegúrate de tener suficientes recursos:

```powershell
# Ver uso de VRAM
nvidia-smi  # Si tienes NVIDIA GPU

# Ver VRAM después de cargar un modelo
# En PowerShell, después de que Ollama lo cargue
```

**Requisitos mínimos:**
- GPU VRAM: 6 GB (RTX 3050) ✓ Suficiente
- RAM: 8 GB ✓ Suficiente
- Disco: 10 GB libres ✓ Para modelos + DB

---

## ✅ Checklist antes de MANUAL.md

- [ ] Python 3.13 verificado
- [ ] requirements.txt instalados sin errores
- [ ] Chroma Docker corriendo (puerto 8000)
- [ ] Ollama corriendo (puerto 11434)
- [ ] Modelos descargados (`ollama list` muestra ambos)
- [ ] config.ini actualizado con tus paths/URLs
- [ ] validate_smoke_test.py pasa ✓
- [ ] app.py se ejecuta sin errores

**Si todos los checks ✓, sigue a MANUAL.md para usar la app.**

---

## 📞 Soporte

- Logs detallados: `logs/rag_agentai.log`
- Código: `C:\Claude\dev-ia\RAG-AgentAI`
- Preguntas: Ver sección **Troubleshooting** o revisar MANUAL.md

