# QUICKSTART — IA Agente - Tools y Math (3 minutos)

## 🚀 En 3 pasos

### Paso 1: Preparar Ollama (1 minuto)

En una **terminal separada**:

```bash
# Verificar que Ollama está instalado
ollama --version

# Descargar el modelo (primera vez: ~5 min)
ollama pull llama3.1:8b-instruct-q2_K

# Ejecutar el servidor
ollama serve
```

Debe mostrar: `Listening on 127.0.0.1:11434`

### Paso 2: Instalar Dependencias (1 minuto)

En la **terminal del proyecto**:

```bash
C:\workspace-vc\env-llm-314\Scripts\python.exe -m pip install -r requirements.txt
```

### Paso 3: Ejecutar Notebook (1 minuto)

```bash
C:\workspace-vc\env-llm-314\Scripts\python.exe -m jupyter notebook
```

1. Abre: `AI Math Assistant - LangChain Tool Calling_LLM_local.ipynb`
2. Kernel → Change kernel → Python 3.14 (env-llm-314)
3. Run All (Ctrl+Shift+Enter) o celda por celda (Shift+Enter)

**Esperado**: Sin errores, con logs en `logs/` y resultados en `outputs/`.

---

## ✅ Verificación Rápida

Después de ejecutar, verifica:

```bash
# 1. Logs creados
ls logs/
# → ai_math_YYYYMMDD.log

# 2. Resultados guardados
ls outputs/
# → resultado_YYYYMMDD_HHMMSS.txt

# 3. Contenido del log
cat logs/ai_math_*.log | tail -20
# → Debe ver: "✅ Agente ReAct creado"
```

---

## 🔧 Si Algo Falla

| Error | Causa | Solución |
|---|---|---|
| `ConnectionError: Connection refused [IP:11434]` | Ollama no corre | `ollama serve` en otra terminal |
| `Model not found: llama3.1:8b` | Modelo no descargado | `ollama pull llama3.1:8b-instruct-q2_K` |
| `ModuleNotFoundError: langchain` | Dependencias no instaladas | `pip install -r requirements.txt` |
| Kernel error | Ambiente incorrecto | Kernel → Change → Python 3.14 |

Ver **SOLUCION_ERRORES.md** para más.

---

## 📊 Salida Esperada

### En Jupyter

```
✅ Configuración cargada: IA Agente - Tools y Math
   Modelo: llama3.1:8b-instruct-q2_K
   Base URL: http://localhost:11434
   Lenguaje: es

✅ LLM Ollama configurado
   Modelo: llama3.1:8b-instruct-q2_K
   Temperature: 0.0
   Contexto: 8192 tokens

✅ Herramientas matemáticas definidas:
   • sumar_numeros
   • restar_numeros
   • multiplicar_numeros
   • dividir_numeros

============================================================
CONSULTAS DE EJEMPLO
============================================================

[Consulta 1] ¿Cuánto es 5 + 3 + 10?
------
Respuesta: 5 + 3 + 10 = 18

[Consulta 2] Réstame 50 menos 12 menos 8.
------
Respuesta: 50 - 12 - 8 = 30

...
```

### En `logs/ai_math_YYYYMMDD.log`

```
[2026-09-18 10:30:45] ai_math_agent - INFO - 🚀 Iniciando IA Agente - Tools y Math
[2026-09-18 10:30:46] ai_math_agent - INFO - ✅ LLM inicializado: llama3.1:8b-instruct-q2_K
[2026-09-18 10:30:47] ai_math_agent - INFO - Suma: 5 y 3 y 10 = 18.0
...
```

---

## 🎯 Siguiente

1. **Entender cómo funciona**: Lee **README.md** (5 min)
2. **Casos de uso**: Consulta **EJEMPLOS.md** (10 min)
3. **Crear tu propia herramienta**: Ver sección "Extender" en **MANUAL.md**
