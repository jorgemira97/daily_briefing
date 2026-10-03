# 🗞️ The Digest Times — Automated Morning Briefing Pipeline

[![Daily Morning Briefing](https://github.com/<TU_USUARIO>/<TU_REPOSITORIO>/actions/workflows/daily_briefing.yml/badge.svg)](https://github.com/<TU_USUARIO>/<TU_REPOSITORIO>/actions/workflows/daily_briefing.yml)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![LLM](https://img.shields.io/badge/LLM-Gemini%203.5%20Flash--Lite-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Telegram Bot API](https://img.shields.io/badge/Delivery-Telegram%20Bot%20API-26A5E4.svg?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions%20(Serverless)-2088FF.svg?logo=githubactions&logoColor=white)](https://github.com/features/actions)

Pipeline de producción autónomo y serverless para la ingesta, sintetización editorial asistida por IA y distribución multicanal de información diaria a Telegram. Implementa una arquitectura desacoplada con verificación en dos etapas (*Two-Stage LLM Generation & Verification*), mitigación determinista de alucinaciones y ejecución desatendida invariante al cambio de hora.

---

## 🏛️ Arquitectura del Sistema y Flujo de Datos
                            [ FUENTES EXTERNAS ]
                  (Feeds RSS Nacionales, Sectoriales y Locales)
                                       │
                                       ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTA Y NORMALIZACIÓN (collector.py)                                              │
│    - Filtrado temporal estricto (ventana móvil de 24 horas).                           │
│    - Parsing tolerante a fallos de esquemas RSS/Atom heterogéneos.                     │
│    - Sanitización y extracción de metadatos (título, sumario, URL canónica).           │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
│ Payload JSON normalizado
▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. SÍNTESIS EDITORIAL Y VERIFICACIÓN FORENSE (summarizer.py)                           │
│    ├─ Etapa 1: Generador Editorial (Gemini 3.5 Flash-Lite | Temp: 0.1)                 │
│    │    - Taxonomía estricta de 8 secciones y rúbrica de peso estructural vs. ruido.   │
│    │    - Jerarquización objetiva, cobertura plural y presupuesto de caracteres.       │
│    │    - Formato HTML semántico con enlaces embebidos por cabecera.                   │
│    │                                                                                   │
│    ├─ Etapa 2: Auditor Factual Forense (Fact-Checker | Temp: 0.0)                      │
│    │    - Grounding estricto contra el JSON original (mitigación de sesgos contextuales)│
│    │    - Blindaje de formato visual y conservación obligatoria de etiquetas .      │
│    │                                                                                   │
│    └─ Etapa 3: Inyección Determinista de Cabecera (Python Nativo)                      │
│         - Cálculo exacto de fecha en 'Europe/Madrid' (eliminación de inferencia del LLM)│
└───────────────────────────────────┬────────────────────────────────────────────────────┘
│ Digest verificado en HTML
▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. ENTREGA Y DESACOPLE MODULAR (delivery.py)                                           │
│    - Control del límite estricto de Telegram (4.096 caracteres).                       │
│    - Desacoplamiento de entrega: Bloque General + Píldora Local independiente.         │
│    - Gestión de transporte y manejo de excepciones sobre Telegram Bot API.             │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
│ HTTPS POST
▼
[ CLIENTE TELEGRAM ]
(Entrega garantizada a las 08:15 CET / CEST)
---

## ⚙️ Características Técnicas y Decisiones de Diseño

### 1. LLMOps, Verificación y Control de Alucinaciones
* **Pipeline en Dos Fases (*Dual-Stage LLM Pipeline*):** Desacoplamiento de roles entre generación creativa/sintética (`temperature=0.1`) y verificación analítica (`temperature=0.0`). La segunda llamada actúa exclusivamente como un filtro forense de veracidad.
* **Mitigación de Deriva Contextual (*Role-Drift Mitigation*):** Instrucciones específicas para neutralizar la contaminación temática cruzada entre noticias agrupadas (por ejemplo, evitar que un perito judicial o informático sea categorizado como futbolista al redactar la sección deportiva).
* **Determinismo de Calendario en Python:** La fecha de publicación jamás se delega al razonamiento probabilístico del LLM. Se calcula e inyecta directamente desde Python mediante la librería nativa `zoneinfo` referenciada a la zona horaria peninsular española.

### 2. Infraestructura Serverless Resiliente (CI/CD)
* **Invarianza Estacional (DST Handling):** El programador de GitHub Actions opera en UTC. Para garantizar la entrega a las **08:15** locales tanto en horario de verano (CEST, UTC+2) como en horario de invierno (CET, UTC+1), el workflow se programa con un cron dual (`15 6,7 * * *`) respaldado por un validador bash que descarta de forma limpia la ejecución no correspondiente.
* **Mecanismo Autónomo *Keep-Alive*:** GitHub desactiva flujos programados tras 60 días de inactividad de commits. El pipeline ejecuta un chequeo el día 1 de cada mes que registra un micro-commit en `log.txt` con la etiqueta `[skip ci]`, garantizando operatividad perpetua sin mantenimiento manual.
* **Seguridad *Zero-Trust*:** Despliegue seguro en repositorio público. Las credenciales (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) están encapsuladas exclusivamente en GitHub Secrets y se inyectan como variables de entorno efímeras en el runner de Ubuntu.

---

## 📂 Taxonomía Editorial y Rúbrica de Relevancia

El contenido se estructura bajo un balance estricto de 8 secciones priorizadas por impacto sistémico:

| Emoji | Sección | Criterio de Inclusión (Nivel 1) | Filtro de Descarte (Ruido) |
| :---: | :--- | :--- | :--- |
| 🏛️ | **Política** | Resoluciones vinculantes, legislación, acuerdos de Estado. | Reproches retóricos, tertulias y declaraciones sin valor legal. |
| 📈 | **Economía** | Política monetaria (BCE/Fed), fusiones/adquisiciones troncales, macroeconomía. | Variaciones bursátiles intradiarias, criptomonedas, finanzas personales. |
| 💻 | **Tecnología** | Modelos fundacionales, regulación de IA, hardware troncal e infraestructura. | Filtraciones sin confirmar, rumores de producto o polémicas en redes. |
| 🎬 | **Entretenimiento** | Industria audiovisual global, estrenos clave, premios oficiales de referencia. | Prensa rosa, cotilleos o agenda de espectáculos provinciales. |
| 📚 | **Cultura** | Literatura de fondo, patrimonio histórico, artes plásticas y pensamiento. | Ferias locales, actos conmemorativos menores o nombramientos directivos. |
| ⚽ | **Fútbol** | Resoluciones disciplinarias, títulos, grandes ligas. *Preferencia de seguimiento orgánico al Real Madrid sin forzar cuotas*. | Rumores de fichajes no cerrados, polémicas arbitrales o tertulias. |
| 🔬 | **Ciencias** | Publicaciones indexadas (Nature, Science), hitos aeroespaciales reproducibles. | Notas curiosas, anécdotas zoológicas o estudios sin validación empírica. |
| 📍 | **Novelda** | Acuerdos del pleno municipal, licitaciones de obra pública, cortes o cambios de servicios esenciales e hitos locales de peso. | Sucesos rutinarios de tráfico o notas de trámite burocrático menor. |

---

## 📁 Estructura del Repositorio

```text
├── .github/
│   └── workflows/
│       └── daily_briefing.yml   # Workflow CI/CD (cron dual, validación horaria y keep-alive)
├── collector.py                 # Ingesta, filtrado temporal de 24h y extracción de feeds RSS
├── config_sources.yaml          # Catálogo de fuentes, taxonomía, reglas de frontera y exclusión
├── delivery.py                  # Orquestador del pipeline, segmentación de mensajes y API de Telegram
├── summarizer.py                # Pipeline dual LLM (Generador + Auditor Fact-Check a temp 0.0)
├── requirements.txt             # Dependencias fijadas para el entorno de producción
├── .gitignore                   # Blindaje contra subida de entornos (.env) y temporales
├── log.txt                      # Registro mensual de actividad desatendida (keep-alive)
└── README.md                    # Documentación técnica y Declaración de Diligencia

Prerrequisitos
Python 3.11 o superior.
API Key de Google Gemini (Google AI Studio).
Token de Bot de Telegram y Chat ID destino.

🛡️ Declaración de Diligencia y Gobernanza de IA (Diligence Statement)
Este proyecto ha sido desarrollado bajo un marco estructurado de Ingeniería Colaborativa Humano-IA, estableciendo límites precisos entre automatización generativa y gobernanza técnica:

1. Diligencia de Creación y Delegación de Tareas
Modelo Base: gemini-3.5-flash-lite consumido a través del SDK oficial google-genai.

Criterio de Elección: Optimización del balance entre coste computacional, baja latencia y ventana de contexto extendida para absorber decenas de artículos periodísticos en un solo prompt estructurado.

Frontera de Delegación:

Capacidades delegadas a la IA: Extracción de tesis informativas, jerarquización según rúbrica prefijada, condensación estilística y verificación cruzada de textos.

Responsabilidades reservadas a la lógica determinista (Python/Bash): Consumo HTTP de feeds, validación temporal de marcas de tiempo, cálculo invariante de calendario, control de límites de carga útil y transporte de red hacia Telegram.

2. Diligencia de Despliegue y Control Factual
Mitigación de Alucinaciones (Fact-Checking Pipeline): Implementación de una arquitectura en dos etapas. Un segundo agente evaluador con temperature=0.0 audita el borrador contrastándolo directamente con el volcado crudo de las fuentes originales antes de autorizar el envío.

Supervisión Estructural: El validador tiene restringida la modificación del maquetado HTML (<b>...</b> e hipervínculos estructurados), neutralizando el deterioro sintáctico común en salidas secuenciales de LLMs.

3. Supervisión Humana (Human-in-the-Loop) y Responsabilidad
Aunque el sistema opera en la nube con un 100% de autonomía técnica diaria:

Gobernanza Editorial: El autor supervisa activamente la vigencia de los feeds en config_sources.yaml para corregir desvíos de redifusión de las cabeceras periodísticas y mitigar sesgos de cobertura.

Auditoría Técnica: Se monitorizan de forma continua las métricas de ejecución, tiempos de respuesta y registros de fallos de la API en GitHub Actions.

Titularidad y Responsabilidad: La responsabilidad final sobre la calidad, exactitud y neutralidad del producto informativo recae exclusivamente sobre el autor del proyecto, actuando el modelo de lenguaje como una herramienta de síntesis asistida y no como una entidad de decisión autónoma.
