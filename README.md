# 🗞️ The Digest Times — Automated Morning Briefing Pipeline

[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![LLM](https://img.shields.io/badge/LLM-Gemini%203.5%20Flash--Lite-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Telegram Bot API](https://img.shields.io/badge/Delivery-Telegram%20Bot%20API-26A5E4.svg?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions%20(Serverless)-2088FF.svg?logo=githubactions&logoColor=white)](https://github.com/features/actions)

Pipeline de producción autónomo y serverless para la ingesta, sintetización editorial asistida por IA y distribución multicanal de información diaria a Telegram. Implementa una arquitectura desacoplada con verificación en dos etapas (*Two-Stage LLM Generation & Verification*), mitigación determinista de alucinaciones y ejecución desatendida invariante al cambio de hora.

---

## 🏛️ Arquitectura del Sistema y Flujo de Datos

El sistema opera bajo un pipeline modular desacoplado en cuatro fases consecutivas, asegurando trazabilidad, tolerancia a fallos y determinismo en cada etapa:

### 1. Ingesta y Normalización de Fuentes (collector.py)
Consumo multi-feed: Rastreo concurrente de cabeceras de prensa generalista, económica, tecnológica, científica, deportiva y medios locales (config_sources.yaml).

Ventana temporal estricta: Filtrado automático para descartar cualquier noticia publicada hace más de 24 horas respecto al momento de ejecución.

Sanitización de datos: Extracción normalizada de titular, sumario limpio y URL de origen en un esquema JSON estructurado, tolerante a variaciones de formato entre feeds RSS y Atom.

### 2. Síntesis Editorial y Auditoría en Dos Etapas (summarizer.py)
**Etapa 1** — Generador Editorial (gemini-3.5-flash-lite | Temp: 0.1):

Aplica una taxonomía de 8 secciones cerradas con rúbrica de impacto (hechos estructurales de Nivel 1 frente a ruido o declaraciones retóricas).

Distribución equitativa de medios y control de extensión (presupuesto de 3.400 a 3.800 caracteres).

Formateo semántico en HTML con enlaces integrados por medio.

**Etapa 2** — Auditor Factual Forense (Fact-Checker | Temp: 0.0):

Validación factual estricta (grounding) contrastando el borrador contra el volcado JSON original de noticias.

Mitigación de deriva de contexto (role-drift), corrigiendo atribuciones erróneas de cargos o profesiones provocadas por la proximidad temática.

Blindaje de sintaxis visual: garantiza la conservación obligatoria de etiquetas de negrita <b>...</b> en los puntos clave de cada párrafo.

**Etapa 3** — Inyección Determinista de Cabecera (Python nativo):

Python calcula directamente la fecha en español bajo la zona horaria Europe/Madrid y antepone el encabezado oficial The Digest Times, eliminando el riesgo de alucinación temporal del modelo.

### 3. Orquestación y Entrega Desacoplada (delivery.py)
Control de límites: Validación del volumen de caracteres frente al tope estricto de 4.096 caracteres de la Telegram Bot API.

Desacople modular: Envío independiente del bloque informativo general y de la píldora local de Novelda para evitar desbordamientos y permitir lectura segmentada.

Gestión de transporte: Manejo de excepciones de red y confirmación de recepción en el cliente de Telegram.

### 4. Automatización Serverless y Mantenimiento (daily_briefing.yml)
Invarianza horaria (DST): Disparo dual en GitHub Actions (06:15 UTC y 07:15 UTC) respaldado por un script bash que evalúa la hora local en España, garantizando la entrega exacta a las 08:15 tanto en horario de verano (CEST) como de invierno (CET).

Mecanismo Keep-Alive: Ejecución mensual condicionada (día 1 de cada mes) que genera un micro-commit en log.txt, evitando que GitHub Actions congele los flujos automáticos por la regla de 60 días de inactividad.

Seguridad Zero-Trust: Repositorio público sin exposición de variables; inyección segura de credenciales mediante GitHub Secrets en entornos efímeros de Ubuntu.

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

## Prerrequisitos
Python 3.11 o superior.
API Key de Google Gemini (Google AI Studio).
Token de Bot de Telegram y Chat ID destino.

## 🛡️ Declaración de Diligencia y Gobernanza de IA (Diligence Statement)
Este proyecto ha sido desarrollado bajo un marco estructurado de Ingeniería Colaborativa Humano-IA, estableciendo límites precisos entre automatización generativa y gobernanza técnica:

**1. Diligencia de Creación y Delegación de Tareas**
Modelo Base: gemini-3.5-flash-lite consumido a través del SDK oficial google-genai.

Criterio de Elección: Optimización del balance entre coste computacional, baja latencia y ventana de contexto extendida para absorber decenas de artículos periodísticos en un solo prompt estructurado.

Frontera de Delegación:

Capacidades delegadas a la IA: Extracción de tesis informativas, jerarquización según rúbrica prefijada, condensación estilística y verificación cruzada de textos.

Responsabilidades reservadas a la lógica determinista (Python/Bash): Consumo HTTP de feeds, validación temporal de marcas de tiempo, cálculo invariante de calendario, control de límites de carga útil y transporte de red hacia Telegram.

**2. Diligencia de Despliegue y Control Factual**
Mitigación de Alucinaciones (Fact-Checking Pipeline): Implementación de una arquitectura en dos etapas. Un segundo agente evaluador con temperature=0.0 audita el borrador contrastándolo directamente con el volcado crudo de las fuentes originales antes de autorizar el envío.

Supervisión Estructural: El validador tiene restringida la modificación del maquetado HTML (<b>...</b> e hipervínculos estructurados), neutralizando el deterioro sintáctico común en salidas secuenciales de LLMs.

**3. Supervisión Humana (Human-in-the-Loop) y Responsabilidad**
Aunque el sistema opera en la nube con un 100% de autonomía técnica diaria:

Gobernanza Editorial: El autor supervisa activamente la vigencia de los feeds en config_sources.yaml para corregir desvíos de redifusión de las cabeceras periodísticas y mitigar sesgos de cobertura.

Auditoría Técnica: Se monitorizan de forma continua las métricas de ejecución, tiempos de respuesta y registros de fallos de la API en GitHub Actions.

Titularidad y Responsabilidad: La responsabilidad final sobre la calidad, exactitud y neutralidad del producto informativo recae exclusivamente sobre el autor del proyecto, actuando el modelo de lenguaje como una herramienta de síntesis asistida y no como una entidad de decisión autónoma.
