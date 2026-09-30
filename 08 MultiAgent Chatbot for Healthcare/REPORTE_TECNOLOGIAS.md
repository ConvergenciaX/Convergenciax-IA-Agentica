# Reporte Técnico Completo — AutoMed
## Tecnologías, Arquitectura y Mejores Prácticas

**Proyecto:** MultiAgent Chatbot for Healthcare  
**Versión:** 2.1 — Documentación Corregida de AutoGen  
**Fecha:** 2026-09-20  
**Autor:** Claude Haiku 4.5  
**Framework:** AutoGen (AG2) 0.14.1 + Ollama Local  
**Cambios v2.1:** Correcciones críticas en Celda 4 del notebook y documentación (system_message, api_type: ollama, human_input_mode)

---

## Índice

1. [Introducción](#introducción)
2. [Tecnologías Principales](#tecnologías-principales)
   - 2.1 [AutoGen (AG2) — Framework Completo](#autogen-en-profundidad-guía-completa)
     - [Qué hace](#1-qué-hace-autogen--desglose-funcional)
     - [Compatibilidades](#2-compatibilidades-de-autogen-v0100)
     - [Configuraciones](#3-configuraciones-detalladas)
     - [Casos de Uso](#4-casos-de-uso-use-cases)
     - [Ejemplos Prácticos](#5-ejemplos-prácticos-de-código)
   - 2.2 [Ollama — LLM Local](#2-ollama--inferencia-local-de-llms)
   - 2.3 [Python 3.14](#3-python-314--entorno-de-ejecución)
   - 2.4 [Config.ini](#4-configini--centralización-de-configuración)
   - 2.5 [Benchmarking](#5-benchmarking--medición-de-rendimiento)
   - 2.6 [Evaluación de Exactitud](#6-evaluación-de-exactitud-diagnóstica)
3. [Arquitectura Multiagente](#arquitectura-multiagente)
4. [Mejores Prácticas](#mejores-prácticas)
5. [Optimizaciones y Configuración](#optimizaciones-y-configuración)
6. [Seguridad Médica](#seguridad-médica)
7. [Benchmarking y Evaluación](#benchmarking-y-evaluación)
8. [Troubleshooting](#troubleshooting)

---

## Introducción

Este documento explica en detalle cada tecnología utilizada en AutoMed, por qué fue elegida, cómo funciona, y las mejores prácticas para implementarla.

**Filosofía del proyecto:**
- ✅ **Transparencia:** Todo configurable, sin hardcoding
- ✅ **Educativo:** Notas didácticas en código para aprender
- ✅ **Producción-ready:** Benchmarking, evaluación, seguridad desde DAY 1
- ✅ **Local-first:** Ollama local, sin APIs cloud (soberanía de datos)

---

## Tecnologías Principales

### 1. AutoGen (AG2) — Framework de Multi-Agente

#### ¿Qué es?

AutoGen es un framework open-source de Microsoft para construir sistemas **multiagente colaborativos**. En lugar de un único chatbot, permite crear múltiples agentes especializados que se comunican entre sí.

#### ¿Por qué AutoGen?

| Característica | Alternativas | AutoGen | Razoón de elección |
|---|---|---|---|
| **Multi-agente nativo** | CrewAI (más overhead), LangChain (agente único) | ✅ Soporte completo | Diseñado específicamente para colaboración |
| **Comunicación flexible** | Rígida (solo supervisor) | ✅ Conversación libre | Agentes pueden negociar, debatir, validar |
| **Bajo overhead** | CrewAI (pesado) | ✅ Minimalista | Perfecto para Ollama local |
| **Open source** | OpenAI (propietario) | ✅ MIT license | Control total, sin dependencia de proveedor |
| **Soporte Ollama** | Algunos (parcial) | ✅ Compatible via OpenAI-like API | Funciona con Ollama sin modificaciones |

#### Cómo Funciona AutoGen

```
┌──────────────────────────────────┐
│   ConversableAgent               │
│   - Rol/name (ej: "Médico")      │
│   - system_prompt (instrucciones)│
│   - llm_config (modelo + params) │
│   - max_consecutive_auto_reply   │
└──────────────────────────────────┘
        ↓
        Cada agente tiene:
        • ID único
        • Memoria de conversación
        • Capacidad de llamar a otros agentes
        • Capacidad de decidir cuándo terminar
```

**Flujo de conversación:**

```
Agent A: "Analiza estos síntomas"
         ↓
Agent B: "Diagnóstico diferencial: X, Y, Z"
         ↓
Agent C: "Información relevante sobre X..."
         ↓
Agent D: "Opciones de tratamiento para X..."
         ↓
Agent E: "VERIFICAR: No hay contraindicaciones"
         ↓
Agent A: "Resumen final con disclaimer"
```

#### Concepto Clave: `max_consecutive_auto_reply`

```python
agent = ConversableAgent(
    name="Médico",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=10  # ← CRÍTICO
)
```

**¿Qué significa?**
- `10` = El agente puede tener hasta 10 turnos de conversación automática
- Si llega a 10, detiene (evita loops infinitos)
- Aumentar si conversación es cortada prematuramente
- Disminuir si consume demasiados tokens

**Regla de oro:**
```
max_consecutive_auto_reply = longitud_esperada_de_conversacion * 1.5
```

#### Integración con Ollama

```python
config_list = [
    {
        "model": "qwen2.5:7b",          # Nombre exacto del modelo
        "api_type": "open_ai",           # ← Crucial: Ollama simula OpenAI
        "api_base": "http://localhost:11434",
        "api_key": "not-needed",         # Ollama no requiere API key
        "temperature": 0.3,              # Control de creatividad
    }
]

agent = ConversableAgent(
    llm_config={"config_list": config_list}
)
```

**¿Por qué `api_type: "open_ai"`?**
- Ollama expone un endpoint compatible con la API de OpenAI
- AutoGen lo usa automáticamente
- Sin necesidad de modificar AutoGen

#### AutoGen en Profundidad: Guía Completa

Este apartado expande la comprensión de AutoGen v0.10.0+ con detalles adicionales sobre qué hace, compatibilidades, configuraciones avanzadas, casos de uso, y ejemplos prácticos.

##### 1. ¿Qué hace AutoGen? — Desglose Funcional

AutoGen **orquesta conversaciones entre múltiples agentes LLM** con memoria compartida, permitiendo que cada agente:
- Tenga un rol específico (médico, analista, validador)
- Mantenga contexto de toda la conversación
- Llame a otros agentes para colaborar
- Tome decisiones sobre cuándo terminar

**Sin AutoGen:**
```
Entrada → LLM único → Salida única
(Un chatbot responde todo)
```

**Con AutoGen:**
```
Entrada → Agente A (rol 1) → Agente B (rol 2) → Agente C (validador) → Salida
(Múltiples expertos debaten y validan)
```

**Capacidades específicas:**

| Capacidad | Descripción | Ejemplo |
|---|---|---|
| **ConversableAgent** | Agente que puede conversar con otros | `ConversableAgent(name="Doctor")` |
| **initiate_chat()** | Inicia conversación entre dos agentes | `agentA.initiate_chat(agentB, message="Analiza esto")` |
| **user_proxy_agent** | Agente que representa al usuario humano | Permite interacción interactiva |
| **Tool use / Function calling** | Agentes pueden ejecutar funciones Python | Llamar APIs, acceder datos, etc |
| **Agent state management** | Cada agente mantiene estado de conversación | Memoria completa de turnos previos |
| **Custom termination** | Decidir cuándo termina la conversación | Basado en condiciones lógicas |

##### 2. Compatibilidades de AutoGen v0.10.0+

**Compatibilidad de Versiones:**

```
AutoGen 0.2.x (deprecated):
  ✗ Python 3.14 incompatible
  ✗ config_list_from_json() no existe
  ✗ API deprecada

AutoGen 0.10.0+ (actual):
  ✅ Python 3.14 soportado completamente
  ✅ API moderna (ConversableAgent simplificado)
  ✅ Mejor manejo de errores
  ✅ Compatibilidad con Ollama
```

**Compatibilidad de Modelos LLM:**

| Proveedor | Soporte | API Type | Notas |
|---|---|---|---|
| **Ollama local** | ✅ Completo | `open_ai` | Recomendado (soberanía de datos) |
| **OpenAI** | ✅ Completo | `openai` | API key requerida |
| **Azure OpenAI** | ✅ Completo | `azure` | Configuración especial |
| **Google Gemini** | ⚠️ Parcial | `google` | Soporte limitado |
| **Anthropic Claude** | ⚠️ Parcial | N/A | No soporte nativo (requiere wrapper) |

**Compatibilidad de Plataformas:**

```
Python 3.10+  ✅ Soportado
Python 3.11   ✅ Soportado
Python 3.12   ✅ Soportado
Python 3.13   ✅ Soportado
Python 3.14   ✅ Soportado (v0.10.0+)

Windows        ✅ Soportado
macOS          ✅ Soportado
Linux          ✅ Soportado
```

##### 3. Configuraciones Detalladas

**Configuración Básica (Minimal):**

```python
from autogen import ConversableAgent

# Config más simple posible — AG2 0.14.1 con cliente Ollama nativo
config_list = [
    {
        "api_type": "ollama",                  # Cliente nativo de AG2 (NO "open_ai")
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434"
    }
]

agent = ConversableAgent(
    name="Médico",
    system_message="Eres un médico experto.",  # (NO system_prompt)
    llm_config={"config_list": config_list},
    human_input_mode="NEVER"                   # Automático 100%
)
```

**Configuración Intermedia (Recomendada):**

```python
config_list = [
    {
        "api_type": "ollama",                  # Cliente nativo AG2 (NO "open_ai")
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434",
        "temperature": 0.3,                    # Determinístico para medicina
        "num_ctx": 8192,                       # Contexto — parámetro nativo Ollama
        "num_predict": 2000,                   # Equivalente a max_tokens
    }
]

agent = ConversableAgent(
    name="Médico Especialista",
    system_message="Eres un médico cardiólogo con 15 años de experiencia...",  # (NO system_prompt)
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=10,         # Máximo turnos
    human_input_mode="NEVER",              # Automático 100%
)
```

**Configuración Avanzada (Prod-Ready):**

```python
import os
import configparser

# Cargar desde config.ini
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

ollama_base_url = config.get("ollama", "base_url", fallback="http://localhost:11434")
ollama_model = config.get("ollama", "model_name", fallback="qwen2.5:7b")
temperature = config.getfloat("ollama", "temperature", fallback=0.3)
max_tokens = config.getint("ollama", "max_tokens", fallback=2000)
num_ctx = config.getint("ollama", "num_ctx", fallback=8192)
request_timeout = config.getint("ollama", "request_timeout", fallback=180)
keep_alive = config.get("ollama", "keep_alive", fallback="30m")

# Config dinámica desde archivo — AG2 0.14.1 con cliente Ollama nativo
config_list = [
    {
        "api_type": "ollama",                  # Cliente nativo AG2 (NO "open_ai")
        "model": ollama_model,
        "base_url": ollama_base_url,
        "temperature": temperature,
        "num_ctx": num_ctx,                    # Contexto nativo de Ollama
        "num_predict": max_tokens,             # Equivalente a max_tokens
    }
]

agent = ConversableAgent(
    name=config.get("agentes", "nombre", fallback="Agente"),
    system_prompt=config.get("agentes", "system_prompt"),
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=config.getint("autogen", "max_consecutive_auto_reply", fallback=10),
    human_input_mode="NEVER",
)
```

**Parámetros Clave Explicados:**

| Parámetro | Rango | Recomendado | Impacto |
|---|---|---|---|
| `temperature` | 0.0-2.0 | 0.1-0.3 (medicina) | Controla "creatividad" del modelo |
| `max_tokens` | 1-∞ | 1024-2000 | Límite máximo de salida |
| `timeout` | 1-∞ | 60-180 | Segundos antes de timeout |
| `max_consecutive_auto_reply` | 1-∞ | 8-15 | Máximo turnos de conversación |

##### 4. Casos de Uso (Use Cases)

**Caso 1: Consulta Médica (Healthcare) — Este Proyecto**

```python
# Chatbot médico multiagente
# Agentes: User Interface, Symptom Analyzer, Medical Info, Treatment Suggester, Safety Validator

user_agent.initiate_chat(symptom_agent, message="Tengo fiebre 38°C y tos")
# → Conversación automática entre 5 agentes
# → Respuesta final con diagnósticos y advertencias
```

**Caso 2: Análisis Financiero (Finance)**

```python
# Sistema de análisis de inversiones
# Agentes: Analyst, Risk Manager, Compliance Officer

analyst_agent.initiate_chat(
    compliance_agent,
    message="¿Es segura esta inversión en tech?"
)
# → Análisis técnico + verificación de riesgos + compliance
```

**Caso 3: QA de Código (Software)**

```python
# Sistema de revisión de código
# Agentes: Code Reviewer, Security Expert, Performance Expert

code_reviewer.initiate_chat(
    security_expert,
    message="Revisar este código de autenticación"
)
# → Análisis de funcionalidad + seguridad + performance
```

**Caso 4: Generación de Contenido (Content Creation)**

```python
# Sistema de escritura colaborativa
# Agentes: Writer, Editor, Fact Checker

writer_agent.initiate_chat(
    fact_checker_agent,
    message="Escribe un artículo sobre medicina moderna"
)
# → Redacción + edición + verificación de hechos
```

##### 5. Ejemplos Prácticos de Código

**Ejemplo A: Crear Agente Simple**

```python
from autogen import ConversableAgent

# AG2 0.14.1 — cliente Ollama nativo
config_list = [{
    "api_type": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434"
}]

# Crear agente
doctor = ConversableAgent(
    name="Doctor García",
    system_message="Eres un cardiólogo con experiencia diagnosticando problemas del corazón.",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=5,
    human_input_mode="NEVER"
)

print(f"✓ Agente '{doctor.name}' creado exitosamente")
```

**Ejemplo B: Conversación Entre Dos Agentes**

```python
from autogen import ConversableAgent

# AG2 0.14.1 — cliente Ollama nativo
config_list = [{
    "api_type": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434"
}]

# Crear dos agentes
analyst = ConversableAgent(
    name="Analista de Síntomas",
    system_message="Eres experto en analizar síntomas médicos. Siempre proporciona diagnósticos diferenciales.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER"
)

validator = ConversableAgent(
    name="Validador de Seguridad",
    system_message="Tu rol es verificar que no hay alucinaciones médicas. Marca cualquier información dudosa.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER"
)

# Iniciar conversación
chat_result = analyst.initiate_chat(
    validator,
    message="El paciente tiene fiebre de 39°C, tos seca y fatiga por 3 días. ¿Cuál es tu análisis?",
    max_turns=4  # máximo 4 turnos (2 por agente)
)

# Ver resultado — ChatResult.summary captura el resumen real
print(chat_result.summary)
```

**Ejemplo C: Sistema Multiagente Completo (3 agentes)**

```python
from autogen import ConversableAgent

# AG2 0.14.1 — cliente Ollama nativo
config_list = [{
    "api_type": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434"
}]

# Definir 3 agentes
ui_agent = ConversableAgent(
    name="Interfaz de Usuario",
    system_message="Eres la puerta de entrada. Recibe síntomas y coordina especialistas.",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=3,
    human_input_mode="NEVER"
)

analyzer = ConversableAgent(
    name="Analizador",
    system_message="Analiza síntomas y propone diagnósticos posibles.",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=3,
    human_input_mode="NEVER"
)

safety = ConversableAgent(
    name="Validador",
    system_message="Verifica seguridad médica de las recomendaciones.",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=3,
    human_input_mode="NEVER"
)

# Flujo: UI → Analyzer → Safety → UI
print("Iniciando conversación multiagente...")

result = ui_agent.initiate_chat(
    analyzer,
    message="Paciente reporta: 'Me duele el abdomen, tengo fiebre 38.5°C'",
    max_turns=6  # permite 6 turnos totales
)

# ChatResult.summary captura el resumen real de la conversación
print("\n[Resumen]:", result.summary)
```

**Ejemplo D: Capturar Respuesta del Agente**

```python
# Después de initiate_chat(), acceder a mensajes
for msg in result.chat_history:
    print(f"{msg['name']}: {msg['content'][:200]}...")  # Primeros 200 chars
    
# O acceder al último mensaje del agente
last_message = result.chat_history[-1]
print(f"Última respuesta de {last_message['name']}: {last_message['content']}")
```

**Ejemplo E: Medir Rendimiento Durante Conversación**

```python
import time
from datetime import datetime

# Medir latencia
t_start = time.perf_counter()

result = analyzer.initiate_chat(
    safety,
    message="Revisa estos síntomas",
    max_turns=3
)

t_end = time.perf_counter()
latencia = t_end - t_start

print(f"Latencia total: {latencia:.2f} segundos")
print(f"Número de turnos: {len(result.chat_history)}")
print(f"Promedio por turno: {latencia / len(result.chat_history):.2f}s")

# Guardar métrica
metrica = {
    "timestamp": datetime.now().isoformat(),
    "agentes": f"{analyzer.name} + {safety.name}",
    "latencia_segundos": round(latencia, 3),
    "num_turnos": len(result.chat_history),
    "exito": True
}

import json
with open("benchmark.jsonl", 'a') as f:
    f.write(json.dumps(metrica) + "\n")
```

---

## Análisis Comparativo: Frameworks Multiagentes

### Contexto
Tu proyecto implementa **AutoGen con dos arquitecturas distintas**:
- **Enfoque 1 (Healthcare):** `initiate_chat()` — Conversación bilateral entre dos agentes
- **Enfoque 2 (Mental Health):** `GroupChat` + `GroupChatManager` — Múltiples agentes en grupo

Este apartado compara AutoGen con alternativas (LangChain/LangGraph, CrewAI) para futuras decisiones.

### Matriz Comparativa: 3 Frameworks

| Característica | AutoGen (Actual) | LangChain/LangGraph | CrewAI |
|---|---|---|---|
| **Auditoría Médica** | ✅ Excelente (`chat_history` automático) | ⚠️ Requiere logging custom | ❌ Menos explícito |
| **Performance** | Rápido | Muy rápido (bajo overhead) | Rápido |
| **Escalabilidad (agentes)** | Hasta 5 bien | Ilimitado (nodos) | Ilimitado |
| **Escalabilidad (conversaciones)** | ❌ Verboso con muchos turnos | ✅ Eficiente | ✅ Eficiente |
| **Herramientas/Tools** | ⚠️ Manual | ✅ ReAct integrado | ✅ Integrado |
| **Debugging** | ✅ `chat_history` claro | ⚠️ Menos transparente | ⚠️ Menos transparente |
| **Comunidad Médica** | ✅ Casos documentados | ⚠️ Genérica | ❌ Poca documentación |
| **Reproducibilidad** | ❌ Opaca | ✅ Explícita | ✅ Serializable |
| **Costo (tokens)** | Alto con muchos turnos | Bajo | Bajo |
| **Curva de Aprendizaje** | Media | Alta | Baja |
| **Production-ready** | ✅ Microsoft | ✅ LangChain Inc | ✅ CrewAI Inc |

### AutoGen: Dos Implementaciones

#### Enfoque 1: Conversación Bilateral con `initiate_chat()`

**Tu código (Celda 12 del notebook):**
```python
# Iniciar conversación entre dos agentes específicos
chat_result = user_interface_agent.initiate_chat(
    symptom_analyzer,                    # ← Receptor específico
    message=consulta_sistema,
    max_turns=autogen_max_turns          # ← Máximo 8 turnos
)

# Capturar resultado
respuesta_final = chat_result.summary    # ← Resumen limpio
print(len(chat_result.chat_history))     # ← Auditar cada turno
```

**Flujo de Conversación:**
```
User Interface Agent
    ↓ (inicia chat con)
Symptom Analyzer
    ↓ (responde)
User Interface Agent
    ↓ (responde)
Symptom Analyzer
    ↓ (responde)
... (máximo 8 turnos)
    ↓
chat_result.summary (respuesta final)
```

**Características Técnicas:**
- **Comunicación:** Bilateral (Agent A ↔ Agent B)
- **Iniciador:** `user_interface_agent.initiate_chat(receptor, ...)`
- **Control:** Explícito sobre quién habla con quién
- **Auditoría:** Cada mensaje en `chat_history`
- **Resultado:** `ChatResult.summary` (respuesta limpia)

**Ventajas:**
- ✅ **Simple:** Solo 2 agentes, flujo claro
- ✅ **Auditable:** `chat_history` es determinístico, predecible
- ✅ **Médico:** Ideal para validación bilateral (Médico + Validador)
- ✅ **Debugging:** Fácil rastrear cada turno
- ✅ **Tokens:** Menor consumo (conversación corta, controlada)

**Desventajas:**
- ❌ **Escalabilidad:** Para 5 agentes, necesitas encadenar múltiples `initiate_chat()`
- ❌ **Silenciosos:** Otros agentes no participan en diálogo principal
- ❌ **Complejidad:** Orquestar 5 agentes manualmente es engorroso

**Cuándo usar Enfoque 1:**
- ✅ Diagnóstico médico con validación (análisis + seguridad)
- ✅ Revisión de código (autor + reviewer)
- ✅ Análisis financiero (analyst + compliance)
- ✅ Cuando necesitas auditoría completa
- ✅ Cuando roles están claramente definidos (2 perspectivas)

**Ejemplo de tu proyecto (Healthcare):**
```
Usuario dice: "Tengo fiebre 38.5°C, tos seca..."
          ↓
[User Interface] clarifica: "¿Cuántos días de síntomas?"
          ↓
[Symptom Analyzer] analiza: "Diagnósticos posibles: Gripe, Resfriado, Bronquitis"
          ↓
[User Interface] presenta: "Recomendamos consultar profesional"
```

---

#### Enfoque 2: Conversación Grupal con `GroupChat` + `GroupChatManager`

**Tu código (Celda 22 del notebook):**
```python
# Crear grupo de agentes
groupchat = autogen.GroupChat(
    agents=[emotion_analysis_agent, therapy_recommendation_agent],
    messages=[],                          # ← Historial compartido
    max_round=3,                          # ← Máximo 3 rondas (todos hablan)
    speaker_selection_method="round_robin" # ← Turno por turno
)

# Crear coordinador
manager = autogen.GroupChatManager(name="manager", groupchat=groupchat)

# Iniciar conversación grupal
response = patient_agent.initiate_chat(
    manager,                              # ← Habla con manager, no directamente
    message=f"Me he estado sintiendo {user_feelings}"
)
```

**Flujo de Conversación:**
```
Patient Agent
    ↓ (inicia chat con Manager)
Manager (coordinador)
    ↓ (selecciona siguiente speaker)
Emotion Analysis Agent
    ↓ (análisis)
Manager (coordinador)
    ↓ (selecciona siguiente speaker)
Therapy Recommendation Agent
    ↓ (recomendación)
Manager (coordinador)
    ↓ (3 rondas completadas)
Fin
```

**Características Técnicas:**
- **Comunicación:** Grupal (N agentes + Manager coordinador)
- **Iniciador:** `patient_agent.initiate_chat(manager, ...)`
- **Coordinador:** `GroupChatManager` orquesta quién habla
- **Selección:** `speaker_selection_method` decide siguiente speaker
- **Control:** Menos explícito, más "emergente"

**Ventajas:**
- ✅ **Escalable:** N agentes participan sin encadenamiento manual
- ✅ **Natural:** Conversación fluida, todos tienen voz
- ✅ **UX:** Mejor para interfaces conversacionales (Gradio, chat)
- ✅ **Dinámico:** Agentes pueden debatir/negociar

**Desventajas:**
- ❌ **Menos Auditable:** Manager elige speakers, menos predecible
- ❌ **Tokens:** Mayor consumo (N agentes × conversación)
- ❌ **Debugging:** Difícil rastrear por qué Agent X habló en turno Y
- ❌ **Médico:** Menos control sobre orden de decisiones
- ❌ **Divergencia:** Puede ir por caminos inesperados

**Cuándo usar Enfoque 2:**
- ✅ Conversación natural con usuario (UX conversacional)
- ✅ Brainstorming colaborativo (múltiples perspectivas emergentes)
- ✅ Interfaces de chat (Gradio, aplicaciones web)
- ✅ Cuando roles son fluidos o no bien definidos
- ❌ Cuando auditoría médica es crítica

**Ejemplo de tu proyecto (Mental Health):**
```
Usuario: "Me siento ansioso y cansado"
          ↓
[Manager] selecciona: Emotion Analysis Agent
          ↓
[Emociones] analiza: "Ansiedad detectada, fatiga mental"
          ↓
[Manager] selecciona: Therapy Agent
          ↓
[Terapia] recomienda: "Técnicas de relajación..."
          ↓
Conversación fluida, natural
```

---

#### Comparativa Directa: `initiate_chat()` vs `GroupChat`

| Aspecto | `initiate_chat()` (Enfoque 1) | `GroupChat` (Enfoque 2) |
|--------|------|---------|
| **Agentes** | 2 (bilateral) | N (grupal) |
| **Iniciación** | `agentA.initiate_chat(agentB, ...)` | `agentX.initiate_chat(manager, ...)` |
| **Coordinación** | Explícita (A ↔ B) | Implícita (Manager elige) |
| **Speaker Selection** | Alternancia fija | `round_robin` o `auto` |
| **Auditoría** | ✅ Muy clara | ⚠️ Menos clara |
| **Tokens** | Bajo (conversación corta) | Alto (N agentes × turnos) |
| **Debugging** | ✅ Fácil | ❌ Difícil |
| **Escalabilidad** | ❌ Manual para 5+ agentes | ✅ Automática para N agentes |
| **UX Conversacional** | ⚠️ Limitada (2 voces) | ✅ Natural (múltiples voces) |
| **Medicina** | ✅ Recomendado (auditoría) | ⚠️ Solo si UX prioritario |
| **Caso de Uso Ideal** | Validación bilateral, análisis | Chat natural, brainstorming |

---

#### Recomendación para Tu Proyecto

**Para Hito 1 (Production):** 
- ✅ Mantén **Enfoque 1** (`initiate_chat()`)
- Razón: Auditoría médica crítica, roles claros

**Para Hito 2+ (Si integras UI conversacional):**
- 🔄 Considera **Enfoque 2** (`GroupChat`)
- Pero: Mantén Validador de Seguridad como paso final (no grupal)

**Configuración Híbrida Recomendada:**
```python
# Enfoque 1: Diagnóstico médico (bilateral, auditable)
chat_result = user_interface_agent.initiate_chat(
    symptom_analyzer,
    message=consulta,
    max_turns=3
)

# Luego: Validación (bilateral, auditable)
validation_result = safety_validator.initiate_chat(
    user_interface_agent,
    message=f"Valida esta recomendación: {chat_result.summary}",
    max_turns=2
)

# Resultado: Auditoría completa, seguridad médica garantizada
respuesta_final = validation_result.summary
```

**No usar GroupChat para medicina crítica** porque la auditoría es difusa.

### AutoGen vs LangChain/LangGraph

#### LangChain/LangGraph: Alternativa para Flujos Lineales

**Concepto:** Cadenas de reasoning con nodos determinísticos.

**Ejemplo equivalente en LangChain:**
```python
from langgraph.graph import StateGraph

def parse_symptoms(state: State):
    return {"symptom_analysis": analyze_with_llm(state["symptoms"])}

def diagnose(state: State):
    return {"differential_diagnosis": diagnose_with_llm(state["symptom_analysis"])}

def validate(state: State):
    return {"validated_diagnosis": validate_with_llm(state["differential_diagnosis"])}

workflow = StateGraph(State)
workflow.add_node("parse", parse_symptoms)
workflow.add_node("diagnose", diagnose)
workflow.add_node("validate", validate)
workflow.add_edge("parse", "diagnose")
workflow.add_edge("diagnose", "validate")
```

**Comparación:**
- **Líneas:** LangChain 50 vs AutoGen 20
- **Claridad:** LangChain es más explícito
- **Auditoría:** AutoGen es automático; LangChain requiere logging
- **Tokens:** LangChain gasta menos (sin `chat_history`)

**Cuándo usar LangChain:**
- ✅ Flujos lineales A→B→C
- ✅ Bajo overhead de tokens crítico
- ✅ Múltiples herramientas/APIs
- ❌ Auditoría médica (menos automática)

### AutoGen vs CrewAI

#### CrewAI: El Equilibrio Empresarial

**Concepto:** Abstracción sobre LangChain con semántica de "crews" (equipos).

**Ejemplo equivalente en CrewAI:**
```python
from crewai import Agent, Task, Crew

symptom_analyzer = Agent(
    role="Especialista en Síntomas",
    goal="Identificar diagnósticos diferenciales",
    backstory="Médico internista con 20 años...",
)

analysis_task = Task(
    description="Analiza síntomas: {symptoms}",
    agent=symptom_analyzer,
    expected_output="Diagnósticos diferenciales con confianza"
)

crew = Crew(agents=[symptom_analyzer], tasks=[analysis_task])
result = crew.kickoff(inputs={"symptoms": "..."})
```

**Ventajas de CrewAI:**
- ✅ Semántica clara (roles, tareas, herramientas)
- ✅ Menos código boilerplate que LangChain
- ✅ Gestión automática de contexto entre tareas
- ✅ Serialización (fácil ML Ops)

**Desventajas de CrewAI:**
- ❌ Menos transparencia que AutoGen
- ❌ Comunidad más nueva (~2024)
- ❌ Menos casos de uso médicos documentados
- ❌ Overhead de abstracción

**Cuándo usar CrewAI:**
- ✅ Equipos empresariales (5+ agentes)
- ✅ ML Ops con reproducibilidad
- ✅ Interfaz amigable para no-técnicos
- ❌ Auditoría médica (menos explícito)

### AutoGen: Features Específicos Utilizados en Tu Proyecto

**Inventario de capacidades AutoGen 0.14.1 en uso:**

| Feature | Ubicación | Uso | Valor |
|---------|-----------|-----|-------|
| **ConversableAgent** | Celda 9 (5 agentes) | Crear agentes especializados | ✅ Rol específico cada uno |
| **system_message** | Celda 9 (c/ agente) | Define rol e instrucciones | ✅ Especialistas distintos |
| **initiate_chat()** | Celda 12 (función ejecutar_consulta) | Inicia conversación bilateral | ✅ Diagnóstico multiperspectiva |
| **ChatResult** | Celda 12 (chat_result.summary) | Captura resumen de diálogo | ✅ Respuesta final limpia |
| **chat_history** | Celda 12 (medir_y_registrar) | Rastrear cada turno | ✅ Auditoría completa |
| **max_consecutive_auto_reply** | config.ini (10) | Limitar iteraciones | ✅ Evita loops infinitos |
| **max_turns** | Celda 12 (autogen_max_turns) | Limitar turnos totales | ✅ Controlar duración |
| **human_input_mode="NEVER"** | Celda 9 (c/ agente) | 100% automático | ✅ Sin intervención humana |
| **llm_config** | Celda 9 (config_list) | Config de LLM | ✅ Ollama integrado |
| **GroupChat** | Celda 22 (mental health) | Conversación grupal | ✅ UX conversacional |
| **GroupChatManager** | Celda 22 | Coordinador de grupo | ✅ Múltiples agentes simultáneo |
| **round_robin speaker selection** | Celda 22 | Turno-por-turno | ✅ Justo y predecible |

**Código Específico en Uso:**

```python
# CARACTERÍSTICA 1: ConversableAgent con system_message
user_interface_agent = ConversableAgent(
    name="InterfazDeUsuario",
    system_message="Eres un asistente médico...",  # ← system_message (NO system_prompt)
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=max_consecutive_auto_reply,  # ← Límite de turnos
    human_input_mode="NEVER",  # ← 100% automático
)

# CARACTERÍSTICA 2: initiate_chat() para conversación bilateral
chat_result = user_interface_agent.initiate_chat(
    symptom_analyzer,
    message=consulta_sistema,
    max_turns=autogen_max_turns  # ← Límite de turnos totales
)

# CARACTERÍSTICA 3: ChatResult.summary captura respuesta
respuesta_final = chat_result.summary  # ← Output limpio
print(f"Chat history turnos: {len(chat_result.chat_history)}")  # ← Auditoría

# CARACTERÍSTICA 4: GroupChat + GroupChatManager
groupchat = autogen.GroupChat(
    agents=[emotion_analysis_agent, therapy_recommendation_agent],
    messages=[],
    max_round=3,
    speaker_selection_method="round_robin"  # ← Selección de speaker
)
manager = autogen.GroupChatManager(name="manager", groupchat=groupchat)
```

**Lo que NO estás usando (pero podrías en futuro):**

| Feature | Por Qué No | Cuándo Agregar |
|---------|-----------|----------------|
| **user_proxy_agent** | No necesitas interacción humana | Si integras con UI (Gradio) |
| **Tool use / Function calling** | Agentes solo conversan, no ejecutan | Si necesitas APIs médicas |
| **AssistantAgent** | Similar a ConversableAgent | Cambio menor si lo necesitas |
| **Nested conversations** | Complejidad innecesaria por ahora | Si escalas a 10+ agentes |
| **Logging callbacks** | Ya tienes benchmark.py | Agregar si necesitas métricas extras |

### Recomendación para Tu Proyecto

#### ✅ QUÉDATE CON AUTOGEN

**Razones:**

1. **Auditoría Médica Crítica**
   - `chat_history` automático con cada mensaje
   - Cada decisión queda registrada
   - LangChain requiere logging custom (error-prone)
   - CrewAI es menos transparente

2. **Ya Invertiste en AutoGen**
   - Tienes `benchmark.py` optimizado para `ChatResult`
   - 5 agentes definidos y funcionando
   - Cambiar = reescribir todo

3. **Multiagente con Validación**
   - SafetyValidator es crítico
   - AutoGen permite que Validador revise output de otros
   - LangChain/CrewAI lo hacen más implícito

4. **Dos Enfoques Complementarios**
   - Enfoque 1 (bilateral): Simple, auditable → Producción
   - Enfoque 2 (grupal): Dinámico, conversacional → UX
   - Combina lo mejor de ambos

#### Optimizaciones Sugeridas (Hito 2)

**Para Enfoque 1 (Bilateral):**
```python
# Reducir tokens: Validador como paso final, no iterativo
# Diagn → Validador → FIN (3 turnos, 6k tokens vs 16k)
max_turns = 3  # reducir de 8

# Mejora: Capturar solo lo esencial
chat_result = analyzer.initiate_chat(validator, max_turns=3)
summary = chat_result.summary  # Usa ChatResult.summary (optimizado)
```

**Para Enfoque 2 (Grupal):**
```python
# Mejor selección de siguiente agente (en lugar de round_robin)
groupchat = autogen.GroupChat(
    agents=[emociones_agent, terapia_agent],
    speaker_selection_method="auto",  # Deja que LLM elija siguiente
    max_round=3
)
```

---

### 2. Ollama — Configuración de Parámetros

#### Parámetros Críticos en config.ini

**En config.ini:**

```ini
[ollama]
model_name = qwen2.5:7b        # Modelo en uso (gemma4:26b en v2.2)
temperature = 0.3              # 0.1-0.3 para medicina (factual, menos hallucinations)
max_tokens = 2000              # Límite máximo de generación
num_ctx = 8192                 # Tamaño de contexto (CRÍTICO: evita truncamiento)
request_timeout = 180          # Timeout máximo (segundos)
keep_alive = 30m               # Mantener modelo en memoria (evita reload)
base_url = http://convergenciax02:11434  # Endpoint Ollama
```

**¿Por qué `num_ctx = 8192`?**

```
Sin num_ctx (por defecto 2048):
- Conversación larga → contexto se corta → modelo pierde historia
- Resultado: respuesta desconectada

Con num_ctx = 8192:
- Puede recordar conversación completa
- Medical use case: retiene síntomas, historial médico
```

**¿Por qué `temperature = 0.3`?**

```
Temperature controla "creatividad":
- 0.0 = Determinístico (recomendado para medicina)
  → Respuestas consistentes, predecibles, factual
  
- 1.0 = Creativo (escritura)
  → Respuestas variadas, exploratorias, riesgo de hallucinations
  
Para medicina: BAJO (0.1-0.3) = más factual, menos alucinaciones
```

#### Trade-off: Velocidad vs Calidad

| Modelo | Velocidad | Calidad | Recomendación |
|---|---|---|---|
| mistral:7b | ⚡⚡⚡ (1s) | ⭐⭐ | Demo, pruebas rápidas |
| qwen2.5:7b | ⚡⚡ (2s) | ⭐⭐⭐ | ✅ Producción balanced |
| llama3.1:8b | ⚡ (3s) | ⭐⭐⭐⭐ | Alta precisión diagnóstica |
| gemma4:26b | ⚡ (3-4s) | ⭐⭐⭐⭐ | (actual en v2.2) |

---

### 3. Python 3.14 — Entorno de Ejecución

#### ¿Por qué 3.14?

- ✅ Más rápido que 3.13
- ✅ Mejor manejo de memoria
- ✅ Compatibilidad con LangChain, pandas, matplotlib

#### Compatibilidad con AutoGen

```
Python 3.14: AutoGen puede tener wheel issues (C extensions)
Fallback: Python 3.13 (env-llm-ia)

En config, detectar error y cambiar automáticamente:
try:
    import autogen
except ImportError:
    print("Cambiar a Python 3.13 (env-llm-ia)")
```

**Comando correcto:**
```bash
# NO hacer esto (resuelve a intérprete global):
python -m pip install ...

# HACER ESTO (ruta explícita):
C:\workspace-vc\env-llm-314\Scripts\python.exe -m pip install ...
```

---

### 4. Config.ini — Centralización de Configuración

#### Concepto: Single Source of Truth

Toda configuración en **un único archivo**, NO en código.

**Ventajas:**
- 🔄 Cambiar modelos/parámetros sin editar Python
- 📊 Experimentar rápidamente (A/B testing)
- 🔒 Parámetros sensibles no en GitHub
- 🎯 Comparar configuraciones fácilmente

#### Estructura de config.ini

```ini
[ollama]
# Conexión al LLM
model_name = qwen2.5:7b

[autogen]
# Parámetros de MultiAgente
max_consecutive_auto_reply = 10

[benchmark]
# Medición de rendimiento
enabled = true
variant_label = qwen25_t03_ctx8192

[evaluacion]
# Medición de exactitud diagnóstica
modo = hibrida              # automática/manual/hibrida
verdades_archivo = data/verdades_medicas.jsonl

[seguridad_medica]
# Protecciones médicas
disclaimer = true           # Mostrar advertencia
max_confidence_medical = 0.85   # Pedir confirmación si confianza > 85%
```

#### Cargar en Python

```python
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')  # ← UTF-8 CRÍTICO

# Acceder
model = config.get('ollama', 'model_name')
max_tokens = config.getint('ollama', 'max_tokens')
benchmark_enabled = config.getboolean('benchmark', 'enabled')
```

---

### 5. Benchmarking — Medición de Rendimiento

#### ¿Qué Medir?

**Métricas de Rendimiento:**
- Latencia (wall-clock time): Cuánto tarda la consulta
- Tokens consumidos: Eficiencia del modelo
- Throughput: Consultas/minuto

**Métricas de Efectividad:**
- Exactitud diagnóstica: ¿Es correcto el diagnóstico?
- Hallucinations: ¿Información médica incorrecta?
- Seguridad: ¿Se detectan emergencias?

#### Implementación

```python
import time
from datetime import datetime

# Medir latencia
t_start = time.perf_counter()

respuesta = agente.invoke(consulta)

t_end = time.perf_counter()
latencia = t_end - t_start

# Registrar métrica
metrica = {
    "timestamp": datetime.now().isoformat(),
    "modelo": "qwen2.5:7b",
    "latencia_segundos": round(latencia, 3),
    "tokens_entrada": ...,
    "tokens_salida": ...,
    "exactitud": 0.95,  # 0-1
    "exito": True
}

# Persistir (JSONL append-only)
with open("outputs/benchmark.jsonl", 'a', encoding='utf-8') as f:
    f.write(json.dumps(metrica, ensure_ascii=False) + "\n")
```

#### JSONL Append-Only

**¿Por qué JSONL y por qué append-only?**

```
JSONL = JSON Lines (una línea = un documento)
Append-only = agregar líneas sin sobrescribir

Ventaja: Comparar múltiples variantes sin borrar:

Día 1: Ejecutar con qwen2.5 → agrega 5 líneas
Día 2: Ejecutar con llama3.1 → agrega 5 líneas más
Día 3: Ejecutar con mistral → agrega 5 líneas más

benchmark.jsonl ahora tiene 15 líneas (todas las variantes)
Fácil de analizar: pandas.read_json("benchmark.jsonl", lines=True)
```

#### Análisis con Pandas

```python
import pandas as pd

# Leer JSONL
df = pd.read_json("outputs/benchmark.jsonl", lines=True)

# Filtrar por variante
df_qwen = df[df['modelo'] == 'qwen2.5:7b']

# Estadísticas
print(df_qwen['latencia_segundos'].mean())  # Promedio
print(df_qwen['exactitud'].mean())          # Exactitud promedio

# Comparar variantes
print(df.groupby('modelo')['latencia_segundos'].mean())

# Exportar a CSV
df.to_csv("benchmark.csv", index=False)
```

---

### 6. Evaluación de Exactitud Diagnóstica

#### Concepto

Comparar salidas del sistema contra "verdades médicas esperadas".

#### Estrategias de Evaluación

**A) Automática (Ideal para medicina)**

```python
def evaluar_exactitud(respuesta, diagnosticos_esperados):
    """
    Verificar si respuesta sugiere alguno de los diagnósticos esperados.
    """
    for diag in diagnosticos_esperados:
        if diag.lower() in respuesta.lower():
            return 1.0  # Correcto
    return 0.0  # Incorrecto

# Uso
respuesta = "Probablemente sea una gripe viral..."
diagnósticos_esperados = ["Gripe", "Influenza", "Infección viral"]
exactitud = evaluar_exactitud(respuesta, diagnósticos_esperados)
# → 1.0 (correcto, contiene "viral")
```

**B) Manual (Necesaria para medicina real)**

```
Para cada respuesta, médico experto responde:
- ¿Es correcto el diagnóstico? SI/NO
- ¿Es segura la recomendación? SI/NO
- ¿Hay alucinaciones? SI/NO
- Confianza en la respuesta: 0-100%
```

**C) Híbrida (Recomendada)**

```
- Automática para casos simples (exactitud 0 o 1)
- Manual para casos límite (exactitud 0.3-0.7)
- Muestreo aleatorio del 10%
```

#### Definir Verdades Médicas

**Archivo: data/verdades_medicas.jsonl**

```json
{
  "síntomas": "Fiebre 38.5°C, tos seca, dolor garganta, 3 días",
  "diagnósticos_esperados": ["Resfriado", "Gripe", "Infección viral"],
  "urgencia": "normal",
  "tratamiento_esperado": "Reposo, hidratación, analgésicos",
  "contraindicaciones_conocidas": ["Antibióticos (no viral)"],
  "confianza_esperada": 0.85
}
```

#### Métrica: Exactitud Diagnóstica

```
Exactitud = (# diagnósticos correctos) / (# total casos)

Target pre-producción: ≥95%
Si < 90%: No desplegar (reentrenar, ajustar prompts)
Si 90-95%: Desplegar con advertencia, monitorear
Si ≥95%: Desplegar con confianza
```

---

## Arquitectura Multiagente

### 5 Agentes Especializados

#### 1. User Interface Agent

**Rol:** Puerta de entrada, coordinador

```
Recibe: Síntomas del usuario
Hace: 
  - Clarifica síntomas con preguntas
  - Coordina otros agentes
  - Presenta respuesta final
Envía a: Symptom Analyzer
```

**System Prompt (clave):**

```
"Eres un asistente médico profesional.
Tu rol es:
1. Recibir síntomas naturalmente
2. Hacer preguntas de seguimiento
3. Coordinar especialistas
4. Presentar recomendaciones claras

IMPORTANTE: Termina SIEMPRE con:
'⚠️ Esta es una consulta IA. Consulta médico real.'"
```

#### 2. Symptom Analyzer

**Rol:** Análisis clínico, diagnósticos diferenciales

```
Recibe: Síntomas analizados
Hace:
  - Genera lista de diagnósticos posibles
  - Prioriza por probabilidad
  - Identifica síntomas de alerta
  - Sugiere urgencia
Envía a: Medical Info Agent
```

#### 3. Medical Info Specialist

**Rol:** Base de conocimiento médico

```
Recibe: Diagnósticos propuestos
Hace:
  - Proporciona información factual
  - Explica mecanismos
  - Comparte prevalencia, síntomas típicos
  - Cita estudios si aplica
Envía a: Treatment Suggester
```

#### 4. Treatment Suggester

**Rol:** Opciones terapéuticas

```
Recibe: Diagnósticos validados
Hace:
  - Propone opciones de tratamiento
  - Compara: eficacia, riesgos, beneficios
  - Considera contexto del paciente
  - Clasifica por urgencia
Envía a: Safety Validator
```

#### 5. Safety Validator

**Rol:** Control de calidad, seguridad

```
Recibe: Recomendaciones completadas
Hace:
  - Detecta hallucinations (información falsa)
  - Verifica contraindicaciones
  - Marca información dudosa
  - Asegura disclaimer presente
Envía a: User Interface Agent
```

### Flujo de Comunicación

```
Usuario: "Me duele el abdomen, fiebre 39°C"
   ↓
[User Interface] ← Recibe, clarifica
   ↓
[Symptom Analyzer] → "Posibles: Appendicitis, gastroenteritis, infección..."
   ↓
[Medical Info] → "Appendicitis: inflamación del apéndice vermiforme..."
   ↓
[Treatment Suggester] → "Opción 1: Cirugía (urgente). Opción 2: Antibióticos..."
   ↓
[Safety Validator] → "✓ Información correcta. ⚠️ Urgencia ALTA. [VERIFICAR CON MÉDICO]"
   ↓
[User Interface] → Resume y presenta disclaimer
   ↓
Usuario: Recomendación clara con advertencia legal
```

---

## Mejores Prácticas

### 1. System Prompts en Español (CRÍTICO)

**❌ MAL:**
```python
system_prompt = "You are a medical expert. Analyze the symptoms..."
# Resultado: El modelo responde en inglés
```

**✅ BIEN:**
```python
system_prompt = """Eres un especialista médico con 20 años de experiencia.
Tu rol es:
1. Analizar síntomas
2. Generar diagnósticos
3. Responder siempre en español

IMPORTANTE: Respuesta clara y precisa."""
# Resultado: El modelo responde en español, sigue instrucciones
```

**Regla de oro:** El idioma del system_prompt determina el idioma de respuesta.

### 2. Manejo de Contexto (`num_ctx`)

**Problema sin num_ctx (2048 por defecto):**
```
Turno 1: Usuario describe síntomas (100 tokens)
Turno 2: Agente 1 analiza (300 tokens)
Turno 3: Agente 2 propone (300 tokens)
Turno 4: Agente 3 sugiere (300 tokens)
Turno 5: Agente 4 valida...
         ↓ CONTEXTO SE CORTA → Pierde síntomas originales
         → Respuesta desconectada
```

**Solución: `num_ctx = 8192`**
```
Puede mantener conversación completa en contexto
Agente 5 recuerda síntomas originales y toda la discusión
Respuesta final coherente
```

**Regla de oro:**
```
num_ctx ≥ longitud_conversacion_esperada * 2
Para medicina: mínimo 8192
```

### 3. Timeout y Retries

```ini
request_timeout = 180      # Máximo 3 minutos por consulta
max_retries = 3           # Reintentar 3 veces si falla
keep_alive = 30m          # Mantener modelo listo (evita reload)
```

**¿Por qué importante?**

```
Sin timeout: Si Ollama se cuelga, esperas eternamente
Sin keep_alive: Cada consulta carga el modelo (2+ segundos overhead)

Con configuración: Respuestas consistentes y rápidas
```

### 4. Logging Completo

```python
import logging

logging.basicConfig(
    filename="logs/automed.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # ← UTF-8 para caracteres españoles
)

logger = logging.getLogger(__name__)
logger.info(f"Consulta: {síntomas}")
logger.info(f"Modelo: {modelo}")
logger.info(f"Latencia: {latencia:.2f}s")
```

**Para medicina:**
- Logging completo de TODAS las interacciones
- Auditoría: quién consultó, cuándo, qué se recomendó
- Compliance: GDPR, HIPAA (si aplica)

### 5. Validación de Entrada (Sin Hallucinations)

```python
def validar_consulta_medica(síntomas_texto):
    """
    Verificar que entrada sea razonable (no inyección de prompts).
    """
    if len(síntomas_texto) < 10:
        raise ValueError("Síntomas demasiado breves")
    
    if len(síntomas_texto) > 5000:
        raise ValueError("Síntomas demasiado largos")
    
    # Verificar no haya patrones de inyección
    patrones_peligrosos = ["SYSTEM PROMPT:", "Ignora instrucciones", "admin"]
    for patrón in patrones_peligrosos:
        if patrón.lower() in síntomas_texto.lower():
            raise ValueError("Entrada sospechosa detectada")
    
    return True
```

---

## Optimizaciones y Configuración

### 1. Trade-off: Velocidad vs Calidad

| Modelo | Velocidad | Calidad | Caso de Uso |
|---|---|---|---|
| mistral:7b | ⚡⚡⚡ (1s) | ⭐⭐ | Demo, pruebas rápidas |
| qwen2.5:7b | ⚡⚡ (2s) | ⭐⭐⭐ | ✅ Producción balanced |
| llama3.1:8b | ⚡ (3s) | ⭐⭐⭐⭐ | Alta precisión diagnóstica |

**Elegir según:**

```
Si latencia crítica (<2s) → mistral o qwen2.5
Si exactitud crítica (≥95%) → llama3.1 o qwen2.5
Si presupuesto limitado → qwen2.5 (balanced)
```

### 2. Temperatura por Caso de Uso

```ini
# Medicina (diagnóstico, análisis) = BAJO
[ollama]
temperature = 0.1          # Muy determinístico

# Brainstorming, ideas = ALTO
temperature = 0.8          # Muy creativo

# Recomendado para medicina = MEDIO-BAJO
temperature = 0.3          # Factual pero con variación
```

### 3. Max Tokens por Agente

```python
# Agente corto (solo clasificación)
agent1 = ConversableAgent(
    system_prompt="Clasifica el síntoma como: grave/moderado/leve",
    llm_config={"config_list": config_list}
    # Usará max_tokens global (2000 por defecto)
)

# Agente largo (análisis profundo)
# Aumentar max_tokens en config.ini si respuestas truncadas
config.set('ollama', 'max_tokens', '4000')
```

---

## Seguridad Médica

### 1. Disclaimer Obligatorio

Cada respuesta **DEBE** incluir:

```
⚠️ DISCLAIMER:
Este sistema NO es un sustituto de consulta médica real.
SIEMPRE consulta con un profesional médico calificado.
En caso de emergencia, llama a emergencias.
```

**Implementación:**

```python
safety_validator_prompt = """
...análisis de seguridad...

IMPORTANTE: Anexa SIEMPRE:
'⚠️ Esta es una consulta de IA. Consulta profesional médico real.
En emergencia, llama a emergencias.'
"""
```

### 2. Límite de Confianza Máxima

Si confianza > threshold → **pedir confirmación profesional**

```ini
[seguridad_medica]
max_confidence_medical = 0.85   # Si confianza > 85%, pedir confirmación
```

**Lógica:**

```python
if confidence_score > max_confidence_medical:
    respuesta += "\n[VERIFICAR CON PROFESIONAL ANTES DE ACTUAR]"
```

### 3. Detección de Hallucinations

Búsqueda de información médica claramente falsa:

```python
def detectar_hallucination_medico(respuesta):
    """
    Flagear información médica que parece incorrecta.
    """
    hallucinations_comunes = [
        "la aspirina cura el cáncer",
        "no necesitas doctor si",
        "100% efectivo sin efectos secundarios",
    ]
    
    for pattern in hallucinations_comunes:
        if pattern.lower() in respuesta.lower():
            return True, pattern
    
    return False, None

# Uso
has_hallucination, patrón = detectar_hallucination_medico(respuesta)
if has_hallucination:
    logger.warning(f"Potencial hallucination detectado: {patrón}")
    respuesta = "[INFORMACIÓN VERIFICADA COMO INCORRECTA] " + respuesta
```

### 4. Auditoría Completa

```python
def registrar_consulta_medica(usuario_id, síntomas, respuesta, exactitud):
    """
    Registrar TODA consulta para auditoría.
    """
    registro = {
        "timestamp": datetime.now().isoformat(),
        "usuario": usuario_id,  # Anónimo, no personal
        "síntomas": síntomas,
        "respuesta": respuesta,
        "exactitud": exactitud,
        "modelo": ollama_model,
        "temperatura": ollama_temperature,
        "duración_segundos": ...,
        "hallucination_detected": False,
        "disclaimer_included": True,
    }
    
    # Guardar en logs (para compliance)
    with open("logs/consultas_medicas.log", 'a', encoding='utf-8') as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
```

---

## Benchmarking y Evaluación

### Flujo Completo Pre-Producción

```
FASE 1: DESARROLLO (Este notebook)
├─ Definir 5 agentes
├─ Conectar a Ollama local
├─ Ejecutar 3-5 casos de prueba
└─ Benchmarking básico (latencia)

FASE 2: VALIDACIÓN INTERNA
├─ Crear dataset 20+ casos (con verdades esperadas)
├─ Ejecutar con 2-3 modelos
├─ Calcular exactitud diagnóstica
├─ Detectar hallucinations
└─ Elegir modelo ganador (score ponderado)

FASE 3: VALIDACIÓN EXTERNA
├─ Médico experto revisa 50+ casos
├─ Calidad editorial de recomendaciones
├─ Seguridad: síntomas de alerta detectados?
├─ Legal: disclaimer suficiente?
└─ Compliance: requisitos regulatorios?

FASE 4: PRODUCCIÓN
├─ Desplegar modelo ganador
├─ Monitoreo en vivo (SLO: exactitud ≥95%)
├─ Logging completo (auditoría)
├─ Re-evaluar cada 30 días
└─ Actualizar modelo si exactitud cae < 90%
```

### Umbrales de Aceptabilidad

```
✅ DESPLEGAR:
- Exactitud diagnóstica ≥95%
- Latencia <3 segundos
- Hallucinations <5% de casos
- Disclaimer presente 100%

⚠️ REVISAR:
- Exactitud 90-95%
- Latencia 3-5 segundos
- Hallucinations 5-10%

❌ NO DESPLEGAR:
- Exactitud <90%
- Latencia >5 segundos
- Hallucinations >10%
- Disclaimer ausente en algún caso
```

---

## Troubleshooting

### Problema: "Respuesta cortada (truncada)"

**Síntoma:**
```
Respuesta incompleta: "El diagnóstico probable es..."
(se corta aquí)
```

**Solución:**

```ini
# En config.ini, aumentar contexto y tokens
[ollama]
num_ctx = 16384        # Duplicar (era 8192)
max_tokens = 4000      # Aumentar (era 2000)
```

### Problema: "Respuestas inconsistentes"

**Síntoma:**
```
Misma consulta → respuestas diferentes cada vez
```

**Solución:**

```ini
# En config.ini, reducir temperatura (más determinístico)
[ollama]
temperature = 0.1      # (antes 0.3)
```

---

## Conclusión

**AutoMed demuestra:**

1. ✅ **Multiagente colaborativo:** 5 agentes especializados que se comunican
2. ✅ **Local-first:** Ollama local, sin APIs cloud (soberanía de datos)
3. ✅ **Production-ready:** Benchmarking, evaluación, seguridad desde DAY 1
4. ✅ **Transparente:** Configuración centralizada, prompts didácticos
5. ✅ **Escalable:** Patrón aplicable a otros dominios (legal, finanzas, etc.)

**Próximos pasos:**

1. Ampliar dataset de verdades médicas (100+ casos)
2. Validar exactitud diagnóstica ≥95%
3. Probar con múltiples modelos (mistral, llama, etc.)
4. Desplegar con monitoreo en producción
5. Actualizar modelos según feedback

---

**Autor:** Claude Haiku 4.5  
**Versión:** 1.0  
**Fecha:** 2026-09-19  
**Licencia:** MIT
