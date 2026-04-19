import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import pandas as pd
import time

def estrai_prezzi_xenios(url_sitemap):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"--- Scansione Xenios: {url_sitemap} ---")
    
    # 1. Recupero i link dalla sitemap
    r = requests.get(url_sitemap, headers=headers)
    root = ET.fromstring(r.content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    links = [loc.text for loc in root.findall('ns:url/ns:loc', namespace)]
    
    # Filtriamo solo i link che contengono prodotti (escludendo CMS, login, etc.)
    # Spesso su Xenios i prodotti hanno percorsi specifici o nomi lunghi
    prodotti = []
    
    for link in links[:15]: # Test sui primi 15 link
        try:
            print(f"Verifica: {link}")
            res = requests.get(link, headers=headers)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # Recupero Nome
            nome = soup.find('h1', class_='h1').get_text(strip=True) if soup.find('h1', class_='h1') else "N/A"
            
            # Recupero Prezzo (Xenios usa spesso gli 'itemprop' per i dati strutturati)
            prezzo_tag = soup.find('span', itemprop='price')
            if not prezzo_tag:
                prezzo_tag = soup.find('div', class_='current-price') # Alternativa
            
            prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "N/A"
            
            prodotti.append({
                'Nome': nome,
                'Prezzo': prezzo,
                'Sito': 'Xenios USA',
                'Link': link
            })
            
            time.sleep(1.5) # Ritardo leggermente maggiore per cortesia
            
        except Exception as e:
            continue

    df = pd.DataFrame(prodotti)
    df.to_csv('prezzi_xenios.csv', index=False)
    print("\n--- Completato! Creato file 'prezzi_xenios.csv' ---")
    print(df)

# Esempio per la sitemap prodotti (verifica l'URL esatto nel loro robots.txt)
URL_XENIOS = "https://xeniosusa.com" 
estrai_prezzi_xenios(URL_XENIOS)
