import datetime
import re
import requests
from bs4 import BeautifulSoup

def count_google_scholar_articles(query, start_date, end_date, project_name, api_key, filters=None):
    """
    Search Google Scholar for articles containing 'query' published between start_date and end_date using web scraping.
    start_date and end_date can be None, 'Sin restricción', 'Presente' or year strings.
    filters: Optional list of language codes (e.g. ['en', 'es'])
    """
    url = "https://scholar.google.com/scholar"
    params = {
        "hl": "es",
        "q": query,
        "as_sdt": "0,5"
    }
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/92.0.4515.131 Safari/537.36")
    }
    
    # Add language filter if specified
    if filters:
        params["lr"] = "lang_" + "|".join(filters)
        
    # Add date parameters if provided
    if start_date and start_date != 'Sin restricción':
        params["as_ylo"] = start_date
    if end_date and end_date != 'Presente':
        params["as_yhi"] = end_date

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    count = 0
    # El div con id "gs_ab_md" contiene la información de resultados.
    result_div = soup.find("div", id="gs_ab_md")
    if result_div:
        text = result_div.get_text()
        # Se busca secuencia de números (con comas o puntos como separadores)
        match = re.search(r'([\d.,]+)', text)
        if match:
            count_str = match.group(1)
            # Normalización removiendo separadores (para números grandes en formatos locales)
            count_str = count_str.replace(',', '').replace('.', '')
            try:
                count = int(count_str)
            except ValueError:
                count = 0
    return count

def count_scopus_articles(query, start_date, end_date, project_name, api_key, filters=None):
    """
    Search Scopus for articles containing 'query' published between start_date and end_date using Scopus API.
    
    start_date can be 'Sin restricción' or year string
    end_date can be 'Presente' or year string
    api_key: Elsevier API key
    filters: Optional list of document types (e.g. ['ar', 'cp'])
    """
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json"
    }
    
    # Build date filter using PUBYEAR
    query_filter = ""
    if start_date and start_date != 'Sin restricción':
        query_filter += f"PUBYEAR > {int(start_date) - 1} AND "
    if end_date and end_date != 'Presente':
        query_filter += f"PUBYEAR < {int(end_date) + 1} AND "
    query_filter = query_filter.rstrip(" AND ")
    
    full_query = query
    if query_filter:
        full_query += f" AND {query_filter}"
    
    # Add document type filter if specified
    if filters:
        doc_types_filter = " OR ".join([f"DOCTYPE({dt})" for dt in filters])
        full_query += f" AND ({doc_types_filter})"
            
    params = {
        "query": full_query,
        "count": 0  # We only need the total count
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        total_str = data.get('search-results', {}).get('opensearch:totalResults', "0")
        try:
            total = int(total_str)
        except ValueError:
            total = 0
        return total
    else:
        return None
