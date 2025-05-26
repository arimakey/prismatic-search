import time
import random
import re
import urllib.parse
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from tqdm import tqdm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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
    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.driver = None
        self.results_per_page = 10
        self.console = Console()
        self.is_headless = True  # Comenzar siempre en modo headless
        self.captcha_resolved = False
        self._setup_logging()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler('scholar_scraper.log')]
        )
        self.logger = logging.getLogger(__name__)

    def _configure_driver(self, force_visible: bool = False) -> webdriver.Chrome:
        options = Options()
        
        # User Agent aleatorio y realista
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Configuración para evadir detección
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Configuración de ventana - headless por defecto, visible solo cuando sea necesario
        if self.is_headless and not force_visible:
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            self.console.print("🔒 [dim cyan]Ejecutando en modo invisible[/dim cyan]")
        else:
            options.add_argument('--window-size=1366,768')
            options.add_argument('--start-maximized')
            self.console.print("👁️ [yellow]Ejecutando en modo visible para resolver CAPTCHA[/yellow]")
        
        # Configuración de navegador real
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-extensions-file-access-check')
        options.add_argument('--disable-extensions-http-throttling')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-default-apps')
        
        # Evitar detección de bot
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Configuración de memoria y rendimiento
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # Preferencias adicionales para comportamiento realista
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
            },
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 1,
        }
        options.add_experimental_option("prefs", prefs)

        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        # Scripts para evadir detección avanzada
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        driver.execute_script("Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})")
        
        # Configurar timeouts
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(5)
        
        return driver

    def _human_like_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Pausas más rápidas - máximo 10 segundos por página total"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _simulate_human_behavior(self):
        """Simula comportamiento humano ligero y rápido"""
        try:
            # Solo hacer scroll ocasionalmente y rápido
            if random.random() < 0.5:  # 50% probabilidad
                scroll_amount = random.randint(100, 300)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass

    def _modify_url_pagination(self, base_url: str, start: int) -> str:
        parsed = urllib.parse.urlparse(base_url)
        params = urllib.parse.parse_qs(parsed.query)
        params['start'] = [str(start)]
        new_query = urllib.parse.urlencode(params, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))

    def _extract_title_and_url(self, el, art: ArticleData):
        try:
            a = el.find_element(By.CSS_SELECTOR, '.gs_rt a')
            art.title = a.text.strip()
            art.url = a.get_attribute('href') or ''
        except NoSuchElementException:
            try:
                txt = el.find_element(By.CLASS_NAME, 'gs_rt').text
                art.title = txt.replace('[PDF]', '').replace('[HTML]', '').strip()
            except:
                pass

    def _extract_publication_info(self, el, art: ArticleData):
        try:
            meta = el.find_element(By.CLASS_NAME, 'gs_a').text
            parts = meta.split(' - ')
            art.authors = parts[0].strip()
            if len(parts) > 1:
                venue_year = parts[1]
                m = re.search(r'\b(19|20)\d{2}\b', venue_year)
                if m:
                    art.year = m.group(0)
                    art.venue = venue_year.replace(m.group(0), '').strip(' ,')
                else:
                    art.venue = venue_year
        except NoSuchElementException:
            pass

    def _extract_citations(self, el, art: ArticleData):
        try:
            c = el.find_element(By.XPATH, ".//a[contains(text(),'Citado por') or contains(text(),'Cited by')]")
            num = re.search(r'\d+', c.text)
            if num:
                art.citations = int(num.group())
        except Exception:
            pass

    def _extract_abstract(self, el, art: ArticleData):
        try:
            art.abstract = el.find_element(By.CLASS_NAME, 'gs_rs').text.strip()
        except NoSuchElementException:
            pass

    def _extract_article(self, el) -> Optional[ArticleData]:
        art = ArticleData()
        self._extract_title_and_url(el, art)
        if not art.title:
            return None
        self._extract_publication_info(el, art)
        self._extract_citations(el, art)
        self._extract_abstract(el, art)
        return art

    def _check_block(self) -> bool:
        """Detección mejorada de bloqueos"""
        src = self.driver.page_source.lower()
        title = self.driver.title.lower()
        url = self.driver.current_url.lower()
        
        # Indicadores específicos de bloqueo
        specific_block_phrases = [
            'unusual traffic from your computer',
            'automated queries',
            'suspicious activity',
            'please show you\'re not a robot',
            'verify you are not a robot',
            'our systems have detected unusual traffic',
            'this page appears when google automatically detects',
            'we can\'t take you to this page',
            'access denied',
            'blocked',
            'rate limit exceeded',
            'too many requests'
        ]
        
        # Verificar frases específicas de bloqueo
        for phrase in specific_block_phrases:
            if phrase in src:
                return True
        
        # Verificar si estamos en una página de CAPTCHA por URL
        captcha_urls = ['sorry/index', 'recaptcha', 'captcha', 'ipv4_blocked']
        for captcha_url in captcha_urls:
            if captcha_url in url:
                return True
        
        # Verificar títulos específicos de bloqueo
        block_titles = ['blocked', 'access denied', 'unusual traffic', 'captcha', 'error']
        for block_title in block_titles:
            if block_title in title and 'scholar' not in title:
                return True
        
        # Verificar elementos de CAPTCHA
        try:
            captcha_elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'captcha') or contains(@id, 'captcha') or contains(@class, 'recaptcha')]")
            if captcha_elements:
                return True
        except:
            pass
        
        return False

    def _handle_captcha_block(self, url: str) -> bool:
        """Maneja bloqueos abriendo ventana visible para resolver CAPTCHA"""
        self.console.print("🚫 [red]BLOQUEO DETECTADO - Abriendo ventana visible para resolver CAPTCHA[/red]")
        
        # Cerrar driver actual
        if self.driver:
            self.driver.quit()
        
        # Crear nuevo driver en modo visible
        self.driver = self._configure_driver(force_visible=True)
        
        try:
            self.driver.get(url)
            self.console.print("🔓 [yellow]RESUELVE EL CAPTCHA MANUALMENTE Y PRESIONA ENTER CUANDO TERMINES...[/yellow]")
            input("Presiona Enter cuando hayas resuelto el CAPTCHA: ")
            
            # Verificar si el CAPTCHA fue resuelto
            if not self._check_block():
                self.console.print("✅ [green]CAPTCHA resuelto exitosamente[/green]")
                
                # Cerrar driver visible y volver a modo headless
                self.driver.quit()
                self.driver = self._configure_driver(force_visible=False)
                self.captcha_resolved = True
                return True
            else:
                self.console.print("❌ [red]CAPTCHA no resuelto correctamente[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"❌ [red]Error manejando CAPTCHA: {e}[/red]")
            return False

    def _navigate_to_page(self, url: str, max_retries: int = 3) -> bool:
        """Navegación optimizada con manejo de CAPTCHA"""
        for attempt in range(max_retries):
            try:
                # Pequeña pausa antes de navegar
                if attempt > 0:
                    self._human_like_delay(1, 2)
                
                self.driver.get(url)
                
                # Esperar a que la página cargue
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Verificar bloqueos
                if self._check_block():
                    if not self.captcha_resolved:
                        success = self._handle_captcha_block(url)
                        if success:
                            # Intentar navegar de nuevo después de resolver CAPTCHA
                            self.driver.get(url)
                            WebDriverWait(self.driver, 15).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                            if not self._check_block():
                                self._simulate_human_behavior()
                                return True
                        else:
                            raise Exception('No se pudo resolver el CAPTCHA')
                    else:
                        raise Exception('Bloqueo persistente después de resolver CAPTCHA')
                
                # Esperar por contenido específico de Scholar
                WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.gs_r, .gs_ri')),
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'did not match') or contains(text(), 'no results')]")),
                        EC.presence_of_element_located((By.ID, "gs_hdr_tsi"))
                    )
                )
                
                # Simular comportamiento humano ligero
                self._simulate_human_behavior()
                return True
                
            except Exception as e:
                if attempt + 1 < max_retries:
                    wait_time = random.uniform(3, 6)
                    self.console.print(f"⚠️ [yellow]Reintento {attempt+1} en {wait_time:.1f}s[/yellow]")
                    time.sleep(wait_time)
                else:
                    self.console.print(f"❌ [red]Falló navegación: {str(e)[:50]}[/red]")
                    return False
        
        return False

    def scrape_articles(
        self,
        query: str,
        max_results: int = 1000,
        project_name: str = 'prismatic-search',
        max_retries: int = 3,
        idioma: str = 'en'
    ) -> List[Dict[str, Any]]:
        
        # URL base con parámetros mejorados
        base = (
            f"https://scholar.google.com/scholar?"
            f"q={urllib.parse.quote(query)}&"
            f"hl={idioma}&"
            f"as_sdt=0,5&"
            f"as_vis=1"
        )
        
        total_pages = (max_results + self.results_per_page - 1) // self.results_per_page
        collected: List[ArticleData] = []

        # Header bonito
        self.console.print("\n" + "="*80, style="bright_blue")
        self.console.print("🎓 GOOGLE SCHOLAR SCRAPER", style="bold bright_blue", justify="center")
        self.console.print("="*80, style="bright_blue")
        
        # Información de la búsqueda
        search_table = Table(box=box.ROUNDED, show_header=False)
        search_table.add_column("Campo", style="cyan", width=15)
        search_table.add_column("Valor", style="white")
        search_table.add_row("🔍 Query", f"[green]{query}[/green]")
        search_table.add_row("📊 Max Resultados", f"[yellow]{max_results}[/yellow]")
        search_table.add_row("📄 Páginas", f"[magenta]{total_pages}[/magenta]")
        search_table.add_row("🌐 Idioma", f"[blue]{idioma}[/blue]")
        
        self.console.print(search_table)
        
        try:
            self.driver = self._configure_driver()
            
            # Visitar Google Scholar homepage primero
            self.console.print("\n🌐 [cyan]Iniciando navegador y visitando Google Scholar...[/cyan]")
            self.driver.get("https://scholar.google.com/")
            self._human_like_delay(1, 2)
            
            # Progress bar con rich
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TextColumn("•"),
                TextColumn("[cyan]{task.fields[articles]}[/cyan] artículos"),
                TimeElapsedColumn(),
                console=self.console,
                expand=True
            ) as progress:
                
                task = progress.add_task(
                    "📚 Scrapeando páginas...", 
                    total=total_pages,
                    articles=0
                )
                
                consecutive_failures = 0
                
                for page_num in range(total_pages):
                    if len(collected) >= max_results:
                        break
                    
                    start_idx = page_num * self.results_per_page
                    url = self._modify_url_pagination(base, start_idx)
                    
                    success = self._navigate_to_page(url, max_retries)
                    
                    if not success:
                        consecutive_failures += 1
                        progress.console.print(f"❌ [red]Falla en página {page_num + 1}[/red]")
                        
                        if consecutive_failures >= 3:
                            progress.console.print("🛑 [bold red]Demasiadas fallas consecutivas, deteniendo...[/bold red]")
                            break
                        progress.advance(task)
                        continue
                    
                    consecutive_failures = 0
                    
                    try:
                        # Extraer artículos
                        elements = self.driver.find_elements(By.CSS_SELECTOR, '.gs_r.gs_or.gs_scl, .gs_r')
                        page_articles = 0
                        
                        if len(elements) == 0:
                            # Verificar si hay mensaje de "sin resultados"
                            no_results = self.driver.find_elements(By.XPATH, 
                                "//*[contains(text(), 'did not match') or contains(text(), 'no results') or contains(text(), 'Try different keywords')]")
                            if no_results:
                                progress.console.print(f'ℹ️ [blue]Página {page_num + 1}: Sin más resultados[/blue]')
                                break
                            else:
                                progress.console.print(f'⚠️ [yellow]Página {page_num + 1}: No se encontraron artículos[/yellow]')
                                progress.advance(task)
                                continue
                        
                        for el in elements[:max_results - len(collected)]:
                            article = self._extract_article(el)
                            if article:
                                collected.append(article)
                                page_articles += 1
                        
                        # Actualizar progress
                        progress.update(task, articles=len(collected))
                        progress.console.print(f'✅ [green]Página {page_num + 1}:[/green] {page_articles} artículos ([cyan]{len(collected)} total[/cyan])')
                        
                        # Pausa optimizada entre páginas - máximo 10 segundos total por página
                        if page_num < total_pages - 1:
                            self._human_like_delay(2, 4)  # Pausa entre 2-4 segundos
                        
                    except Exception as e:
                        progress.console.print(f'❌ [red]Error página {page_num + 1}:[/red] {str(e)[:50]}...')
                    
                    progress.advance(task)
            
        except Exception as e:
            self.console.print(f'💥 [bold red]Error general:[/bold red] {e}')
        finally:
            if self.driver:
                self.driver.quit()
                self.console.print("🔒 [dim]Navegador cerrado[/dim]")
        
        # Mostrar resumen final
        self._show_final_summary(collected, query, project_name)
        
        # Guardar resultados
        if collected:
            try:
                save_csv(project_name, 'google', [a.to_dict() for a in collected])
                self.console.print(f'💾 [bold green]Guardados exitosamente {len(collected)} artículos[/bold green]')
            except Exception as e:
                self.console.print(f'❌ [red]Error guardando:[/red] {e}')
        else:
            self.console.print('⚠️ [yellow]No se recolectaron artículos[/yellow]')
        
        return [a.to_dict() for a in collected]

    def _show_final_summary(self, collected: List[ArticleData], query: str, project_name: str):
        """Muestra resumen final bonito"""
        self.console.print("\n" + "="*80, style="bright_green")
        self.console.print("📊 RESUMEN FINAL", style="bold bright_green", justify="center")
        self.console.print("="*80, style="bright_green")
        
        if not collected:
            self.console.print(Panel("❌ No se encontraron artículos", style="red"))
            return
        
        # Estadísticas
        total_citations = sum(a.citations for a in collected)
        years = [int(a.year) for a in collected if a.year.isdigit()]
        avg_year = sum(years) / len(years) if years else 0
        
        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("📊 Estadística", style="cyan", width=20)
        summary_table.add_column("Valor", style="white", width=15)
        summary_table.add_column("Detalle", style="dim")
        
        summary_table.add_row("🎯 Query", f"[green]{len(collected)}[/green]", query[:50] + "..." if len(query) > 50 else query)
        summary_table.add_row("📚 Artículos", f"[yellow]{len(collected)}[/yellow]", "artículos únicos")
        summary_table.add_row("📈 Citas totales", f"[magenta]{total_citations:,}[/magenta]", f"promedio: {total_citations/len(collected):.1f}")
        summary_table.add_row("📅 Año promedio", f"[blue]{avg_year:.0f}[/blue]", f"rango: {min(years) if years else 'N/A'}-{max(years) if years else 'N/A'}")
        
        self.console.print(summary_table)
        
        # Top 3 más citados
        if collected:
            top_cited = sorted(collected, key=lambda x: x.citations, reverse=True)[:3]
            self.console.print("\n🏆 [bold yellow]TOP 3 MÁS CITADOS:[/bold yellow]")
            for i, article in enumerate(top_cited, 1):
                title_short = article.title[:60] + "..." if len(article.title) > 60 else article.title
                self.console.print(f"  {i}. [cyan]{title_short}[/cyan] ([yellow]{article.citations}[/yellow] citas)")


def download_google_scholar_articles(
    query: str,
    max_results: int = 1000,
    project_name: str = 'prismatic-search',
    max_retries: int = 3,
    idioma: str = 'en'
) -> List[Dict[str, Any]]:
    """
    Wrapper optimizado para scraping de Google Scholar.
    Ejecuta en modo headless por defecto, solo abre ventana visible para resolver CAPTCHAs.
    
    Args:
        query: Término de búsqueda
        max_results: Número máximo de resultados
        project_name: Nombre del proyecto para guardar archivos
        max_retries: Número máximo de reintentos por página
        idioma: Idioma de búsqueda ('en', 'es', etc.)
    
    Returns:
        Lista de diccionarios con datos de artículos
    """
    scraper = GoogleScholarScraper()
    return scraper.scrape_articles(query, max_results, project_name, max_retries, idioma)