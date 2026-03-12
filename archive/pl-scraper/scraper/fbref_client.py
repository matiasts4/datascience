import os
import io
import time
import json
import re
from loguru import logger
import pandas as pd
from lxml import html, etree
import soccerdata.fbref
from soccerdata._common import BaseRequestsReader
import soccerdata as sd
from config import LEAGUE
from dotenv import load_dotenv
from scraper.browser_client import BrowserClient

load_dotenv()

# MONKEY PATCH: Override soccerdata's download method to use our undetected-chromedriver
def _download_and_save_with_browser(
    self,
    url: str,
    filepath=None,
    var=None,
):
    """Download file at url to filepath using a real browser to bypass Cloudflare. Overwrites if filepath exists."""
    for i in range(5):
        try:
            # Let undetected-chromedriver do the heavy lifting
            driver = BrowserClient.get_page()
            
            logger.debug(f"Página con navegador: {url}")
            driver.get(url)
            
            # Additional Cloudflare Challenge Check
            BrowserClient._wait_for_cloudflare(timeout=120)
                
            time.sleep(3) # Wait for JS to render stats tables
            
            if var is not None:
                if isinstance(var, str):
                    var = [var]
                var_names = "|".join(var)
                template_understat = rb"(%b)+[\s\t]*=[\s\t]*JSON\.parse\('(.*)'\)"
                pattern_understat = template_understat % bytes(var_names, encoding="utf-8")
                results = re.findall(pattern_understat, driver.page_source.encode('utf-8'))
                data = {
                    key.decode("unicode_escape"): json.loads(value.decode("unicode_escape"))
                    for key, value in results
                }
                payload = json.dumps(data).encode("utf-8")
            else:
                payload = driver.page_source.encode("utf-8")
            
            if not self.no_store and filepath is not None:
                # Create parent dirs if they don't exist
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with filepath.open(mode="wb") as fh:
                    fh.write(payload)
            return io.BytesIO(payload)
            
        except Exception as e:
            logger.exception(
                "Error while scraping %s con navegador. Retrying... (attempt %d of 5). Detalles: %s",
                url,
                i + 1,
                e
            )
            time.sleep(5)
            continue

    raise ConnectionError(f"Could not download {url} incluso usando el navegador undetected-chromedriver.")

# Apply the patch to the base class used by FBref
BaseRequestsReader._download_and_save = _download_and_save_with_browser

# MONKEY PATCH 2: Override _parse_table to prevent NoneType errors on Selenium HTML
def _patched_parse_table(html_table: html.HtmlElement) -> pd.DataFrame:
    # remove icons (use .// to search inside the table only, not the whole doc)
    for elem in html_table.xpath(".//span[contains(@class, 'f-i')]"):
        parent = elem.getparent()
        if parent is not None:
            etree.strip_elements(parent, "span", with_tail=False)
    # remove sep rows
    for elem in html_table.xpath(".//tbody/tr[contains(@class, 'spacer')]"):
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)
    # remove thead rows in the table body
    for elem in html_table.xpath(".//tbody/tr[contains(@class, 'thead')]"):
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)
    # parse HTML to dataframe
    (df_table,) = pd.read_html(html.tostring(html_table), flavor="lxml")
    return df_table.convert_dtypes()

soccerdata.fbref._parse_table = _patched_parse_table

def get_fbref(season: int):
    # We don't necessarily need injecting these anymore since the real browser handles state,
    # but we can leave it mapping just in case sd tries to use it somewhere else.
    cookie = os.getenv("STATHEAD_COOKIE")
    ua = os.getenv("STATHEAD_USER_AGENT")
    
    if cookie:
        soccerdata.fbref.FBREF_HEADERS["Cookie"] = cookie
    if ua:
        soccerdata.fbref.FBREF_HEADERS["User-Agent"] = ua

    return sd.FBref(
        leagues=LEAGUE,
        seasons=[season]
    )
