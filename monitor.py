import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import pandas as pd
import time

def estrai_dati(url_sitemap, brand):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    prodotti = []
    
    try:
        print(f"--- Scansione {brand}: {url_sitemap} ---")
        r = requests.get(url_sitemap, headers=headers, timeout=10)
        root = ET.fromstring(r.content)
        namespace = {'ns': 'http://sitemaps.org'}
        links = [loc.text for loc in root.findall('ns:url/ns:loc', namespace)]
        
        # Testiamo i primi 10 link per ogni brand per evitare blocchi o tempi lunghi su GitHub
        for link in links[:10]:
            try:
                print(f"Analizzo {brand}: {link}")
                res = requests.get(link, headers=headers, timeout=10)
                soup = BeautifulSoup(res.content, 'html.parser')
                
                nome = "N/A"
                prezzo = "N/A"
                
                if brand == "Lacertosus":
                    nome = soup.find('h1').get_text(strip=True) if soup.find('h1') else "N/A"
                    prezzo_meta = soup.find('meta', property='product:price:amount')
                    prezzo = prezzo_meta['content'] if prezzo_meta else "N/A"
                
                elif brand == "Xenios":
                    nome = soup.find('h1').get_text(strip=True) if soup.find('h1') else "N/A"
                    prezzo_tag = soup.find('span', itemprop='price')
                    if not prezzo_tag:
                        prezzo_tag = soup.find('div', class_='current-price')
                    prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "N/A"
                
                prodotti.append({
                    'Brand': brand,
                    'Nome': nome,
                    'Prezzo': prezzo,
                    'Link': link,
                    'Data': time.strftime("%Y-%m-%d")
                })
                time.sleep(1) # Rispetto per il server
                
            except Exception as e:
                print(f"Errore sul link {link}: {e}")
                continue
                
    except Exception as e:
        print(f"Errore durante la lettura della sitemap di {brand}: {e}")
    
    return prodotti

if __name__ == "__main__":
    # Liste sitemap corrette
    sitemap_lacertosus = "https://lacertosus.com"
    sitemap_xenios = "https://xeniosusa.com"
    
    # Esecuzione estrazioni
    dati_lacertosus = estrai_dati(sitemap_lacertosus, "Lacertosus")
    dati_xenios = estrai_dati(sitemap_xenios, "Xenios")
    
    # Unione e salvataggio
    totale = dati_lacertosus + dati_xenios
    if totale:
        df = pd.DataFrame(totale)
        df.to_csv('prezzi.csv', index=False, encoding='utf-8')
        print(f"\n✅ Successo! Salvati {len(totale)} prodotti in prezzi.csv")
    else:
        print("\n❌ Nessun dato raccolto.")
