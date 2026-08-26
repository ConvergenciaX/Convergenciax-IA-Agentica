# CHECKPOINTS — Agente IA - pydanticai

## 2026-08-25 — v2 local con Ollama, sin dependencia de OpenAI

- Proyecto incorporado a la tabla maestra de proyectos IA.
- Base: `pydanticai-101.ipynb` (lab de IBM SkillsNetwork) + `customer_support_tickets.csv` (dataset local, ~4 MB).
- Nuevos artefactos:
  - `pydanticai_ollama_v2.ipynb` — agente PydanticAI apuntando al endpoint OpenAI-compatible de Ollama (`OpenAIModel` + `OpenAIProvider(base_url=...)`), CSV local, `search_tickets` implementada (en el original estaba referenciada pero nunca definida, y la celda de chat tenía una indentación inválida que la rompía), celda de prueba no interactiva además del chat con `input()`.
  - `config.ini` — `[ollama]` (base_url, modelo, temperature), `[datos]` (csv_path, max_tickets_al_llm), `[logging]`.
  - `requirements.txt` — pydantic-ai[openai], pandas, nest-asyncio (sin paquete de OpenAI cloud).
  - `MANUAL.md` — documentación completa + recomendación de modelos Ollama para RTX 3050 Ti 6GB VRAM.
- **Modelo por defecto**: `qwen2.5:7b-instruct-q4_K_M` (ya estaba descargado, 4.7 GB, cabe cómodo en 6 GB VRAM). Alternativas evaluadas: `llama3.1:8b-instruct-q4_K_M` (más lento, buen razonamiento), `phi4-mini:3.8b` (más rápido, calidad algo menor). Descartados: variantes Q2 (schema-following pobre) y `deepseek-coder` (no es el dominio correcto).
- **No probado en esta sesión (build inicial)**: no se ejecutó el notebook end-to-end (requiere confirmar que `ollama serve` responde y medir latencia real del modelo elegido). `pydantic-ai` tampoco estaba instalado en el entorno usado para generar el notebook (se generó el `.ipynb` con `nbformat` directamente).
- Cómo verificar: `pip install -r requirements.txt`, confirmar `ollama list` muestra `qwen2.5:7b-instruct-q4_K_M`, correr `pydanticai_ollama_v2.ipynb` celda por celda; la celda `probar_agente(...)` debe devolver un `SupportResponse` válido antes de lanzar el chat interactivo.
- Estado: en curso — pendiente prueba end-to-end contra Ollama real.

## 2026-08-25 (fix) — ImportError OpenAIModel

- El usuario reportó `ImportError: cannot import name 'OpenAIModel' from 'pydantic_ai.models.openai'` al correr en su entorno real `c:\workspace-vc\env-llm-314` (pydantic-ai 2.34.0).
- Causa: `pydantic-ai` renombró `OpenAIModel` → `OpenAIChatModel` en la serie 2.x; el notebook se había escrito contra la API antigua.
- Fix: se reemplazó `OpenAIModel` por `OpenAIChatModel` en `pydanticai_ollama_v2.ipynb` (import y construcción del modelo), se actualizó `requirements.txt` (`pydantic-ai[openai]>=2.34.0`) y se agregó nota de compatibilidad en `MANUAL.md`.
- Verificado en `env-llm-314`: import + instanciación de `OpenAIChatModel`/`OpenAIProvider`/`Agent` corre sin error (`OK OpenAIChatModel()`). No se probó todavía una llamada real `agent.run(...)` contra Ollama en ese entorno.
- Estado: en curso — el ImportError está resuelto; falta validar `probar_agente(...)` end-to-end en `env-llm-314`.

## 2026-08-25 (fix) — Quitar rastro de OpenAI de pydanticai_ollama_v2.ipynb

- El usuario pidió eliminar cualquier código sobrante de OpenAI, específicamente en `pydanticai_ollama_v2.ipynb` (no en `pydanticai-101.ipynb`, que se dejó tal cual el lab original tras un intento previo de comentarlo que se revirtió).
- Cambio: se reemplazó `pydantic_ai.providers.openai.OpenAIProvider(base_url=..., api_key="ollama")` por `pydantic_ai.providers.ollama.OllamaProvider(base_url=...)` — el provider dedicado para Ollama que trae `pydantic-ai`, sin necesidad de un `api_key` placeholder.
- `OpenAIChatModel` se mantiene (no hay una clase `OllamaModel` separada en `pydantic-ai`: Ollama se habla vía el mismo protocolo de chat de OpenAI, por eso el nombre de la clase sigue diciendo "OpenAI" aunque no hay ninguna dependencia real de OpenAI). Se documentó esto en `MANUAL.md` para que no genere confusión de nuevo.
- Verificado en `env-llm-314`: `OpenAIChatModel(provider=OllamaProvider(base_url=...))` + `Agent(...)` se construye sin error.
- Estado: en curso — sin rastro de OpenAI real en `pydanticai_ollama_v2.ipynb`; sigue pendiente la prueba end-to-end de `agent.run(...)` contra Ollama corriendo.
