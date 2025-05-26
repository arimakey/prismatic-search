import requests
import time
from typing import List, Dict, Any

from utils.file_utils import save_csv

def download_scopus_articles(query: str,
                             max_results: int = 1000,
                             project_name: str = "prismatic-search"
                             ) -> List[Dict[str, Any]]:
    """
    Descarga artículos de Scopus y devuelve lista de diccionarios
    con la estructura: title, authors, venue, year, citations, url, abstract.
    """
    API_KEY = "ddbd21300a00b5f5da2d75c7f33a7cac"
    base_url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }

    articles = []
    start = 0
    count = 25

    while start < max_results:
        params = {
            "query": query,
            "count": count,
            "start": start
        }

        resp = requests.get(base_url, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"Error en la solicitud: {resp.status_code}")
            break

        data = resp.json()
        entries = data.get("search-results", {}).get("entry", [])
        if not entries:
            break

        for entry in entries:
            # Transformar al formato deseado
            title = entry.get("dc:title", "")
            authors = entry.get("dc:creator", "")
            venue = entry.get("prism:publicationName", "")
            # Extraer año de coverDate, que viene en formato YYYY-MM-DD
            cover_date = entry.get("prism:coverDate", "")
            year = cover_date.split("-")[0] if cover_date else ""
            # Conteo de citas
            citations = 0
            try:
                citations = int(entry.get("citedby-count", "0"))
            except ValueError:
                pass
            # URL principal (primer link)
            url = ""
            links = entry.get("link", [])
            if links:
                # Buscar el link de tipo "scopus" o fallback al primero
                for l in links:
                    if l.get("@ref") == "scopus":
                        url = l.get("@href", "")
                        break
                else:
                    url = links[0].get("@href", "")
            # Abstract
            abstract = entry.get("dc:description", "")

            articles.append({
                "title":        title,
                "authors":      authors,
                "venue":        venue,
                "year":         year,
                "citations":    citations,
                "url":          url,
                "abstract":     abstract
            })

        start += count
        time.sleep(1)  # para respetar rate limits

    # Guardar en CSV usando la misma utilidad
    save_csv(project_name, "scopus", articles)
    print(f"{len(articles)} artículos guardados en el proyecto '{project_name}'.")

    return articles
