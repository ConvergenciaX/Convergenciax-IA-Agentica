# 📚 Ejemplos de Uso: CrewAI con Ollama

Colección de ejemplos prácticos para ejecutar el sistema multiagente con diferentes temas y configuraciones.

## Ejemplos Básicos

### 1. Ejecución por Defecto (Sin Argumentos)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py
```

**Tema por defecto:** "avances recientes en inteligencia artificial generativa"  
**Modelo:** qwen2.5:7b  
**Temperatura:** 0.7 (balance entre creatividad y precisión)

**Salida esperada:** Artículo de blog de 4-5 párrafos sobre IA generativa

---

## Ejemplos por Categoría

### 🤖 Tecnología e IA

#### Ejemplo 1: Últimas Tendencias en IA

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "tendencias de desarrollo de IA en 2025" `
  --model qwen2.5:7b
```

#### Ejemplo 2: Ciberseguridad

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "amenazas cibernéticas emergentes y defensa"
```

#### Ejemplo 3: DevOps y Cloud

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "mejores prácticas de DevOps en 2025"
```

#### Ejemplo 4: Programación

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "paradigmas de programación modernos"
```

---

### 🔬 Ciencia

#### Ejemplo 5: Computación Cuántica

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "avances en computación cuántica" `
  --temperature 0.7
```

#### Ejemplo 6: Neurociencia

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "descubrimientos recientes en neurociencia cognitiva"
```

#### Ejemplo 7: Física

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "teoría de cuerdas y gravedad cuántica" `
  --temperature 0.5
```

#### Ejemplo 8: Biotecnología

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "CRISPR y edición genética: aplicaciones médicas"
```

---

### 🌍 Sostenibilidad

#### Ejemplo 9: Energías Renovables

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "transición a energías renovables" `
  --model qwen2.5:7b
```

#### Ejemplo 10: Cambio Climático

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "mitigación del cambio climático: soluciones tecnológicas"
```

#### Ejemplo 11: Economía Circular

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "economía circular y sostenibilidad"
```

---

### 💼 Negocios

#### Ejemplo 12: Transformación Digital

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "transformación digital en empresas" `
  --temperature 0.6
```

#### Ejemplo 13: Análisis de Mercados

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "tendencias del mercado de tecnología"
```

#### Ejemplo 14: Emprendimiento

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "estrategias de emprendimiento en la era digital"
```

---

### 📊 Datos e Inteligencia de Negocios

#### Ejemplo 15: Big Data

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "big data y análisis de datos masivos"
```

#### Ejemplo 16: Machine Learning

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "aplicaciones prácticas de machine learning"
```

---

### 🎨 Creatividad y Arte

#### Ejemplo 17: IA Generativa (Creativa)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "arte digital y IA generativa" `
  --temperature 0.9
```

#### Ejemplo 18: Diseño

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "tendencias de diseño en 2025" `
  --temperature 0.8
```

#### Ejemplo 19: Narrativa

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "el futuro de la narrativa digital" `
  --temperature 0.85
```

---

## Ejemplos con Diferentes Configuraciones

### 🚀 Modo Muy Creativo (Temperatura Alta)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "especulación sobre civilizaciones extraterrestres" `
  --temperature 0.95
```

**Efecto:** Respuestas más creativas, originales, pero menos precisas

### ⚙️ Modo Muy Preciso (Temperatura Baja)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "definición técnica de criptografía asimétrica" `
  --temperature 0.2
```

**Efecto:** Respuestas factualmente precisas y consistentes

### ⚖️ Modo Equilibrado (Temperatura Intermedia)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "el futuro de la educación" `
  --temperature 0.5
```

**Efecto:** Balance entre creatividad e información precisa

---

## Ejemplos con Diferentes Modelos

### Modelo: Qwen2.5 (Recomendado - Rápido)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --model qwen2.5:7b `
  --topic "arquitectura de microservicios"
```

**Características:** Muy rápido (3-4 min), buena calidad

### Modelo: Llama 2 (Equilibrado)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --model llama2 `
  --topic "redes neuronales profundas"
```

**Características:** Rápido (2-3 min), excelente calidad

### Modelo: Neural Chat (Conversacional)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --model neural-chat `
  --topic "cómo aprender inteligencia artificial"
```

**Características:** Conversacional, bueno para educación

---

## Ejemplos Avanzados

### 📝 Con Modo Verbose (Ver Detalles de Ejecución)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "cadena de bloques" `
  --verbose
```

**Muestra:** Cada paso de la ejecución, logs detallados

### 💾 Guardar Resultado Automáticamente

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "metaverso y realidad virtual" `
  --save
```

**Genera:** Archivo en `outputs/resultado_TIMESTAMP.txt`

### 🔄 Combinación Completa

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "Web3 y descentralización" `
  --model qwen2.5:7b `
  --temperature 0.7 `
  --verbose `
  --save
```

---

## Ejemplos Temáticos Especiales

### 📚 Para Educadores

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "pedagogía moderna y tecnología educativa" `
  --temperature 0.7
```

### 👨‍💼 Para Profesionales IT

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "infraestructura moderna y mejores prácticas DevOps" `
  --temperature 0.5
```

### 🏥 Para Sector Salud

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "telemedicina y salud digital" `
  --temperature 0.6
```

### 📈 Para Analistas

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "análisis predictivo y data science" `
  --temperature 0.4
```

---

## Script de Ejecución Múltiple

Para procesar varios temas en lote:

```powershell
# crear_batch.ps1
$temas = @(
    "inteligencia artificial",
    "sostenibilidad",
    "ciberseguridad",
    "blockchain"
)

$env = "C:\workspace-vc\env-llm-314\Scripts\python.exe"
$script = "crewai_ollama.py"

foreach ($tema in $temas) {
    Write-Host "Procesando: $tema"
    & $env $script --topic $tema --save
    Write-Host "Completado: $tema`n"
}
```

Ejecutar:
```powershell
.\crear_batch.ps1
```

---

## Consejos Prácticos

### ✅ Recomendaciones

1. **Temas específicos:** Funcionan mejor que temas genéricos
2. **Temperatura 0.5-0.7:** Balance óptimo para la mayoría de casos
3. **Modelo qwen2.5:7b:** Mejor relación velocidad-calidad
4. **Verbose en primeras ejecuciones:** Para entender el flujo

### ⏱️ Tiempos Esperados

| Modelo | Tiempo |
|--------|--------|
| qwen2.5:7b | 3-5 minutos |
| llama2 | 2-4 minutos |
| neural-chat | 4-6 minutos |

### 💾 Gestión de Archivos

```
outputs/                    # Resultados generados
├── resultado_20260913_142530.txt
├── resultado_20260913_143045.txt
└── ...

logs/                       # Logs de ejecución
├── crewai_20260913_142530.log
├── crewai_20260913_143045.log
└── ...
```

---

## Troubleshooting con Ejemplos

### Problema: Ejecución lenta

```powershell
# Usar modelo más rápido
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --model llama2 `
  --topic "tu_tema"
```

### Problema: Resultado genérico

```powershell
# Ser más específico en el tema
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "impacto de transformers en NLP 2024-2025" `
  --temperature 0.5
```

### Problema: Necesitas respuesta más creativa

```powershell
# Aumentar temperatura
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py `
  --topic "tu_tema_creativo" `
  --temperature 0.85
```

---

**¡Prueba estos ejemplos y personaliza según tus necesidades! 🚀**
