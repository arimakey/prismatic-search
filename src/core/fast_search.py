import datetime
import re
import requests
from bs4 import BeautifulSoup

# Función para contar artículos en Google Académico usando scraping.
def count_google_scholar_articles(query, start_date, end_date, project_name, criteria):
    """
    Busca en Google Académico la cantidad de artículos que contengan 'query'
    publicados entre start_date y end_date usando scraping.
    start_date y end_date deben ser objetos datetime.date.
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
    
    # Add criteria to the query
    if criteria:
        if criteria.get("idiomas"):
            params["lr"] = "lang_" + "|lang_".join(criteria["idiomas"])
        if criteria.get("año_mínimo"):
            params["as_ylo"] = criteria["año_mínimo"]
        if criteria.get("año_máximo"):
            params["as_yhi"] = criteria["año_máximo"]

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

# Función para contar artículos en Scopus utilizando su API.
def count_scopus_articles(query, start_date, end_date, api_key, project_name, criteria):
    """
    Busca en Scopus la cantidad de artículos que contengan 'query'
    publicados entre start_date y end_date utilizando la API de Scopus.
    
    start_date y end_date deben ser objetos datetime.date.
    api_key es tu clave de API de Elsevier.
    """
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json"
    }
    
    # Construimos el filtro de fechas. Scopus utiliza el campo "PUBYEAR"
    query_filter = ""
    if criteria:
        if criteria.get("año_mínimo"):
            query_filter += f"PUBYEAR > {int(criteria['año_mínimo']) - 1} AND "
        if criteria.get("año_máximo"):
            query_filter += f"PUBYEAR < {int(criteria['año_máximo']) + 1} AND "
    query_filter = query_filter.rstrip(" AND ")
    
    full_query = query
    if query_filter:
        full_query += f" AND {query_filter}"
    
    # Add criteria to the query
    if criteria:
        if criteria.get("tipos_estudio"):
            study_types_filter = " OR ".join([f"DOCTYPE({st})" for st in criteria["tipos_estudio"]])
            full_query += f" AND ({study_types_filter})"
            
    # Parámetros de la solicitud.
    params = {
        "query": full_query,
        "count": 0  # No necesitamos los registros, solamente el total.
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

# Ejemplo de uso:
if __name__ == "__main__":
    start = datetime.date(2018, 1, 1)
    end = datetime.date(2020, 12, 31)
    consulta = '("Impact of M2M Technologies on Cost Management in Supply Chains" OR "Impacto de las tecnologías M2M en la gestión de costos en cadenas de suministro") AND (automatización OR "visibilidad en tiempo real" OR "optimización de procesos" OR "eficiencia logística" OR "reducción de errores" OR "gestión de inventario" OR "mantenimiento predictivo" OR "optimización de recursos" OR "beneficios económicos" OR desafíos OR implementación OR "estructura de costos")'

    total_google = count_google_scholar_articles(consulta, start, end, project_name)
    if total_google is not None:
        print(f"Google Académico: {total_google} artículos encontrados.")
    else:
        print("No se pudo obtener la cantidad de Google Académico.")

    # Personaliza tu API Key para Scopus.
    API_KEY_SCOPUS = "ddbd21300a00b5f5da2d75c7f33a7cac"
    total_scopus = count_scopus_articles(consulta, start, end, API_KEY_SCOPUS, project_name)
    if total_scopus is not None:
        print(f"Scopus: {total_scopus} artículos encontrados.")
    else:
        print("Ocurrió un error al conectar con la API de Scopus.")

    from utils.file_utils import save_data_to_file
    results = f"Google Scholar: {total_google} articles found.\\nScopus: {total_scopus} articles found."
    save_data_to_file(project_name, "search_results.txt", results)
