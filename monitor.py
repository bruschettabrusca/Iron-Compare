import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

LACERTOSUS_BASE = "https://www.lacertosus.com"
LACERTOSUS_CATEGORIE = [
    ("Power Racks",        "/it/219-rack-da-palestra-home-gym-pro-power-racks"),
    ("Half Racks",         "/it/56-half-racks-stand"),
    ("Foldable Racks",     "/it/232-foldable-racks"),
    ("Elite Rigs",         "/it/26-elite-rigs"),
    ("Panche",             "/it/18-panche"),
    ("Pavimento",          "/it/19-pavimento-gommato"),
    ("Manubri Kettlebell", "/it/15-manubri-palestra-home-gym-regolabili-esagonali-gomma-caricabili"),
    ("Dischi Bilancieri",  "/it/14-dischi-palestra-pesi-bilancieri-bumper-home-gym"),
    ("Isotonici",          "/it/68-attrezzi-isotonici"),
    ("Cardio",             "/it/21-attrezzi-cardio"),
    ("Corpo Libero",       "/it/142-allenamento-a-corpo-libero"),
    ("Accessori",          "/it/67-accessories-and-clothing-lacertosus"),
]

KINGSBOX_BASE = "https://kingsbox.com"
KINGSBOX_CATEGORIE = [
    ("Bilancieri e Dischi", "/it-it/category/strength"),
    ("Dischi",              "/it-it/category/strength/plates"),
    ("Dischi Micro",        "/it-it/category/strength/plates/micro-loads"),
    ("Rigs e Rack",         "/it-it/category/rigs-racks"),
    ("Rigs Freestanding",   "/it-it/category/rigs-racks/freestanding"),
    ("Accessori Rack",      "/it-it/category/rigs-racks/accessories"),
    ("Corpo Libero",        "/it-it/category/body-weight"),
    ("Conditioning",        "/it-it/category/conditioning"),
    ("Pesi Indossabili",    "/it-it/category/conditioning/vests"),
    ("Pavimento",           "/it-it/category/gym-essentials/flooring"),
    ("Tappeti",             "/it-it/category/gym-essentials/mats"),
    ("Macchine",            "/it-it/category/strength-machines"),
    ("Pulegge",             "/it-it/category/strength-machines/pulley-systems"),
    ("Plate Loaded",        "/it-it/category/strength-machines/plate-loaded-machines"),
    ("Accessori",           "/it-it/category/accessories"),
    ("Set",                 "/it-it/category/sets"),
    ("Home Gym Set",        "/it-it/category/sets/home-gym"),
]

SCONTO_RE = re.compile(r'^-?\d+\s*%$')


def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.content, 'html.parser')


def slug_to_name(url):
    """Ricava il nome del prodotto dallo slug URL come ultimo fallback."""
    slug = url.rstrip('/').split('/')[-1]
    return slug.replace('-', ' ').title()


# ── Lacertosus ────────────────────────────────────────────────────────────────

def is_product_url(href):
    return href and href.endswith('.html') and '/it/' in href

def is_subcat_url(href, current_url):
    return (
        href
        and '/it/' in href
        and not href.endswith('.html')
        and href != current_url
        and not href.endswith('/it/')
    )

def normalize_lacertosus(href):
    """Converte URL relativo in assoluto."""
    if href.startswith('http'):
        return href
    return LACERTOSUS_BASE + href


def estrai_prodotti_lacertosus_da_soup(soup, nome_cat):
    prodotti = []
    # Selettore corretto: .product-item (tema custom di Lacertosus)
    for card in soup.select('.product-item'):
        try:
            # Nome: heading con classe product-name
            nome_el = card.select_one('.product-name a') or card.select_one('h2 a') or card.select_one('a[href$=".html"]')
            nome = nome_el.get_text(strip=True) if nome_el else "N/A"
            link = normalize_lacertosus(nome_el['href']) if nome_el else "N/A"

            prezzo_el = card.select_one('.price')
            prezzo = prezzo_el.get_text(strip=True) if prezzo_el else "N/A"

            if nome == "N/A" and link == "N/A":
                continue

            prodotti.append({
                'Brand': 'Lacertosus',
                'Categoria': nome_cat,
                'Nome': nome,
                'Prezzo': prezzo,
                'Link': link,
            })
        except Exception:
            continue
    return prodotti


def scrapa_categoria_lacertosus(nome_cat, path):
    url = normalize_lacertosus(path)
    print(f"  [{nome_cat}] {url}")
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"    [WARN] {e}")
        return []

    prodotti = estrai_prodotti_lacertosus_da_soup(soup, nome_cat)

    if prodotti:
        print(f"    → {len(prodotti)} prodotti")
        return prodotti

    # Nessun prodotto diretto: cerca sottocategorie
    subcats = []
    for a in soup.select('a[href]'):
        href = a.get('href', '')
        full = normalize_lacertosus(href) if href.startswith('/') else href
        if is_subcat_url(full, url) and LACERTOSUS_BASE in full:
            if full not in subcats:
                subcats.append(full)

    if subcats:
        print(f"    → {len(subcats)} sottocategorie trovate")
        for sub_url in subcats:
            try:
                sub_soup = get_soup(sub_url)
                sub_prod = estrai_prodotti_lacertosus_da_soup(sub_soup, nome_cat)
                prodotti += sub_prod
                time.sleep(0.5)
            except Exception as e:
                print(f"    [WARN] {sub_url}: {e}")
        print(f"    → {len(prodotti)} prodotti totali")
    else:
        print(f"    → Nessun prodotto né sottocategoria trovata")

    return prodotti


def scrapa_lacertosus():
    print("\n=== Scraping: Lacertosus ===")
    tutti = []
    visti = set()
    for nome_cat, path in LACERTOSUS_CATEGORIE:
        prodotti = scrapa_categoria_lacertosus(nome_cat, path)
        nuovi = [p for p in prodotti if p['Link'] not in visti]
        for p in nuovi:
            visti.add(p['Link'])
        tutti += nuovi
        time.sleep(1)
    return tutti


# ── Kingsbox ──────────────────────────────────────────────────────────────────

def estrai_nome_kingsbox(a_tag):
    """
    Dentro il tag <a> che wrappa la card ci sono: badge sconto, immagine, nome, prezzo.
    Scarta i testi che sembrano percentuali di sconto e prende il primo testo utile.
    """
    testi = [t.strip() for t in a_tag.stripped_strings if t.strip()]
    for testo in testi:
        if not SCONTO_RE.match(testo) and len(testo) > 2:
            return testo
    # Fallback: ricava nome dallo slug URL
    return slug_to_name(a_tag.get('href', ''))


def estrai_prezzo_kingsbox(a_tag):
    """Cerca un elemento con 'price' nella classe dentro o vicino alla card."""
    price_el = a_tag.select_one('[class*="price"]')
    if price_el:
        return price_el.get_text(strip=True)
    return "N/A"


def scrapa_categoria_kingsbox(nome_cat, path):
    url = KINGSBOX_BASE + path
    print(f"  [{nome_cat}] {url}")
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"    [WARN] {e}")
        return []

    prodotti = []
    visti = set()

    for a in soup.select('a[href*="/product/"]'):
        href = a.get('href', '')
        link = href if href.startswith('http') else KINGSBOX_BASE + href
        if link in visti:
            continue
        visti.add(link)

        nome = estrai_nome_kingsbox(a)
        prezzo = estrai_prezzo_kingsbox(a)

        if not nome or nome == "N/A":
            continue

        prodotti.append({
            'Brand': 'Kingsbox',
            'Categoria': nome_cat,
            'Nome': nome,
            'Prezzo': prezzo,
            'Link': link,
        })

    print(f"    → {len(prodotti)} prodotti")
    return prodotti


def scrapa_kingsbox():
    print("\n=== Scraping: Kingsbox ===")
    tutti = []
    visti_link = set()
    for nome_cat, path in KINGSBOX_CATEGORIE:
        prodotti = scrapa_categoria_kingsbox(nome_cat, path)
        nuovi = [p for p in prodotti if p['Link'] not in visti_link]
        for p in nuovi:
            visti_link.add(p['Link'])
        rimossi = len(prodotti) - len(nuovi)
        if rimossi:
            print(f"    ({rimossi} duplicati rimossi)")
        tutti += nuovi
        time.sleep(1)
    return tutti


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dati = []
    dati += scrapa_lacertosus()
    dati += scrapa_kingsbox()

    colonne = ['Brand', 'Categoria', 'Nome', 'Prezzo', 'Link']
    df = pd.DataFrame(dati if dati else [], columns=colonne)
    df = df.drop_duplicates(subset=['Brand', 'Link'])
    df = df.sort_values(['Brand', 'Categoria', 'Nome']).reset_index(drop=True)
    df.to_csv('prezzi.csv', index=False, encoding='utf-8')

    if not df.empty:
        print(f"\n[OK] Salvati {len(df)} prodotti in prezzi.csv")
        print(df.groupby(['Brand', 'Categoria']).size().to_string())
    else:
        print("\n[WARN] Nessun prodotto trovato. File prezzi.csv creato vuoto.")
