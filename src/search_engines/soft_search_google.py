import time
import random
import re
import urllib.parse
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from utils.file_utils import save_csv


@dataclass
class ArticleData:
    """Estructura de datos para artículos de Google Scholar"""
    title: str = ''
    authors: str = ''
    venue: str = ''
    year: str = ''
    citations: int = 0
    url: str = ''
    abstract: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'authors': self.authors,
            'venue': self.venue,
            'year': self.year,
            'citations': self.citations,
            'url': self.url,
            'abstract': self.abstract
        }


class GoogleScholarScraper:
    """Scraper optimizado para Google Scholar con mejor manejo de errores y logging"""
    
    def __init__(self, headless: bool = True, timeout: int = 15):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.results_per_page = 20
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('scholar_scraper.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def configure_driver(self) -> webdriver.Chrome:
        """Configura y retorna el driver de Selenium con opciones optimizadas"""
        options = Options()
        
        # Configuraciones básicas
        if self.headless:
            options.add_argument("--headless")
        
        # Optimizaciones de rendimiento
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # User agent realista
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Configuraciones adicionales para evitar detección
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.logger.error(f"Error configurando driver: {e}")
            raise
    
    def modify_url_pagination(self, base_url: str, start_value: int) -> str:
        """Modifica la URL para paginación en Google Scholar"""
        try:
            parsed = urllib.parse.urlparse(base_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            query_params['start'] = [str(start_value)]
            
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            return urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
        except Exception as e:
            self.logger.error(f"Error modificando URL: {e}")
            return base_url
    
    def extract_article_metadata(self, element) -> Optional[ArticleData]:
        """Extrae metadatos de un elemento de artículo"""
        try:
            article = ArticleData()
            
            # Extraer título y URL
            self._extract_title_and_url(element, article)
            
            # Extraer información de autores, venue y año
            self._extract_publication_info(element, article)
            
            # Extraer número de citas
            self._extract_citations(element, article)
            
            # Extraer resumen
            self._extract_abstract(element, article)
            
            # Validar que al menos tengamos título
            if not article.title.strip():
                return None
                
            return article
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo metadatos: {e}")
            return None
    
    def _extract_title_and_url(self, element, article: ArticleData):
        """Extrae título y URL del artículo"""
        try:
            title_elem = element.find_element(By.CSS_SELECTOR, ".gs_rt a")
            article.title = title_elem.text.strip()
            article.url = title_elem.get_attribute('href') or ''
        except NoSuchElementException:
            try:
                title_elem = element.find_element(By.CLASS_NAME, 'gs_rt')
                article.title = title_elem.text.strip()
            except NoSuchElementException:
                pass
    
    def _extract_publication_info(self, element, article: ArticleData):
        """Extrae información de publicación (autores, venue, año)"""
        try:
            meta_elem = element.find_element(By.CLASS_NAME, 'gs_a')
            meta_text = meta_elem.text.strip()
            
            # Dividir por ' - ' para separar autores de venue/año
            parts = meta_text.split(' - ')
            
            if parts:
                article.authors = parts[0].strip()
            
            if len(parts) > 1:
                venue_year = parts[1].strip()
                
                # Buscar año (4 dígitos que empiecen con 19 o 20)
                year_match = re.search(r'\b(19|20)\d{2}\b', venue_year)
                if year_match:
                    article.year = year_match.group(0)
                    # Remover año del venue
                    article.venue = re.sub(r'\b(19|20)\d{2}\b', '', venue_year).strip(' ,-')
                else:
                    article.venue = venue_year
                    
        except NoSuchElementException:
            pass
    
    def _extract_citations(self, element, article: ArticleData):
        """Extrae número de citas"""
        try:
            citation_elem = element.find_element(
                By.XPATH, 
                ".//a[contains(text(),'Citado por') or contains(text(),'Cited by')]"
            )
            citation_text = citation_elem.text
            citation_match = re.search(r'\d+', citation_text)
            if citation_match:
                article.citations = int(citation_match.group(0))
        except (NoSuchElementException, ValueError):
            pass
    
    def _extract_abstract(self, element, article: ArticleData):
        """Extrae resumen del artículo"""
        try:
            abstract_elem = element.find_element(By.CLASS_NAME, 'gs_rs')
            article.abstract = abstract_elem.text.strip()
        except NoSuchElementException:
            pass
    
    def check_for_blocking(self) -> bool:
        """Verifica si Google Scholar nos está bloqueando"""
        page_source = self.driver.page_source.lower()
        blocking_indicators = [
            'sorry', 'robot', 'automated', 'captcha', 
            'unusual traffic', 'try again later'
        ]
        return any(indicator in page_source for indicator in blocking_indicators)
    
    def wait_with_backoff(self, attempt: int, base_delay: float = 5.0):
        """Implementa backoff exponencial para reintentos"""
        delay = base_delay * (2 ** attempt) + random.uniform(1, 3)
        self.logger.info(f"Esperando {delay:.1f} segundos antes del reintento...")
        time.sleep(delay)
    
    def scrape_articles(self, query: str, max_results: int = 1000, 
                      project_name: str = "prismatic-search", 
                      max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Función principal para descargar artículos de Google Scholar
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados a obtener
            project_name: Nombre del proyecto para guardar archivos
            max_retries: Número máximo de reintentos por página
            
        Returns:
            Lista de diccionarios con los datos de los artículos
        """
        # Configurar URL base
        base_url = f"https://scholar.google.com/scholar?hl=es&as_sdt=0%2C5&q={urllib.parse.quote(query)}"
        
        # Inicializar variables
        results = []
        total_pages = (max_results + self.results_per_page - 1) // self.results_per_page
        
        self.logger.info(f"Iniciando scraping de Google Scholar para: '{query}'")
        self.logger.info(f"Páginas a procesar: {total_pages}, Máximo resultados: {max_results}")
        
        try:
            # Configurar driver
            self.driver = self.configure_driver()
            
            # Procesar páginas con barra de progreso
            with tqdm(total=total_pages, desc="🔍 Procesando páginas", 
                     bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
                
                for page_num in range(total_pages):
                    if len(results) >= max_results:
                        self.logger.info("Se alcanzó el límite máximo de resultados")
                        break
                    
                    # Calcular offset para paginación
                    start_offset = page_num * self.results_per_page
                    current_url = self.modify_url_pagination(base_url, start_offset)
                    
                    # Intentar procesar la página con reintentos
                    page_results = self._process_page_with_retries(
                        current_url, page_num + 1, max_retries, max_results - len(results)
                    )
                    
                    if page_results is None:
                        self.logger.warning(f"Falló el procesamiento de la página {page_num + 1}")
                        continue
                    
                    results.extend(page_results)
                    pbar.update(1)
                    pbar.set_postfix({"Artículos": len(results)})
                    
                    # Pausa entre páginas para evitar detección
                    if page_num < total_pages - 1:  # No esperar después de la última página
                        time.sleep(random.uniform(2, 5))
            
        except KeyboardInterrupt:
            self.logger.info("Proceso interrumpido por el usuario")
        except Exception as e:
            self.logger.error(f"Error durante el scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        
        # Guardar resultados
        if results:
            self._save_results(results, project_name)
            self.logger.info(f"✅ Proceso completado: {len(results)} artículos guardados")
        else:
            self.logger.warning("❌ No se obtuvieron resultados")
        
        return [article.to_dict() if isinstance(article, ArticleData) else article for article in results]
    
    def _process_page_with_retries(self, url: str, page_num: int, 
                                 max_retries: int, max_articles: int) -> Optional[List[ArticleData]]:
        """Procesa una página con sistema de reintentos"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                
                # Esperar a que carguen los resultados
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'gs_ri'))
                )
                
                # Verificar bloqueo
                if self.check_for_blocking():
                    self.logger.warning(f"Bloqueo detectado en página {page_num} (intento {attempt + 1})")
                    if attempt < max_retries - 1:
                        self.wait_with_backoff(attempt, 8)
                        continue
                    else:
                        return None
                
                # Extraer artículos
                elements = self.driver.find_elements(By.CSS_SELECTOR, ".gs_r.gs_or.gs_scl")
                
                if not elements:
                    self.logger.warning(f"No se encontraron resultados en página {page_num}")
                    return []
                
                page_results = []
                for element in elements:
                    if len(page_results) >= max_articles:
                        break
                        
                    article = self.extract_article_metadata(element)
                    if article:
                        page_results.append(article)
                
                self.logger.info(f"Página {page_num}: {len(page_results)} artículos extraídos")
                return page_results
                
            except TimeoutException:
                self.logger.warning(f"Timeout en página {page_num} (intento {attempt + 1})")
                if attempt < max_retries - 1:
                    self.wait_with_backoff(attempt)
            except WebDriverException as e:
                self.logger.error(f"Error del WebDriver en página {page_num}: {e}")
                if attempt < max_retries - 1:
                    self.wait_with_backoff(attempt)
            except Exception as e:
                self.logger.error(f"Error inesperado en página {page_num}: {e}")
                if attempt < max_retries - 1:
                    self.wait_with_backoff(attempt)
        
        return None
    
    def _save_results(self, results: List[ArticleData], project_name: str):
        """Guarda los resultados en archivo CSV"""
        try:
            dict_results = [article.to_dict() for article in results]
            save_csv(project_name, "google", dict_results)
            
            # Mostrar estadísticas
            self._print_statistics(results)
            
        except Exception as e:
            self.logger.error(f"Error guardando resultados: {e}")
    
    def _print_statistics(self, results: List[ArticleData]):
        """Imprime estadísticas de los resultados"""
        if not results:
            return
            
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS DE LA BÚSQUEDA")
        print("="*60)
        print(f"Total de artículos: {len(results)}")
        
        # Artículos con URL
        with_url = sum(1 for r in results if r.url)
        print(f"Con URL: {with_url} ({with_url/len(results)*100:.1f}%)")
        
        # Artículos con año
        with_year = sum(1 for r in results if r.year)
        print(f"Con año: {with_year} ({with_year/len(results)*100:.1f}%)")
        
        # Citas totales
        total_citations = sum(r.citations for r in results)
        print(f"Citas totales: {total_citations:,}")
        
        if with_year > 0:
            years = [int(r.year) for r in results if r.year.isdigit()]
            if years:
                print(f"Rango de años: {min(years)} - {max(years)}")
        
        print("="*60)


# Función de compatibilidad con la API anterior
def download_google_scholar_articles(query: str, max_results: int = 1000, 
                                   project_name: str = "prismatic-search", 
                                   max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    Función wrapper para mantener compatibilidad con la API anterior
    """
    scraper = GoogleScholarScraper()
    return scraper.scrape_articles(query, max_results, project_name, max_retries)