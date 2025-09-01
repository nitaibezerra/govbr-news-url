#!/usr/bin/env python3
"""
GovBR News URL Scraper

A robust web scraper that finds news links in Brazilian government websites.
Uses multiple fallback strategies to maximize link discovery success rate.
"""

import logging
import os
import time
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag


class NewsLinkScraper:
    """
    A web scraper for finding news links in Brazilian government websites.

    This class implements a multi-level fallback strategy:
    1. Search for "Notícias" links in the footer
    2. Search for "Mais Notícias" links throughout the page
    3. Search for "Últimas Notícias" links throughout the page
    """

    def __init__(
        self,
        request_timeout: int = 30,
        request_delay: float = 2.0,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ) -> None:
        """
        Initialize the NewsLinkScraper.

        Args:
            request_timeout: Timeout for HTTP requests in seconds
            request_delay: Delay between requests in seconds to avoid overloading servers
            user_agent: User agent string for HTTP requests
        """
        self.request_timeout = request_timeout
        self.request_delay = request_delay
        self.headers = {'User-Agent': user_agent}
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Set up logging configuration.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('govbr_news_scraper')
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if not logger.handlers:
            # File handler
            file_handler = logging.FileHandler('scraping_log.txt')
            file_handler.setLevel(logging.INFO)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Make an HTTP request and return parsed HTML.

        Args:
            url: The URL to fetch

        Returns:
            BeautifulSoup object if successful, None otherwise
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.request_timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout ao acessar {url}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao acessar {url}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao processar {url}: {str(e)}")
            return None

    def _convert_to_absolute_url(self, href: str, base_url: str) -> str:
        """
        Convert a relative URL to an absolute URL.

        Args:
            href: The href attribute value (may be relative or absolute)
            base_url: The base URL for converting relative URLs

        Returns:
            Absolute URL
        """
        if href.startswith('/'):
            return urljoin(base_url, href)
        elif not href.startswith('http'):
            return urljoin(base_url, href)
        return href

    def _find_links_by_text(self, soup: BeautifulSoup, search_text: str,
                           container: Optional[Tag] = None) -> List[Tag]:
        """
        Find links with intelligent text matching (prioritizes exact matches).

        Args:
            soup: BeautifulSoup object to search in
            search_text: Text to search for in link text
            container: Optional container to limit search scope

        Returns:
            List of link tags with prioritized matching
        """
        search_container = container or soup
        search_text_clean = search_text.lower().strip()
        all_links = search_container.find_all('a')

        exact_matches = []
        ends_with_matches = []
        starts_with_matches = []

        for link in all_links:
            if link.text:
                link_text_clean = link.text.lower().strip()

                # Priority 1: Exact match (e.g., "notícias")
                if link_text_clean == search_text_clean:
                    exact_matches.append(link)
                # Priority 2: Ends with search text (e.g., "principais notícias")
                elif link_text_clean.endswith(search_text_clean):
                    ends_with_matches.append(link)
                # Priority 3: Starts with search text (e.g., "notícias siscomex")
                elif link_text_clean.startswith(search_text_clean):
                    starts_with_matches.append(link)

        # Return in order of priority
        if exact_matches:
            return exact_matches
        elif ends_with_matches:
            return ends_with_matches
        elif starts_with_matches:
            return starts_with_matches
        else:
            return []

    def _extract_link_url(self, link: Tag, base_url: str) -> Optional[str]:
        """
        Extract and validate URL from a link tag.

        Args:
            link: BeautifulSoup link tag
            base_url: Base URL for converting relative URLs

        Returns:
            Absolute URL if valid, None otherwise
        """
        href = link.get('href', '')
        if not href:
            return None

        return self._convert_to_absolute_url(href, base_url)

    def _search_footer_news_links(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Search for news links in the footer section with intelligent selection.

        Args:
            soup: Parsed HTML content
            url: Base URL for converting relative links

        Returns:
            News link URL if found, None otherwise
        """
        footer_div = soup.find('div', class_='footer-wrapper')

        if not footer_div:
            self.logger.warning(f"Div footer-wrapper não encontrada em {url}")
            return None

        news_links = self._find_links_by_text(soup, 'notícias', footer_div)

        if news_links:
            # Se há múltiplos links, usar lógica inteligente de seleção
            if len(news_links) > 1:
                selected_link = self._select_best_news_link(news_links, url)
            else:
                selected_link = news_links[0]

            link_url = self._extract_link_url(selected_link, url)
            if link_url:
                self.logger.info(f"Link de notícias encontrado no rodapé de {url}: {link_url}")
                return link_url

        return None

    def _select_best_news_link(self, links: List[Tag], base_url: str) -> Tag:
        """
        Select the best news link from multiple options using intelligent criteria.

        Prioritizes links based on URL patterns and context:
        1. Links containing 'comunicacao' (communication-related)
        2. Links containing 'noticias' in path
        3. Shorter, more direct paths
        4. First found as fallback

        Args:
            links: List of link tags to choose from
            base_url: Base URL for analysis

        Returns:
            The best link tag
        """
        scored_links = []

        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            score = 0

            if href:
                absolute_url = self._convert_to_absolute_url(href, base_url)

                # Scoring criteria
                if 'comunicacao' in absolute_url.lower():
                    score += 100  # High priority for communication links
                if 'ultimas' in text:
                    score += 50   # Priority for "últimas notícias"
                if absolute_url.count('/') <= 6:  # Prefer shorter paths
                    score += 10
                if 'noticias' in absolute_url.lower():
                    score += 5

                scored_links.append((score, link))

        # Sort by score (highest first) and return best
        scored_links.sort(key=lambda x: x[0], reverse=True)

        if scored_links:
            best_score, best_link = scored_links[0]
            self.logger.info(f"Selecionado link com score {best_score}: {best_link.get_text(strip=True)}")
            return best_link

        # Fallback to first link if scoring fails
        return links[0]

    def _search_more_news_links(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Search for "Mais Notícias" links throughout the page.

        Args:
            soup: Parsed HTML content
            url: Base URL for converting relative links

        Returns:
            News link URL if found, None otherwise
        """
        self.logger.info(f"Tentando fallback: procurando 'Mais Notícias' em toda a página de {url}")

        more_news_links = self._find_links_by_text(soup, 'mais notícias')

        if more_news_links:
            link_url = self._extract_link_url(more_news_links[0], url)
            if link_url:
                self.logger.info(f"Link 'Mais Notícias' encontrado em {url}: {link_url}")
                return link_url

        return None

    def _search_latest_news_links(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Search for "Últimas Notícias" links throughout the page.

        Args:
            soup: Parsed HTML content
            url: Base URL for converting relative links

        Returns:
            News link URL if found, None otherwise
        """
        self.logger.info(f"Tentando segundo fallback: procurando 'Últimas Notícias' em toda a página de {url}")

        latest_news_links = self._find_links_by_text(soup, 'últimas notícias')

        if latest_news_links:
            link_url = self._extract_link_url(latest_news_links[0], url)
            if link_url:
                self.logger.info(f"Link 'Últimas Notícias' encontrado em {url}: {link_url}")
                return link_url

        return None

    def _search_generic_news_links(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Search for generic "Notícias" links throughout the page as final fallback.

        Args:
            soup: Parsed HTML content
            url: Base URL for converting relative links

        Returns:
            News link URL if found, None otherwise
        """
        self.logger.info(f"Tentando fallback final: procurando 'Notícias' genérico em toda a página de {url}")

        # Use intelligent matching to avoid specific/promotional news links
        news_links = self._find_links_by_text(soup, 'notícias')

        if news_links:
            # Filter out obviously promotional or specific links
            filtered_links = []
            for link in news_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()

                # Skip overly specific or promotional links
                skip_patterns = ['g20', 'evento', 'campanha', 'especial', 'promocao']
                if not any(pattern in text or pattern in href.lower() for pattern in skip_patterns):
                    filtered_links.append(link)

            # Use filtered links if available, otherwise use original
            target_links = filtered_links if filtered_links else news_links

            # Select best from available options
            if len(target_links) > 1:
                selected_link = self._select_best_news_link(target_links, url)
            else:
                selected_link = target_links[0]

            link_url = self._extract_link_url(selected_link, url)
            if link_url:
                self.logger.info(f"Link genérico de notícias encontrado em {url}: {link_url}")
                return link_url

        return None

    def find_news_link(self, url: str) -> str:
        """
        Find a news link for a given website using multiple strategies.

        This method implements a multi-level fallback strategy with improved prioritization:
        1. Search for "Notícias" in footer
        2. Search for "Últimas Notícias" in entire page (higher priority than generic)
        3. Search for "Mais Notícias" in entire page
        4. Search for "Notícias" in entire page (broader fallback)

        Args:
            url: The website URL to search for news links

        Returns:
            News link URL if found, empty string otherwise
        """
        soup = self._make_request(url)
        if not soup:
            return ""

        # Strategy 1: Footer news links
        news_link = self._search_footer_news_links(soup, url)
        if news_link:
            return news_link

        # Strategy 2: "Últimas Notícias" fallback (prioritized for better relevance)
        news_link = self._search_latest_news_links(soup, url)
        if news_link:
            return news_link

        # Strategy 3: "Mais Notícias" fallback
        news_link = self._search_more_news_links(soup, url)
        if news_link:
            return news_link

        # Strategy 4: Generic "Notícias" fallback (last resort)
        news_link = self._search_generic_news_links(soup, url)
        if news_link:
            return news_link

        self.logger.info(
            f"Nenhum link de notícias encontrado em {url} "
            "(nenhuma estratégia foi bem-sucedida)"
        )
        return ""

    def scrape_from_csv(self, input_file: str, output_file: str,
                        portal_column: str = 'Portal',
                        news_column: str = 'Noticias') -> Tuple[int, int]:
        """
        Process a CSV file to find news links for all sites.

        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            portal_column: Name of the column containing website URLs
            news_column: Name of the column to store news links

        Returns:
            Tuple of (total_sites, sites_with_news)

        Raises:
            FileNotFoundError: If input file doesn't exist
            KeyError: If portal_column doesn't exist in the CSV
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Arquivo {input_file} não encontrado!")

        df = pd.read_csv(input_file)
        self.logger.info(f"Arquivo {input_file} carregado com {len(df)} linhas")

        if portal_column not in df.columns:
            raise KeyError(f"Coluna '{portal_column}' não encontrada no CSV")

        # Add news column if it doesn't exist
        if news_column not in df.columns:
            df[news_column] = ""

        # Find sites without news links
        sites_to_process = df[(df[news_column].isna()) | (df[news_column] == "")]

        if len(sites_to_process) == 0:
            self.logger.info("Todos os sites já têm links de notícias!")
            return len(df), len(df[df[news_column] != ""])

        self.logger.info(f"Processando {len(sites_to_process)} sites sem links de notícias")

        total_processed = 0
        for index, row in sites_to_process.iterrows():
            url = row[portal_column]
            total_processed += 1

            self.logger.info(f"Processando ({total_processed}/{len(sites_to_process)}): {url}")

            # Find news link
            news_link = self.find_news_link(url)
            df.at[index, news_column] = news_link

            # Rate limiting
            time.sleep(self.request_delay)

            # Save progress periodically
            if total_processed % 5 == 0:
                df.to_csv(output_file, index=False)
                self.logger.info(f"Progresso salvo: {total_processed} sites processados")

        # Save final results
        df.to_csv(output_file, index=False)

        # Calculate statistics
        total_sites = len(df)
        sites_with_news = len(df[df[news_column] != ""])
        sites_without_news = total_sites - sites_with_news
        success_rate = (sites_with_news / total_sites) * 100

        self.logger.info(f"Processamento concluído! Resultado salvo em {output_file}")
        self.logger.info("ESTATÍSTICAS FINAIS:")
        self.logger.info(f"Total de sites: {total_sites}")
        self.logger.info(f"Sites com links de notícias: {sites_with_news}")
        self.logger.info(f"Sites sem notícias: {sites_without_news}")
        self.logger.info(f"Taxa de sucesso: {success_rate:.1f}%")

        return total_sites, sites_with_news


def main() -> None:
    """Main entry point for the script."""
    scraper = NewsLinkScraper()

    input_file = 'all-govbr-sites-with-news.csv'
    output_file = 'all-govbr-sites-with-news-updated.csv'

    # Fallback to original file if processed file doesn't exist
    if not os.path.exists(input_file):
        input_file = 'all-govbr-sites.csv'

    try:
        total_sites, sites_with_news = scraper.process_csv_file(input_file, output_file)
        print("\n✅ Processamento concluído!")
        print(f"📊 {sites_with_news}/{total_sites} sites com links de notícias")
        print(f"📈 Taxa de sucesso: {(sites_with_news/total_sites)*100:.1f}%")

    except Exception as e:
        print(f"❌ Erro durante o processamento: {str(e)}")
        raise


