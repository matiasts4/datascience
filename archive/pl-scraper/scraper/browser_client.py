import time
from seleniumbase import Driver
from loguru import logger

class BrowserClient:
    _instance = None
    _driver = None

    @classmethod
    def get_page(cls):
        """Returns a singleton, reusable SeleniumBase driver instance."""
        if cls._driver is None:
            logger.info("Iniciando navegador con SeleniumBase (Anti-Detect)...")
            
            # SeleniumBase Driver with undetected-chromedriver mode (uc=True)
            # headless=False so the user can see it and solve any captchas
            cls._driver = Driver(uc=True, headless=False)
            
            logger.info("Navegando a FBref para establecer la sesión...")
            cls._driver.get("https://fbref.com")
            
            # Wait for Cloudflare challenge to pass
            cls._wait_for_cloudflare()
            
        return cls._driver

    @classmethod
    def _wait_for_cloudflare(cls, timeout=120):
        """Waits until the Cloudflare 'Just a moment...' text disappears."""
        logger.info("Detectando si hay desafío de Cloudflare...")
        time.sleep(2)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            title = cls._driver.title.lower()
            page_src = cls._driver.page_source.lower()
            
            if "just a moment" not in title and "cloudflare" not in title and "enable javascript" not in page_src and "challenge" not in title:
                logger.success("Cloudflare limpio. Procediendo con el scraping.")
                return True
                
            logger.warning("Desafío de Cloudflare activo. Por favor resuélvelo manualmente en la ventana si solicita hacer clic...")
            time.sleep(5)
            
        logger.error("Se agotó el tiempo esperando resolver Cloudflare (2 min).")
        return False

    @classmethod
    def close(cls):
        """Properly close the browser instance."""
        if cls._driver:
            cls._driver.quit()
            cls._driver = None


def get_html_with_browser(url: str, max_retries: int = 3) -> bytes:
    """
    Given a URL, loads it through the persistent SeleniumBase browser,
    waits for it to render (and bypasses Cloudflare challenge if needed),
    and returns the raw HTML source code as bytes.
    """
    driver = BrowserClient.get_page()
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Página: {url}")
            driver.get(url)
            
            BrowserClient._wait_for_cloudflare(timeout=120)
            
            # Wait a bit for JS to render stats tables fully
            time.sleep(3) 
            
            html_content = driver.page_source
            return html_content.encode("utf-8")
            
        except Exception as e:
            logger.warning(f"Error cargando {url} (Intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise ConnectionError(f"No se pudo cargar la URL después de {max_retries} intentos: {url}")
