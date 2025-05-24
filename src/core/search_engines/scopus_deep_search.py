import requests
import time

from utils.file_utils import save_csv

def download_scopus_articles(query, max_results=1000, project_name="prismatic-search"):
    API_KEY = "ddbd21300a00b5f5da2d75c7f33a7cac"
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }

    articles = []
    start = 0
    count = 25  # máximo permitido por llamada

    while start < max_results:
        params = {
            "query": query,
            "count": count,
            "start": start
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error en la solicitud: {response.status_code}")
            break

        data = response.json()
        entries = data.get("search-results", {}).get("entry", [])
        if not entries:
            break

        for entry in entries:
            articles.append({
                "title": entry.get("dc:title", ""),
                "creator": entry.get("dc:creator", ""),
                "publicationName": entry.get("prism:publicationName", ""),
                "coverDate": entry.get("prism:coverDate", ""),
                "doi": entry.get("prism:doi", ""),
                "eid": entry.get("eid", "")
            })

        start += count
        time.sleep(1)  # evitar límite de tasa de la API

    # Guardar en CSV usando el método de utilidades
    save_csv(project_name, "scopus", articles)

    print(f"{len(articles)} artículos guardados en el proyecto '{project_name}'.")