import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import pandas as pd
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
NS = {'n': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
LIMIT = 5


def fetch_xml(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return ET.fromstring(r.content)


def get_product_links(sitemap_url, keyword='product'):
    """
    Gestisce sia sitemap normali (<urlset>) sia sitemap index (<sitemapindex>).
    Se trova un index, cerca la sub-sitemap che contiene 'keyword' nel nome.
    """
    print(f"[INFO] Scarico sitemap: {sitemap_url}")
    try:
        root = fetch_xml(sitemap_url)
    except Exception as e:
        print(f"[WARN] Impossibile scaricare sitemap ({sitemap_url}): {e}")
        return []

    tag = root.tag.split('}')[-1]  # rimuove il namespace dal tag

    # Sitemap index: contiene altre sitemap
    if tag == 'sitemapindex':
        sub_sitemaps = [loc.text for loc in root.findall('n:sitemap/n:loc', NS)]
        print(f"[INFO] Sitemap index trovata, sub-sitemap: {sub_sitemaps}")

        # Preferisce quella con 'product' nel nome, altrimenti prende la prima
        target = next((s for s in sub_sitemaps if keyword in s.lower()), None)
        if not target and sub_sitemaps:
            target = sub_sitemaps[0]
        if not target:
            print("[WARN] Nessuna sub-sitemap trovata.")
            return []

        print(f"[INFO] Uso sub-sitemap: {target}")
        try:
            root = fetch_xml(target)
        except Exception as e:
            print(f"[WARN] Impossibile scaricare sub-sitemap ({target}): {e}")
            return []

    # Sitemap normale: contiene URL diretti
    links = [loc.text for loc in root.findall('n:url/n:loc', NS)]
    print(f"[INFO] Trovati {len(links)} link.")
    return links


def estrai_prezzo_lacertosus(soup):
    meta = soup.find('meta', property='product:price:amount')
    if meta and meta.get('content'):
        return meta['content']
    return "N/A"


def estrai_prezzo_xenios(soup):
    candidati = [
        soup.find('span', itemprop='price'),
        soup.find('div', class_='current-price'),
        soup.find('span', class_='price'),
    ]
    for el in candidati:
        if el:
            return el.get_text(strip=True)
    return "N/A"


def scrapa_brand(sitemap_url, brand, estrai_prezzo_fn):
    print(f"\n=== Scraping: {brand} ===")
    links = get_product_links(sitemap_url)

    if not links:
        print(f"[WARN] {brand}: nessun link trovato, salto.")
        return []

    prodotti = []
    for link in links[:LIMIT]:
        try:
            res = requests.get(link, headers=HEADERS, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'html.parser')
            h1 = soup.find('h1')
            nome = h1.get_text(strip=True) if h1 else "N/A"
            prezzo = estrai_prezzo_fn(soup)
            prodotti.append({'Brand': brand, 'Nome': nome, 'Prezzo': prezzo, 'Link': link})
            print(f"  OK  {nome[:60]} — {prezzo}")
            time.sleep(1)
        except Exception as e:
            print(f"  ERR {link}: {e}")
            continue

    return prodotti


if __name__ == "__main__":
    lacertosus_sitemap = "https://lacertosus.com/sitemap.xml"
    xenios_sitemap = "https://www.xeniosusa.com/sitemap.xml"

    dati = []
    dati += scrapa_brand(lacertosus_sitemap, "Lacertosus", estrai_prezzo_lacertosus)
    dati += scrapa_brand(xenios_sitemap, "Xenios USA", estrai_prezzo_xenios)

    colonne = ['Brand', 'Nome', 'Prezzo', 'Link']
    df = pd.DataFrame(dati if dati else [], columns=colonne)
    df.to_csv('prezzi.csv', index=False, encoding='utf-8')

    if dati:
        print(f"\n[OK] Salvati {len(dati)} prodotti in prezzi.csv")
    else:
        print("\n[WARN] Nessun prodotto trovato. File prezzi.csv creato vuoto.")
