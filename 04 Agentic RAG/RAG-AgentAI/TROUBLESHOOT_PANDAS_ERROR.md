# 🔧 Solución: Error "pandas compilation" / "ninja: build stopped"

**Error que ves:**
```
[49/151] Compiling Cython source C:/Users/Joel/AppData/Local/Temp/pip-install-l1atamc_/pandas_0f66bdf5900644b49b845a309bbb48e0/pandas/_libs/join.pyx
ninja: build stopped: subcommand failed.
error: metadata-generation-failed
× Encountered error while generating package metadata.
```

---

## ✅ SOLUCIÓN RÁPIDA (90% de los casos)

### Paso 1: Detén la instalación
Presiona `Ctrl+C` en PowerShell.

### Paso 2: Limpia caché de pip
```powershell
pip cache purge
```

### Paso 3: Instala con este comando (modo wheels-only)
```powershell
cd C:\Claude\dev-ia\RAG-AgentAI
C:\workspace-vc\env-llm-ia\Scripts\activate

pip install -r requirements.txt --only-binary :all:
```

**Explicación:** `--only-binary :all:` forza pip a usar wheels precompilados (no compilar desde código fuente).

---

## 🤖 SOLUCIÓN AUTOMÁTICA (recomendado)

```powershell
cd C:\Claude\dev-ia\RAG-AgentAI
powershell -ExecutionPolicy Bypass -File INSTALL_FIX.ps1
```

Este script:
- ✓ Limpia caché
- ✓ Usa `--only-binary`
- ✓ Verifica instalaciones
- ✓ Ejecuta smoke test
- ✓ Tiene fallback automático

---

## 🔍 ¿Por qué ocurre este error?

**Causa:** pandas 2.1.4 no tiene wheel precompilado para tu configuración específica, por lo que pip intenta compilar desde código fuente (Cython). Esto falla porque:
- Compiler de C/C++ no disponible o incompatible
- O conda/Visual C++ no está bien configurado

**Solución:** pandas **NO se usa en el código**. Lo removimos de requirements.txt.

---

## 📋 Verificación post-instalación

```powershell
# Verifica que todo está bien
python validate_smoke_test.py

# Debe mostrar:
# ✓ Config loads from config.ini
# ✓ Ollama base_url accessible
# ✓ LangChain core
# ... (todos los tests con ✓)
```

---

## 🆘 Si nada funciona

### Opción 1: Reinstalar environment limpio

```powershell
# 1. Borra el environment actual
Remove-Item -Recurse -Force C:\workspace-vc\env-llm-ia

# 2. Crea uno nuevo
python -m venv C:\workspace-vc\env-llm-ia

# 3. Activa
C:\workspace-vc\env-llm-ia\Scripts\activate

# 4. Instala con wheels-only
pip install -r requirements.txt --only-binary :all:
```

### Opción 2: Usar pip con modo verbose para ver qué falla

```powershell
pip install -r requirements.txt --only-binary :all: --verbose
```

Esto muestra exactamente dónde falla.

### Opción 3: Instalar paquetes uno por uno

```powershell
pip install langchain==0.3.16
pip install torch==2.6.0
pip install docling==2.15.0
# ... etc
```

---

## ✅ Cómo saber que la instalación fue exitosa

```powershell
# Estos comandos deben funcionar SIN error:
python -c "import langchain; print('✓ LangChain')"
python -c "import torch; print('✓ PyTorch')"
python -c "import docling; print('✓ Docling')"
python -c "import chromadb; print('✓ Chroma')"
python -c "import gradio; print('✓ Gradio')"

# Ejecuta el smoke test
python validate_smoke_test.py  # Debe pasar todos ✓
```

---

## 🎯 Próximo paso

Una vez que la instalación pase:

```powershell
python app.py
# Abre: http://127.0.0.1:5020
```

---

**Creado:** 2026-09-05 | **Para resolver:** pandas/Cython compilation errors en Python 3.13
