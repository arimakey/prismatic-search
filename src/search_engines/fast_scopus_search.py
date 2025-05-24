import requests

def count_scopus_articles_simple(query):

    API_KEY = "ddbd21300a00b5f5da2d75c7f33a7cac"  # Reemplaza con tu API key válida
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "query": query,
        "count": 0
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        try:
            total_str = response.json().get('search-results', {}).get('opensearch:totalResults', "0")
            return int(total_str)
        except (ValueError, KeyError):
            return 0
    else:
        return None
