import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

# ── Categorie Lacertosus ───────────────────────────────────────────────────────
LACERTOSUS_BASE = "https://www.lacertosus.com"
LACERTOSUS_CATEGORIE = [
    ("Power Racks",       "/it/219-rack-da-palestra-home-gym-pro-power-racks"),
    ("Half Racks",        "/it/56-half-racks-stand"),
    ("Foldable Racks",    "/it/232-foldable-racks"),
    ("Elite Rigs",        "/it/26-elite-rigs"),
    ("Panche",            "/it/18-panche"),
    ("Pavimento",         "/it/19-pavimento-gommato"),
    ("Manubri Kettlebell","/it/15-manubri-palestra-home-gym-regolabili-esagonali-gomma-caricabili"),
    ("Dischi Bilancieri", "/it/14-dischi-palestra-pesi-bilancieri-bumper-home-gym"),
    ("Isotonici",         "/it/68-attrezzi-isotonici"),
    ("Cardio",            "/it/21-attrezzi-cardio"),
    ("Corpo Libero",      "/it/142-allenamento-a-corpo-libero"),
    ("Accessori",         "/it/67-accessories-and-clothing-lacertosus"),
]

# ── Categorie Kingsbox ─────────────────────────────────────────────────────────
KINGSBOX_BASE = "https://kingsbox.com"
KINGSBOX_CATEGORIE = [
    ("Bilancieri e Dischi",   "/it-it/category/strength"),
    ("Dischi",                "/it-it/category/strength/plates"),
    ("Dischi Micro",          "/it-it/category/strength/plates/micro-loads"),
    ("Rigs e Rack",           "/it-it/category/rigs-racks"),
    ("Rigs Freestanding",     "/it-it/category/rigs-racks/freestanding"),
    ("Accessori Rack",        "/it-it/category/rigs-racks/accessories"),
    ("Corpo Libero",          "/it-it/category/body-weight"),
    ("Conditioning",          "/it-it/category/conditioning"),
    ("Pesi Indossabili",      "/it-it/category/conditioning/vests"),
    ("Pavimento",             "/it-it/category/gym-essentials/flooring"),
    ("Tappeti",               "/it-it/category/gym-essentials/mats"),
    ("Macchine",              "/it-it/category/strength-machines"),
    ("Pulegge",               "/it-it/category/strength-machines/pulley-systems"),
    ("Plate Loaded",          "/it-it/category/strength-machines/plate-loaded-machines"),
    ("Accessori",             "/it-it/category/accessories"),
    ("Set",                   "/it-it/category/sets"),
    ("Home Gym Set",          "/it-it/category/sets/home-gym"),
]


def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.content, 'html.parser')


# ── Lacertosus ────────────────────────────────────────────────────────────────

def scrapa_categoria_lacertosus(nome_cat, path):
    url = LACERTOSUS_BASE + path
    print(f"  Categoria: {nome_cat} → {url}")
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"    [WARN] {e}")
        return []

    cards = soup.select('.product-miniature')

    # Se non ci sono prodotti diretti, cerca sottocategorie e seguile
    if not cards:
        sub_links = [
            a['href'] for a in soup.select('a[href]')
            if LACERTOSUS_BASE in a.get('href', '')
            and '/it/' in a['href']
            and not a['href'].endswith('.html')
            and a['href'] != url
        ]
        sub_links = list(dict.fromkeys(sub_links))  # deduplica
        print(f"    → Trovate {len(sub_links)} sottocategorie")
        prodotti = []
        for sub_url in sub_links:
            prodotti += scrapa_prodotti_lacertosus(nome_cat, sub_url)
            time.sleep(0.5)
        return prodotti

    return estrai_prodotti_lacertosus(nome_cat, cards)


def scrapa_prodotti_lacertosus(nome_cat, url):
    try:
        soup = get_soup(url)
        cards = soup.select('.product-miniature')
        return estrai_prodotti_lacertosus(nome_cat, cards)
    except Exception as e:
        print(f"    [WARN] {url}: {e}")
        return []


def estrai_prodotti_lacertosus(nome_cat, cards):
    prodotti = []
    for card in cards:
        try:
            a = card.select_one('.product-title a') or card.select_one('a[href$=".html"]')
            nome = a.get_text(strip=True) if a else "N/A"
            link = a['href'] if a else "N/A"
            prezzo_el = card.select_one('.price')
            prezzo = prezzo_el.get_text(strip=True) if prezzo_el else "N/A"
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


def scrapa_lacertosus():
    print("\n=== Scraping: Lacertosus ===")
    tutti = []
    for nome_cat, path in LACERTOSUS_CATEGORIE:
        prodotti = scrapa_categoria_lacertosus(nome_cat, path)
        print(f"    → {len(prodotti)} prodotti")
        tutti += prodotti
        time.sleep(1)
    return tutti


# ── Kingsbox ──────────────────────────────────────────────────────────────────

def scrapa_categoria_kingsbox(nome_cat, path):
    url = KINGSBOX_BASE + path
    print(f"  Categoria: {nome_cat} → {url}")
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"    [WARN] {e}")
        return []

    prodotti = []
    # I prodotti hanno link che contengono /product/
    links_prodotto = soup.select('a[href*="/product/"]')
    visti = set()

    for a in links_prodotto:
        href = a.get('href', '')
        if not href or href in visti:
            continue
        visti.add(href)

        # URL relativo → assoluto
        link = href if href.startswith('http') else KINGSBOX_BASE + href

        # Nome: testo del link oppure attributo title
        nome = a.get_text(strip=True) or a.get('title', 'N/A')
        if not nome or len(nome) < 2:
            continue

        # Prezzo: cerca nel contenitore padre del link
        prezzo = "N/A"
        parent = a.parent
        for _ in range(5):  # risali fino a 5 livelli
            if parent is None:
                break
            price_el = parent.select_one('[class*="price"]')
            if price_el:
                prezzo = price_el.get_text(strip=True)
                break
            parent = parent.parent

        prodotti.append({
            'Brand': 'Kingsbox',
            'Categoria': nome_cat,
            'Nome': nome,
            'Prezzo': prezzo,
            'Link': link,
        })

    return prodotti


def scrapa_kingsbox():
    print("\n=== Scraping: Kingsbox ===")
    tutti = []
    visti_link = set()

    for nome_cat, path in KINGSBOX_CATEGORIE:
        prodotti = scrapa_categoria_kingsbox(nome_cat, path)
        # Deduplica globale per URL prodotto
        nuovi = [p for p in prodotti if p['Link'] not in visti_link]
        for p in nuovi:
            visti_link.add(p['Link'])
        print(f"    → {len(nuovi)} prodotti nuovi ({len(prodotti) - len(nuovi)} duplicati rimossi)")
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

    # Rimuove duplicati per link all'interno dello stesso brand
    df = df.drop_duplicates(subset=['Brand', 'Link'])
    df = df.sort_values(['Brand', 'Categoria', 'Nome']).reset_index(drop=True)

    df.to_csv('prezzi.csv', index=False, encoding='utf-8')

    if not df.empty:
        print(f"\n[OK] Salvati {len(df)} prodotti in prezzi.csv")
        print(df.groupby(['Brand', 'Categoria']).size().to_string())
    else:
        print("\n[WARN] Nessun prodotto trovato. File prezzi.csv creato vuoto.")
