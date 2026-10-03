"""
collector.py
Recolector de noticias RSS con emulación de navegador, bypass SSL,
control de latencia (timeout 15s) y filtro de frescura temporal (últimas 36 horas).
"""

from datetime import datetime, timezone, timedelta
import html
import re
from typing import Dict, List, Any, Optional
import feedparser
import requests
import urllib3
import yaml

# Silenciar advertencias de certificados en consola local
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sesión HTTP configurada con cabecera de navegador
session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})


def clean_html(raw_html: str) -> str:
    """Elimina etiquetas HTML y normaliza espacios en blanco."""
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_config(config_path: str = "config_sources.yaml") -> Dict[str, Any]:
    """Carga el archivo de configuración YAML con codificación UTF-8."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_feed_data(url: str, timeout: int = 15) -> bytes:
    """Descarga el contenido del feed con requests y margen de espera de 15 segundos."""
    response = session.get(url, timeout=timeout, verify=False)
    response.raise_for_status()
    return response.content


def parse_entry_datetime(entry: Any) -> Optional[datetime]:
    """Convierte la fecha de publicación del feed a datetime estándar en UTC."""
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed_time:
        try:
            return datetime(*parsed_time[:6], tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def collect_news(config: Dict[str, Any], max_age_hours: int = 36) -> List[Dict[str, str]]:
    """
    Recorre los feeds, aplica el filtro temporal, desduplica y
    construye la lista normalizada de noticias.
    """
    sources = config.get("sources", {})
    max_items = config.get("pipeline", {}).get("max_items_per_feed", 5)

    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    seen_links = set()
    collected_articles = []

    print(f"[*] Iniciando recolección. Solo noticias posteriores a: {cutoff_date.strftime('%Y-%m-%d %H:%M UTC')}\n")

    for source_id, source_data in sources.items():
        source_name = source_data.get("name", source_id)
        feeds = source_data.get("feeds", {})

        for section_name, feed_url in feeds.items():
            try:
                raw_xml = fetch_feed_data(feed_url, timeout=15)
                parsed = feedparser.parse(raw_xml)
                total_in_feed = len(parsed.entries)

                if total_in_feed == 0:
                    print(f"  [!] {source_name} ({section_name}): Feed vacío (0 entradas).")
                    continue

                items_added = 0
                items_expired = 0

                for entry in parsed.entries:
                    if items_added >= max_items:
                        break

                    link = entry.get("link", "").strip()
                    title = clean_html(entry.get("title", ""))
                    summary = clean_html(entry.get("summary", entry.get("description", "")))

                    if not title or not link or link in seen_links:
                        continue

                    # Validación de fecha de publicación
                    pub_date = parse_entry_datetime(entry)
                    if pub_date and pub_date < cutoff_date:
                        items_expired += 1
                        continue

                    seen_links.add(link)
                    collected_articles.append({
                        "source": source_name,
                        "section": section_name,
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "published_at": pub_date.strftime("%Y-%m-%d %H:%M") if pub_date else "N/A"
                    })
                    items_added += 1

                info_status = f"+{items_added} nuevas"
                if items_expired > 0:
                    info_status += f" | {items_expired} descartadas por antiguas"

                print(f"  [✓] {source_name} ({section_name}): {info_status} (de {total_in_feed} en feed)")

            except Exception as e:
                print(f"  [X] {source_name} ({section_name}): Error -> {e}")

    print(f"\n[✓] Recolección completada. Total de noticias frescas: {len(collected_articles)}")
    return collected_articles


if __name__ == "__main__":
    cfg = load_config()
    articles = collect_news(cfg, max_age_hours=36)

    print("\n--- MUESTRA DE LAS PRIMERAS NOTICIAS VÁLIDAS ---")
    for i, art in enumerate(articles[:5], 1):
        print(f"\n[{i}] {art['source']} ({art['section']}) | Fecha: {art['published_at']}")
        print(f"    Titular: {art['title']}")
        print(f"    Resumen: {art['summary'][:130]}...")