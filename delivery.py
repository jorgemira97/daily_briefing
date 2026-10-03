"""
delivery.py
Pipeline de entrega a Telegram: recolección (24h), síntesis y envío.
Implementa desacople de entrega para emitir el bloque general y, de forma
separada e independiente, la sección local de Novelda al final.
"""

import os
import re
from typing import List
from dotenv import load_dotenv
import requests

from collector import collect_news, load_config
from summarizer import generate_digest

load_dotenv()


def split_into_sections(text: str, max_chars: int = 3800) -> List[str]:
    """
    Divide el texto respetando los límites de sección (\n\n).
    Garantiza que ningún mensaje corte párrafos o palabras a la mitad.
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 <= max_chars:
            current_chunk = f"{current_chunk}\n\n{p}" if current_chunk else p
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def send_telegram_message(text: str) -> bool:
    """Envía un bloque de texto a Telegram en HTML nativo con fallback a texto plano."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise ValueError("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en el archivo .env.")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = split_into_sections(text, max_chars=3800)

    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        res = requests.post(url, json=payload, timeout=15)

        if not res.ok:
            print(f"  [!] Reintentando en texto plano por error de parseo ({res.text})...")
            plain_text = re.sub(r"<[^>]+>", "", chunk)
            payload_plain = {
                "chat_id": chat_id,
                "text": plain_text,
                "disable_web_page_preview": True
            }
            res_plain = requests.post(url, json=payload_plain, timeout=15)
            if not res_plain.ok:
                print(f"  [X] Error crítico en envío Telegram: {res_plain.text}")
                return False

    return True


def run_pipeline():
    """Ejecución del pipeline completo con entrega desacoplada para Novelda."""
    print("=" * 55)
    print("INICIANDO FLUJO DEL DAILY BRIEFING")
    print("=" * 55)

    cfg = load_config()

    # 1. Recolección estricta de las últimas 24 horas
    news = collect_news(cfg, max_age_hours=24)
    if not news:
        print("[!] No se encontraron noticias recientes en las últimas 24 horas.")
        return

    # 2. Síntesis y discriminación
    try:
        digest = generate_digest(news, cfg)
    except Exception as e:
        print(f"[X] Error en síntesis con Gemini: {e}")
        return

    # 3. Partición de entrega: Bloque General vs Bloque Local
    marker = "📍 <b>Novelda</b>"
    if marker in digest:
        parts = digest.split(marker)
        general_digest = parts[0].strip()
        local_digest = f"{marker}{parts[1]}".strip()
    else:
        general_digest = digest.strip()
        local_digest = None

    # Envío 1: Digest General
    print("\n[*] Enviando bloque temático general a Telegram...")
    if not send_telegram_message(general_digest):
        print("[X] Falló la entrega del bloque general.")
        return

    # Envío 2: Píldora Local (Mensaje independiente)
    if local_digest:
        print("[*] Enviando bloque local de Novelda a Telegram...")
        if send_telegram_message(local_digest):
            print("[✓] ¡Bloque local de Novelda entregado con éxito!")
        else:
            print("[!] Advertencia: No se pudo entregar el bloque local.")

    print("\n[✓] ¡Pipeline diario completado con éxito!")


if __name__ == "__main__":
    run_pipeline()