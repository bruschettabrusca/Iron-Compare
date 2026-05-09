import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}
LIMIT = 5


def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.content, 'html.parser')


# ── Lacertosus ────────────────────────────────────────────────────────────────

def get_links_lacertosus(categoria_url):
    soup = get_soup(categoria_url)
    links = []
    for a in soup.select('.product-miniature a[href]'):
        href = a['href']
        if href not in links and href.endswith('.html'):
            links.append(href)
    return links


def estrai_prezzo_lacertosus(soup):
    # meta tag OpenGraph
    meta = soup.find('meta', property='product:price:amount')
    if meta and meta.get('content'):
        return meta['content'] + ' €'
    # JSON-LD fallback
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict) and 'offers' in data:
                return str(data['offers'].get('price', 'N/A')) + ' €'
        except Exception:
            continue
    return "N/A"


def scrapa_lacertosus(categoria_url):
    print("\n=== Scraping: Lacertosus ===")
    try:
        links = get_links_lacertosus(categoria_url)
    except Exception as e:
        print(f"[WARN] Errore categoria Lacertosus: {e}")
        return []

    print(f"[INFO] {len(links)} prodotti trovati, uso i primi {LIMIT}")
    prodotti = []
    for link in links[:LIMIT]:
        try:
            soup = get_soup(link)
            h1 = soup.find('h1')
            nome = h1.get_text(strip=True) if h1 else "N/A"
            prezzo = estrai_prezzo_lacertosus(soup)
            prodotti.append({'Brand': 'Lacertosus', 'Nome': nome, 'Prezzo': prezzo, 'Link': link})
            print(f"  OK  {nome[:60]} — {prezzo}")
            time.sleep(1)
        except Exception as e:
            print(f"  ERR {link}: {e}")
            continue
    return prodotti


# ── Fitshop ───────────────────────────────────────────────────────────────────

def get_links_fitshop(categoria_url):
    soup = get_soup(categoria_url)
    base = 'https://www.fitshop.it'
    links = []
    for a in soup.select('a[href]'):
        href = a['href']
        # I prodotti hanno slug tipo /bilanciere-nome-codice
        if href.startswith('/') and '-' in href and '?' not in href and href.count('/') == 1:
            full = base + href
            if full not in links:
                links.append(full)
    return links


def estrai_prezzo_fitshop(soup):
    # JSON-LD (source più affidabile)
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict) and 'offers' in data:
                price = data['offers'].get('price')
                currency = data['offers'].get('priceCurrency', '€')
                if price:
                    return f"{price} {currency}"
        except Exception:
            continue
    # Fallback CSS
    for sel in ['[itemprop="price"]', '.price-current', '.product-price', '.price']:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return "N/A"


def scrapa_fitshop(categoria_url):
    print("\n=== Scraping: Fitshop ===")
    try:
        links = get_links_fitshop(categoria_url)
    except Exception as e:
        print(f"[WARN] Errore categoria Fitshop: {e}")
        return []

    print(f"[INFO] {len(links)} prodotti trovati, uso i primi {LIMIT}")
    prodotti = []
    for link in links[:LIMIT]:
        try:
            soup = get_soup(link)
            h1 = soup.find('h1')
            nome = h1.get_text(strip=True) if h1 else "N/A"
            prezzo = estrai_prezzo_fitshop(soup)
            prodotti.append({'Brand': 'Fitshop', 'Nome': nome, 'Prezzo': prezzo, 'Link': link})
            print(f"  OK  {nome[:60]} — {prezzo}")
            time.sleep(1)
        except Exception as e:
            print(f"  ERR {link}: {e}")
            continue
    return prodotti


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    lacertosus_url = "https://www.lacertosus.com/it/2-bilancieri-e-dischi"
    fitshop_url = "https://www.fitshop.it/bilancieri/"

    dati = []
    dati += scrapa_lacertosus(lacertosus_url)
    dati += scrapa_fitshop(fitshop_url)

    colonne = ['Brand', 'Nome', 'Prezzo', 'Link']
    df = pd.DataFrame(dati if dati else [], columns=colonne)
    df.to_csv('prezzi.csv', index=False, encoding='utf-8')

    if dati:
        print(f"\n[OK] Salvati {len(dati)} prodotti in prezzi.csv")
    else:
        print("\n[WARN] Nessun prodotto trovato. File prezzi.csv creato vuoto.")

