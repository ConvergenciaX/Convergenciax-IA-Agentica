# Agente de Soporte al Cliente — PydanticAI + Ollama local

## Qué es esto

Version local del laboratorio `pydanticai-101.ipynb` (IBM SkillsNetwork). Mismo caso de
uso (chatbot de soporte que clasifica tickets, asigna prioridad y decide si escalar,
usando un schema Pydantic para forzar salida estructurada), pero:

- **Sin OpenAI API key**: el `Agent` de PydanticAI apunta al endpoint OpenAI-compatible
  de **Ollama** (`http://localhost:11434/v1`), no a la nube de OpenAI.
- **Sin salida de datos**: el CSV de tickets vive en la carpeta del proyecto y nunca sale
  de la máquina — soberanía del dato completa, apto para datos de clientes reales.
- **Config externalizada**: modelo, temperatura y rutas en `config.ini`, no hardcodeados.

Archivo principal: `pydanticai_ollama_v2.ipynb`.

## Requisitos

1. Ollama instalado y corriendo (`ollama serve`, normalmente ya es un servicio activo en
   Windows).
2. Un modelo descargado — ver sección de modelos recomendados abajo.
3. `pip install -r requirements.txt` (pydantic-ai, pandas, nest-asyncio).

## Configuración (`config.ini`)

```ini
[ollama]
base_url = http://localhost:11434/v1
modelo = qwen2.5:7b-instruct-q4_K_M
temperature = 0.1

[datos]
csv_path = customer_support_tickets.csv
max_tickets_al_llm = 10
```

Cambiar de modelo o de host de Ollama (por ejemplo si en el futuro Ollama corre en otra
máquina de la red) no requiere tocar el notebook, solo este archivo.

## Modelos LLM recomendados para tu GPU (RTX 3050 Ti Laptop, 6 GB VRAM)

Con 6 GB de VRAM el límite práctico es un modelo de **~7-8B parámetros cuantizado a
4 bits (Q4)**: ocupa entre 4-5 GB de VRAM, deja margen para el contexto y para que
Windows/el navegador usen el resto de la GPU sin que Ollama se caiga a CPU.

**Ya tienes instalados y son buena opción para este agente** (ninguno requiere descarga
adicional):

| Modelo | Tamaño en disco | Por qué sirve aquí |
|---|---|---|
| `qwen2.5:7b-instruct-q4_K_M` | 4.7 GB | **Recomendado por defecto** (ya configurado). Buen seguimiento de instrucciones y de "responde solo en este formato JSON/schema" — clave porque PydanticAI depende de que el modelo respete el `output_type`. |
| `llama3.1:8b-instruct-q4_K_M` | 4.9 GB | Alternativa sólida, algo más lento que Qwen2.5 7B en la misma GPU pero con buen razonamiento general. Útil para comparar calidad de respuesta. |
| `phi4-mini:3.8b` | 2.5 GB | El más liviano y rápido de los tres; usarlo si necesitas más velocidad o correr el agente junto con otras apps pesadas en la GPU. Calidad de clasificación algo menor que los de 7-8B. |

Evita por ahora en esta GPU:
- `llama3.1:8b-instruct-q2_K` (3.2 GB): la cuantización Q2 es demasiado agresiva —
  degrada bastante la capacidad de seguir un schema estricto, lo cual es justo lo que
  este agente necesita.
- `deepseek-coder:6.7b`: está afinado para código, no para clasificación/soporte
  conversacional — no es la herramienta correcta para esta tarea aunque cargue bien en
  la GPU.
- Modelos 13B+ en Q4 (~7-8 GB): no entran cómodos en 6 GB VRAM; Ollama haría offload
  parcial a CPU y la latencia por respuesta subiría mucho para un chat interactivo.

Si más adelante quieres exprimir algo más de calidad sin subir de tamaño, un salto
natural sería probar `qwen2.5:7b-instruct-q5_K_M` (~5.4 GB) — cabe justo en 6 GB VRAM con
poco margen para contexto largo, así que solo vale la pena si las respuestas actuales se
quedan cortas en calidad.

## Nota de compatibilidad de versión

`pydantic-ai` renombró `OpenAIModel` → `OpenAIChatModel` a partir de la serie 2.x
(el notebook original de referencia usaba una API más antigua). Este proyecto usa
`OpenAIChatModel` (probado contra `pydantic-ai==2.34.0`, entorno
`env-llm-314`). Si en el futuro ves `ImportError: cannot import name 'OpenAIModel'`
o lo inverso, es por un desfase de versión — revisa `python -c "import pydantic_ai;
print(pydantic_ai.__version__)"` y ajusta el import según lo que exponga
`pydantic_ai.models.openai` en esa versión.

## Por qué el código sigue mencionando "OpenAI" en algún lado

`pydantic-ai` no tiene una clase `OllamaModel` separada: Ollama expone su API sirviendo el
mismo protocolo de chat que usa OpenAI, así que cualquier framework se conecta a Ollama
reutilizando su cliente/wrapper "OpenAI-compatible" — es un nombre de protocolo, no una
dependencia real de OpenAI. Por eso el modelo se sigue construyendo con `OpenAIChatModel`.

Lo que sí se limpió: el provider ya no es el genérico `OpenAIProvider` con un
`api_key="ollama"` de relleno — se usa `pydantic_ai.providers.ollama.OllamaProvider`
(provider dedicado que trae `pydantic-ai` para Ollama), que no necesita api_key ni
placeholders. Con esto, en `pydanticai_ollama_v2.ipynb` no queda ningún import,
paquete ni credencial de OpenAI real — todo el tráfico va a `localhost:11434`.

## Diferencias funcionales vs. el notebook original

- `search_tickets(user_input, df)` estaba **referenciada pero nunca definida** en el
  notebook original (celda de chat con bloque `prompt` con indentación inválida que
  además rompía la celda). Se implementó: busca por Ticket ID exacto, o substring
  case-insensitive en nombre/email del cliente.
- El agente ya no recibe el CSV completo en el `instructions` (como hacía la primera
  versión del chat en el original) — con un CSV de ~4 MB eso desborda cualquier contexto
  de un modelo local de 7-8B. En su lugar, solo se le pasan las filas que hacen match
  con la consulta del usuario (máximo `max_tickets_al_llm`, igual que la segunda versión
  del chat del notebook original).
- Se agregó una celda de prueba no interactiva (`probar_agente`) para validar el agente
  sin necesitar escribir en un `input()` — útil para desarrollo y para verificar que
  Ollama responde antes de lanzar el chat completo.

## Cómo correrlo

1. Verifica que Ollama está corriendo: `ollama list` debe mostrar tus modelos.
2. Abre `pydanticai_ollama_v2.ipynb` y ejecuta las celdas en orden.
3. Prueba primero la celda `probar_agente(...)` — si responde con un `SupportResponse`
   válido, el chat interactivo (`await run_chatbot()`) funcionará igual.

## Pendiente / próximos pasos posibles

- No se ha medido latencia real de `qwen2.5:7b-instruct-q4_K_M` en esta GPU para esta
  tarea — si el tiempo de respuesta es muy alto en la práctica, considerar `phi4-mini:3.8b`.
- El agente es de solo lectura sobre el CSV (no modifica tickets) — si más adelante se
  requiere que el agente escale un ticket de verdad (escribir a un sistema real), eso
  necesita una tool nueva y una revisión de seguridad (quién puede autorizar la escritura).
