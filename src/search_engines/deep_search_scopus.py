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
    count = 25

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
                "type": entry.get("prism:aggregationType", ""),
                "url": entry.get("link", [])[0].get("@href", "") if entry.get("link") else "",
                "coverDate": entry.get("prism:coverDate", ""),
                "citedbyCount": entry.get("citedby-count", ""),
                "affiliations": [affil.get("affilname", "") for affil in entry.get("affiliation", [])],
                "publicationName": entry.get("prism:publicationName", ""),
                "openAccess": entry.get("openaccessFlag", False),
                "doi": entry.get("prism:doi", ""),
                "abstract": entry.get("dc:description", "")  # <-- Campo agregado
            })

        start += count
        time.sleep(1) 

    save_csv(project_name, "scopus", articles)

    print(f"{len(articles)} artículos guardados en el proyecto '{project_name}'.")