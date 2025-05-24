import re
import requests
from bs4 import BeautifulSoup

def count_google_scholar_articles_simple(query):
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

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    result_div = soup.find("div", id="gs_ab_md")
    if result_div:
        match = re.search(r'([\d.,]+)', result_div.get_text())
        if match:
            count_str = match.group(1).replace(',', '').replace('.', '')
            try:
                return int(count_str)
            except ValueError:
                return 0
    return 0
