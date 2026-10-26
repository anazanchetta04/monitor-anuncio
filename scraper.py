import os
import json
import re
import requests
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL_BUSCA = 'https://www.olx.com.br/brasil?q=sylvanian&sf=1'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8828380541:AAE15iMNiSbXSE5UBrdPFegFJMbPp-9253s')
CHAT_ID = os.getenv('CHAT_ID', '361561144')
ARQUIVO_IDS = 'anuncios_vistos.json'

def carregar_vistos():
    if os.path.exists(ARQUIVO_IDS):
        with open(ARQUIVO_IDS, 'r') as f:
            return set(json.load(f))
    return set()

def salvar_vistos(vistos):
    with open(ARQUIVO_IDS, 'w') as f:
        json.dump(list(vistos), f)

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mensagem, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def raspar_olx():
    print("A iniciar o navegador...")
    
    with sync_playwright() as p:
        # Mantemos False para burlar o Cloudflare da OLX
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("A aceder à OLX...")
            page.goto(URL_BUSCA, wait_until='domcontentloaded', timeout=60000)
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            vistos = carregar_vistos()
            novos_anuncios = []

            for a in soup.find_all('a', href=True):
                link = a['href']
                if 'olx.com.br' in link and re.search(r'-\d+$', link):
                    id_anuncio = link.split('-')[-1]
                    
                    if id_anuncio not in vistos:
                        h2 = a.find('h2')
                        titulo = h2.text.strip() if h2 else 'Novo Anúncio Encontrado'
                        
                        if not any(id_anuncio == item[0] for item in novos_anuncios):
                            novos_anuncios.append((id_anuncio, titulo, link))
                            vistos.add(id_anuncio)

            for id_anuncio, titulo, link in novos_anuncios:
                mensagem = f"<b>Novo item na OLX!</b>\n\n{titulo}\n<a href='{link}'>Acessar anúncio</a>"
                enviar_telegram(mensagem)
                time.sleep(2) # Pausa obrigatória do Telegram

            salvar_vistos(vistos)
            print(f"Execução concluída: {len(novos_anuncios)} novos anúncios encontrados e enviados.")
            
        except Exception as e:
            print(f"Ocorreu um erro ao processar a página: {e}")
        finally:
            browser.close()

if __name__ == '__main__':
    raspar_olx()