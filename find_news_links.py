#!/usr/bin/env python3
"""
Script para encontrar links de notícias no rodapé de sites do gov.br
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin, urlparse
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping_log.txt'),
        logging.StreamHandler()
    ]
)

def find_news_link_in_footer(url):
    """
    Acessa uma URL e procura por links de notícias, primeiro no rodapé e depois em toda a página

    Args:
        url (str): URL do site para analisar

    Returns:
        str: URL do link de notícias encontrado ou string vazia se não encontrar
    """
    try:
        # Fazer requisição com timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse do HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # PRIMEIRA TENTATIVA: Procurar pela div do rodapé
        footer_div = soup.find('div', class_='footer-wrapper')

        if footer_div:
            # Procurar por links que contenham "Notícias" no texto
            news_links = footer_div.find_all('a', string=lambda text: text and 'notícias' in text.lower())

            if not news_links:
                # Tentar uma busca mais ampla por links que contenham a palavra
                all_links = footer_div.find_all('a')
                for link in all_links:
                    if link.text and 'notícias' in link.text.lower():
                        news_links.append(link)

            if news_links:
                # Pegar o primeiro link encontrado no rodapé
                link = news_links[0]
                href = link.get('href', '')

                if href:
                    # Converter para URL absoluta se necessário
                    if href.startswith('/'):
                        href = urljoin(url, href)
                    elif not href.startswith('http'):
                        href = urljoin(url, href)

                    logging.info(f"Link de notícias encontrado no rodapé de {url}: {href}")
                    return href
        else:
            logging.warning(f"Div footer-wrapper não encontrada em {url}")

                # SEGUNDA TENTATIVA (FALLBACK): Procurar "Mais Notícias" em toda a página
        logging.info(f"Tentando fallback: procurando 'Mais Notícias' em toda a página de {url}")

        # Procurar por links que contenham "Mais Notícias" em toda a página
        more_news_links = soup.find_all('a', string=lambda text: text and 'mais notícias' in text.lower())

        if not more_news_links:
            # Busca mais flexível por links que contenham as palavras
            all_page_links = soup.find_all('a')
            for link in all_page_links:
                if link.text and 'mais notícias' in link.text.lower().strip():
                    more_news_links.append(link)

        if more_news_links:
            # Pegar o primeiro link "Mais Notícias" encontrado
            link = more_news_links[0]
            href = link.get('href', '')

            if href:
                # Converter para URL absoluta se necessário
                if href.startswith('/'):
                    href = urljoin(url, href)
                elif not href.startswith('http'):
                    href = urljoin(url, href)

                logging.info(f"Link 'Mais Notícias' encontrado em {url}: {href}")
                return href

        # TERCEIRA TENTATIVA (FALLBACK): Procurar "Últimas Notícias" em toda a página
        logging.info(f"Tentando segundo fallback: procurando 'Últimas Notícias' em toda a página de {url}")

        # Procurar por links que contenham "Últimas Notícias" em toda a página
        latest_news_links = soup.find_all('a', string=lambda text: text and 'últimas notícias' in text.lower())

        if not latest_news_links:
            # Busca mais flexível por links que contenham as palavras
            all_page_links = soup.find_all('a')
            for link in all_page_links:
                if link.text and 'últimas notícias' in link.text.lower().strip():
                    latest_news_links.append(link)

        if latest_news_links:
            # Pegar o primeiro link "Últimas Notícias" encontrado
            link = latest_news_links[0]
            href = link.get('href', '')

            if href:
                # Converter para URL absoluta se necessário
                if href.startswith('/'):
                    href = urljoin(url, href)
                elif not href.startswith('http'):
                    href = urljoin(url, href)

                logging.info(f"Link 'Últimas Notícias' encontrado em {url}: {href}")
                return href

        logging.info(f"Nenhum link de notícias encontrado em {url} (nem no rodapé, nem 'Mais Notícias', nem 'Últimas Notícias')")
        return ""

    except requests.exceptions.Timeout:
        logging.error(f"Timeout ao acessar {url}")
        return ""
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao acessar {url}: {str(e)}")
        return ""
    except Exception as e:
        logging.error(f"Erro inesperado ao processar {url}: {str(e)}")
        return ""

def main():
    """Função principal do script"""
    input_file = 'all-govbr-sites-with-news.csv'  # Usar o arquivo já processado
    output_file = 'all-govbr-sites-with-news-final.csv'

    try:
        # Verificar se o arquivo já processado existe, senão usar o original
        if not os.path.exists(input_file):
            input_file = 'all-govbr-sites.csv'
            logging.info(f"Arquivo processado não encontrado, usando arquivo original: {input_file}")
            df = pd.read_csv(input_file)
            df['Noticias'] = ""  # Adicionar coluna vazia
        else:
            df = pd.read_csv(input_file)
            logging.info(f"Arquivo já processado carregado: {input_file}")

        logging.info(f"Arquivo carregado com {len(df)} linhas")

        # Identificar sites sem links de notícias (coluna vazia ou NaN)
        sites_sem_noticias = df[(df['Noticias'].isna()) | (df['Noticias'] == "")]

        if len(sites_sem_noticias) == 0:
            logging.info("Todos os sites já têm links de notícias!")
            return

        logging.info(f"Reprocessando {len(sites_sem_noticias)} sites sem links de notícias")

        # Processar apenas os sites sem notícias
        total_to_process = len(sites_sem_noticias)
        processed = 0

        for index, row in sites_sem_noticias.iterrows():
            url = row['Portal']
            processed += 1
            logging.info(f"Reprocessando ({processed}/{total_to_process}): {url}")

            # Encontrar link de notícias com o método melhorado
            news_link = find_news_link_in_footer(url)
            df.at[index, 'Noticias'] = news_link

            # Pausa entre requisições para não sobrecarregar os servidores
            time.sleep(2)

            # Salvar progresso a cada 5 sites processados
            if processed % 5 == 0:
                df.to_csv(output_file, index=False)
                logging.info(f"Progresso salvo: {processed} sites reprocessados")

        # Salvar resultado final
        df.to_csv(output_file, index=False)
        logging.info(f"Reprocessamento concluído! Resultado salvo em {output_file}")

        # Estatísticas finais
        news_found = len(df[df['Noticias'] != ""])
        total_urls = len(df)
        sites_ainda_sem_noticias = len(df[(df['Noticias'].isna()) | (df['Noticias'] == "")])

        logging.info(f"ESTATÍSTICAS FINAIS:")
        logging.info(f"Total de sites: {total_urls}")
        logging.info(f"Sites com links de notícias: {news_found}")
        logging.info(f"Sites ainda sem notícias: {sites_ainda_sem_noticias}")
        logging.info(f"Taxa de sucesso: {(news_found/total_urls)*100:.1f}%")

    except FileNotFoundError:
        logging.error(f"Arquivo {input_file} não encontrado!")
    except Exception as e:
        logging.error(f"Erro durante o processamento: {str(e)}")

if __name__ == "__main__":
    main()
