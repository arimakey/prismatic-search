import time
import random
import re
import urllib.parse
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils.file_utils import save_csv


def configure_driver(headless=True):
    """Configura y retorna el driver de Selenium"""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.212 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver


def modify_url_start_parameter(url, start_value):
    """
    Modifica o inserta el parámetro 'start' en la URL de Google Scholar para paginación.
    """
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(parsed.query)
    q['start'] = [str(start_value)]
    new_query = urllib.parse.urlencode(q, doseq=True)
    return urllib.parse.urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))


def extract_article_data(elem):
    """Extrae metadatos de un elemento de artículo en Google Scholar"""
    data = {'title': '', 'authors': '', 'venue': '', 'year': '', 'citations': 0, 'url': '', 'abstract': ''}
    try:
        # Título y URL
        try:
            t = elem.find_element(By.CSS_SELECTOR, ".gs_rt a")
            data['title'] = t.text
            data['url'] = t.get_attribute('href')
        except NoSuchElementException:
            t_alt = elem.find_element(By.CLASS_NAME, 'gs_rt')
            data['title'] = t_alt.text

        # Autores, lugar de publicación y año
        meta = elem.find_element(By.CLASS_NAME, 'gs_a').text
        parts = meta.split(' - ')
        data['authors'] = parts[0]
        if len(parts) > 1:
            year_match = re.search(r"\b(19|20)\d{2}\b", parts[1])
            if year_match:
                data['year'] = year_match.group(0)
                data['venue'] = parts[1].replace(data['year'], '').strip().strip(',')                
            else:
                data['venue'] = parts[1]

        # Citas
        try:
            c_text = elem.find_element(By.XPATH, ".//a[contains(text(),'Citado por') or contains(text(),'Cited by')]").text
            c_num = re.search(r"\d+", c_text)
            if c_num:
                data['citations'] = int(c_num.group(0))
        except NoSuchElementException:
            pass

        # Resumen
        try:
            data['abstract'] = elem.find_element(By.CLASS_NAME, 'gs_rs').text
        except NoSuchElementException:
            pass

    except Exception:
        return None
    return data


def download_google_scholar_articles(query, max_results=1000, project_name="prismatic-search", max_retries=3):
    """
    Descarga (simula) resultados de Google Scholar usando Selenium.

    Args:
        query (str): Consulta de búsqueda.
        max_results (int): Número máximo de artículos a extraer.
        project_name (str): Nombre del proyecto para guardar resultados.
        max_retries (int): Número máximo de intentos por página.

    Returns:
        list: Lista de diccionarios con metadatos de artículos.
    """
    base_url = f"https://scholar.google.com/scholar?hl=es&as_sdt=0%2C5&q={urllib.parse.quote(query)}"
    driver = configure_driver(headless=True)
    results = []
    per_page = 20  # Google Scholar muestra 20 artículos por página
    total_pages = (max_results + per_page - 1) // per_page

    try:
        for page in tqdm(range(total_pages), desc="Páginas Google Scholar"):
            start = page * per_page
            url = modify_url_start_parameter(base_url, start)
            print(f"Consultando URL: {url}")  # Mostrar URL para verificar

            retry_count = 0
            while retry_count < max_retries:
                try:
                    driver.get(url)
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'gs_ri'))
                    )

                    # Verificar bloqueo
                    if "sorry" in driver.page_source.lower() or "robot" in driver.page_source.lower():
                        print(f"\nBloqueo detectado, esperando... (intento {retry_count + 1}/{max_retries})")
                        time.sleep(random.uniform(10, 15))
                        retry_count += 1
                        continue

                    elems = driver.find_elements(By.CSS_SELECTOR, ".gs_r.gs_or.gs_scl")
                    if not elems:
                        print("No se encontraron resultados en esta página")
                        break

                    for e in elems:
                        if len(results) >= max_results:
                            break
                        art = extract_article_data(e)
                        if art:
                            results.append(art)

                    time.sleep(random.uniform(3, 7))  # Espera después de éxito
                    break

                except TimeoutException:
                    print(f"\nTimeout en página {page + 1}, reintentando... (intento {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    time.sleep(random.uniform(5, 10))
                except Exception as e:
                    print(f"\nError inesperado: {str(e)}")
                    retry_count += 1
                    time.sleep(random.uniform(5, 10))

            if len(results) >= max_results:
                break

    except Exception as e:
        print(f"\nError durante la extracción: {str(e)}")
    finally:
        driver.quit()

    if results:
        save_csv(project_name, "google", results)
        print(f"\nGuardados {len(results)} artículos en '{project_name}'")
    else:
        print("\nNo se pudieron obtener resultados de Google Scholar")

    return results
