"""
summarizer.py
Módulo de discriminación, síntesis y auditoría factual con Google Gemini (gemini-3.5-flash-lite).
Implementa un pipeline en dos etapas:
  1. Generación de borrador editorial denso y estructurado.
  2. Auditoría factual (temp 0.0) con blindaje de negritas y hechos.
  3. Inyección determinista en Python de fecha y cabecera "The Digest Times" (Europe/Madrid).
"""

import json
import os
import time
from datetime import datetime
import zoneinfo
from typing import Dict, List, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

from collector import collect_news, load_config

# Carga de credenciales locales
load_dotenv()


def get_deterministic_header() -> str:
    """Calcula la fecha exacta en España peninsular y genera la cabecera fija."""
    tz = zoneinfo.ZoneInfo("Europe/Madrid")
    now = datetime.now(tz)

    dias_semana = [
        "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
    ]
    meses_ano = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    nombre_dia = dias_semana[now.weekday()]
    nombre_mes = meses_ano[now.month - 1]

    fecha_formateada = f"{nombre_dia}, {now.day} de {nombre_mes} de {now.year}"
    return f"<b>{fecha_formateada}</b>\n<b>The Digest Times</b>"


def build_system_instruction(config: Dict[str, Any]) -> str:
    """Construye las directrices editoriales con formato HTML y reglas transversales."""
    allowed = config.get("taxonomy", {}).get("allowed_topics", [])
    exclusions = config.get("taxonomy", {}).get("strict_exclusions", [])
    boundary_rules = config.get("taxonomy", {}).get("boundary_rules", [])

    allowed_text = "\n".join([f"- {item['name']}: {item['scope']}" for item in allowed])
    exclusions_text = "\n".join([f"- {ex}" for ex in exclusions])
    boundary_text = "\n".join([f"- {b['instruction']}" for b in boundary_rules])

    return f"""Eres el editor jefe de un briefing matinal diario de alta calidad informativa para Telegram.
Tu misión es seleccionar los acontecimientos de mayor peso de las últimas 24 horas, descartar el ruido y redactar un resumen amplio, profundo, analítico y neutral.

TEMÁTICAS PERMITIDAS:
{allowed_text}

EXCLUSIONES ESTRICTAS:
{exclusions_text}

REGLAS DE FRONTERA EDITORIAL:
{boundary_text}

RÚBRICA TRANSVERSAL DE IMPORTANCIA:
- PRIORIDAD MÁXIMA (Nivel 1): Hechos consumados con impacto estructural o sistémico.
  * Resoluciones vinculantes, acuerdos de Estado, leyes y giros geopolíticos.
  * En 📈 Economía: Decisiones de política monetaria (BCE, Fed), operaciones corporativas de fusión y adquisición (M&A) de gran escala, intervenciones antimonopolio y macroeconomía global.
  * Descubrimientos empíricos reproducibles publicados en revistas científicas de referencia.
  * Lanzamientos de producto o modelos tecnológicos troncales con impacto industrial real.
  * En ⚽ Fútbol: Resoluciones sancionadoras o normativas mayores, cambios determinantes en las grandes ligas europeas (Premier League, Champions League, LaLiga), títulos oficiales o fichajes confirmados. Prioriza SIEMPRE estos hitos sobre crónicas ordinarias de partido o polémicas.
  * En 🎬 Entretenimiento y 📚 Cultura: Obras, premios principales, estrenos y debates de calado nacional o internacional.
  * En 📍 Novelda: Acuerdos del pleno municipal, licitaciones de obra pública, cortes o cambios de servicios esenciales e hitos locales de peso.
- PRIORIDAD SECUNDARIA (Nivel 2): Crónicas sectoriales de fondo y novedades de calado general contrastadas.
- FILTRO DE DESCARTE (Nivel 3 - Prohibido incluir):
  * En Economía: Ruido de cotizaciones intradiarias, criptomonedas, finanzas domésticas o variaciones bursátiles sin hecho corporativo de fondo.
  * Agenda local o provincial en Cultura/Entretenimiento (ferias del libro locales, exposiciones provinciales o nombramientos directivos regionales).
  * Declaraciones retóricas o reproches políticos sin efectos jurídicos o institucionales.
  * Rumores de mercado, filtraciones sin confirmar o polémicas de redes sociales.
  * Anécdotas zoológicas o notas curiosas sin relevancia científica.
  * En Novelda: Sucesos menores, notas de trámite burocrático rutinario o eventos de circuito cerrado.

CRITERIO ORGÁNICO PARA ⚽ FÚTBOL:
1. El orden narrativo lo determina estrictamente el peso del hecho: la noticia más determinante de la jornada abre la sección.
2. Preferencia temática de seguimiento: entre la actualidad de clubes, si existen informaciones deportivas relevantes y contrastadas del Real Madrid (resultados de torneos oficiales, partes médicos clave, acuerdos institucionales o fichajes confirmados), priorízalas frente a la actualidad de otros clubes.
3. Sin forzar cuotas: no introduzcas al Real Madrid si un día no hay hechos sustanciales de Nivel 1 o 2, ni lo coloques por delante de un hito internacional de mayor envergadura objetiva.

REGLAS DE DENSIDAD, DIVERSIDAD Y COBERTURA:
1. Mínimo 2 a 3 hechos relevantes por sección:
   - Desarrolla cada hecho aportando contexto: qué ocurrió, quién intervino, cifras o datos objetivos y consecuencias prácticas.
   - Articula los hechos dentro de un único párrafo narrativo continuo y conexo, sin viñetas.
2. Paridad y pluralidad de fuentes:
   - Máximo 1 noticia por medio dentro de la misma sección.
   - Excepción estricta: Solo se admite una segunda noticia del mismo medio si es indiscutiblemente de Nivel 1 y supera con claridad la relevancia de las alternativas de otras cabeceras.
3. Dispersión temática interna:
   - En 🎬 Entretenimiento: equilibra cine, series y videojuegos.
   - En 📚 Cultura: equilibra literatura, patrimonio, arte y pensamiento.

REGLAS DE ESTILO Y FORMATO (HTML PARA TELEGRAM):
1. Tono sobrio y factual (Estilo teletipo internacional tipo Reuters o EFE): neutralidad estricta y precisión descriptiva.
2. Formato de encabezados (Aislamiento visual estricto):
   - Coloca ÚNICAMENTE el emoji y el nombre de la sección en negrita en su propia línea independiente.
   - PROHIBIDO añadir dos puntos (:) al final del encabezado o colocar texto en esa misma línea.
   - Salto de línea obligatorio: el cuerpo del párrafo debe empezar en la línea inmediatamente inferior al encabezado.
   - Usa exactamente estos nombres y este orden:
     🏛️ <b>Política</b>
     📈 <b>Economía</b>
     💻 <b>Tecnología</b>
     🎬 <b>Entretenimiento</b>
     📚 <b>Cultura</b>
     ⚽ <b>Fútbol</b>
     🔬 <b>Ciencias</b>
     📍 <b>Novelda</b> (colócala SIEMPRE en la última posición del digest).
3. Uso OBLIGATORIO de negritas <b>...</b> en el cuerpo:
   - En cada párrafo, resalta en negrita las palabras, sujetos o datos numéricos más relevantes de cada noticia narrada.
4. Integración limpia de enlaces:
   - Al final de la frase que explica cada acontecimiento, inserta ÚNICAMENTE el nombre del medio enlazado entre paréntesis: (<a href="URL">Nombre del Medio</a>).
   - PROHIBIDO poner el título de la noticia entre paréntesis.
5. Sintaxis HTML: Usa exclusivamente <b>, </i> y <a>. Cierra rigurosamente todas las etiquetas.
6. Presupuesto de extensión: Bloque general entre 3.400 y 3.800 caracteres.
7. ARRANQUE DIRECTO (SIN CABECERA NI FECHA):
   - PROHIBIDO escribir la fecha, el día de la semana, saludos o títulos iniciales (estos son inyectados automáticamente por el sistema).
   - Comienza DIRECTAMENTE con el encabezado de la primera sección: 🏛️ <b>Política</b>.
"""


def build_auditor_instruction() -> str:
    """Construye las directrices para la auditoría factual blindando las etiquetas de negrita."""
    return """Eres un auditor de verificación factual y control de calidad informativa (Fact-Checker estricto).
Tu cometido es contrastar el BORRADOR del briefing matinal recibido contra el listado de NOTICIAS FUENTE originales, corregir cualquier discrepancia o invención y PRESERVAR OBLIGATORIAMENTE el formato visual en HTML.

REGLAS DE VERIFICACIÓN ESTRICTA:
1. Fidelidad fáctica absoluta (Grounding):
   - Todo dato, nombre propio, cifra, cargo o rol atribuido a una persona debe coincidir con lo expresado en las noticias fuente.
   - Si el borrador altera la profesión o rol de un sujeto por sesgo de contexto (por ejemplo, calificar de futbolista a un hacker o perito), corrígelo de inmediato al rol exacto respaldado por la fuente documental.
   - Si el borrador incluye hechos no sustentados en las fuentes, ajústalos o elimínalos.

2. BLINDAJE OBLIGATORIO DE NEGRITAS Y FORMATO HTML:
   - PROHIBIDO ELIMINAR LAS NEGRITAS: El texto final DEBE conservar etiquetas <b>...</b> en las palabras, nombres, entidades o datos clave de cada párrafo.
   - Mantén idénticos los encabezados de sección con sus emojis (ej: 🏛️ <b>Política</b>) en su propia línea, sin añadir dos puntos (:).
   - Mantén los saltos de línea dobles entre secciones y el inicio de párrafo debajo del encabezado.
   - Conserva los enlaces en formato exacto: (<a href="URL">Medio</a>) al final de cada frase.
   - No incluyas fechas ni títulos globales en la apertura: el texto debe arrancar en 🏛️ <b>Política</b>.

3. Modo de salida:
   - Devuelve ÚNICAMENTE el texto final completamente corregido, verificado y debidamente maquetado con sus negritas y enlaces en HTML.
   - No agregues explicaciones, preámbulos ni disculpas.
"""


def audit_and_verify_digest(draft_text: str, articles_payload: List[Dict[str, str]], client: genai.Client) -> str:
    """Segunda pasada determinista (temperatura 0.0) para auditar la fidelidad factual y blindar negritas."""
    print("[*] Paso 2/2: Auditoría factual y blindaje de maquetación (Temperatura: 0.0)...")

    prompt_audit = (
        "NOTICIAS FUENTE ORIGINALES (JSON):\n"
        f"{json.dumps(articles_payload, ensure_ascii=False, indent=2)}\n\n"
        "BORRADOR A AUDITAR:\n"
        f"{draft_text}\n\n"
        "Verifica minuciosamente la fidelidad factual de cada hecho, rol y cifra contra las fuentes originales. "
        "Asegúrate de PRESERVAR Y GARANTIZAR las negritas <b>...</b> en las palabras y conceptos más importantes de cada párrafo, "
        "y devuelve el digest limpio y verificado en HTML, comenzando directamente en 🏛️ <b>Política</b>."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt_audit,
            config=types.GenerateContentConfig(
                system_instruction=build_auditor_instruction(),
                temperature=0.0,
            ),
        )
        return response.text
    except Exception as e:
        print(f"  [!] Advertencia: Falló la etapa de auditoría ({e}). Se entrega el borrador base.")
        return draft_text


def generate_digest(articles: List[Dict[str, str]], config: Dict[str, Any], max_retries: int = 3) -> str:
    """Pipeline completo: 1) Borrador -> 2) Auditoría -> 3) Inyección determinista de cabecera."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GEMINI_API_KEY en el archivo .env.")

    client = genai.Client(api_key=api_key)
    system_instruction = build_system_instruction(config)

    articles_payload = [
        {
            "source": art["source"],
            "title": art["title"],
            "summary": art["summary"],
            "url": art["url"]
        }
        for art in articles
    ]

    prompt_content = (
        f"A continuación tienes la lista de {len(articles_payload)} noticias recogidas en las últimas 24 horas:\n\n"
        f"{json.dumps(articles_payload, ensure_ascii=False, indent=2)}\n\n"
        "Aplica la rúbrica transversal de importancia. Redacta un digest amplio y denso (mínimo 2-3 hechos por sección). "
        "En Fútbol, respeta la jerarquía real del impacto informativo y aplica preferencia al Real Madrid solo entre la actualidad de clubes sin forzarla. "
        "Inserta los enlaces únicamente como (<a href=\"URL\">Medio</a>) al final de cada frase, sin títulos entre paréntesis. "
        "Aplica negritas <b>...</b> a las palabras y conceptos más importantes de cada párrafo. "
        "Comienza DIRECTAMENTE con '🏛️ <b>Política</b>' sin ninguna fecha previa. "
        "Aprovecha el presupuesto de 3.400 a 3.800 caracteres para el bloque general y sitúa Novelda al final."
    )

    print(f"[*] Paso 1/2: Generando borrador editorial con Gemini ({len(articles_payload)} artículos)...")

    draft_text = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                ),
            )
            draft_text = response.text
            break
        except (ServerError, APIError) as e:
            if attempt < max_retries:
                wait_seconds = attempt * 5
                print(f"  [!] Servidor ocupado ({e}). Reintentando en {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                raise e

    if not draft_text:
        raise RuntimeError("No se pudo generar el borrador editorial.")

    # Paso 2: Auditoría factual estricta con blindaje de negritas
    verified_body = audit_and_verify_digest(draft_text, articles_payload, client)

    # Paso 3: Inyección determinista de cabecera (Fecha en Madrid + The Digest Times)
    header = get_deterministic_header()
    final_digest = f"{header}\n\n{verified_body.strip()}"

    return final_digest


if __name__ == "__main__":
    cfg = load_config()
    news = collect_news(cfg, max_age_hours=24)
    if news:
        digest = generate_digest(news, cfg)
        print("\n" + "=" * 55)
        print("DIGEST CON FECHA DETERMINISTA")
        print("=" * 55)
        print(digest)
        print("=" * 55)
        print(f"Longitud total de caracteres: {len(digest)}")
    else:
        print("[!] No se encontraron noticias recientes en las últimas 24 horas.")