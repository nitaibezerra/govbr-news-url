"""Tests for the GovBR News URL Scraper."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from bs4 import BeautifulSoup
import requests

from govbr_news_scraper import NewsLinkScraper


class TestNewsLinkScraper:
    """Test cases for NewsLinkScraper class."""
    
    def test_init_default_values(self):
        """Test scraper initialization with default values."""
        scraper = NewsLinkScraper()
        assert scraper.request_timeout == 30
        assert scraper.request_delay == 2.0
        assert 'Mozilla' in scraper.headers['User-Agent']
        
    def test_init_custom_values(self):
        """Test scraper initialization with custom values."""
        scraper = NewsLinkScraper(
            request_timeout=10,
            request_delay=1.0,
            user_agent="TestAgent"
        )
        assert scraper.request_timeout == 10
        assert scraper.request_delay == 1.0
        assert scraper.headers['User-Agent'] == "TestAgent"
        
    def test_convert_to_absolute_url(self, scraper):
        """Test URL conversion from relative to absolute."""
        base_url = "https://example.gov.br"
        
        # Test relative URL starting with /
        result = scraper._convert_to_absolute_url("/noticias", base_url)
        assert result == "https://example.gov.br/noticias"
        
        # Test relative URL without /
        result = scraper._convert_to_absolute_url("noticias", base_url)
        assert result == "https://example.gov.br/noticias"
        
        # Test absolute URL
        absolute_url = "https://other.gov.br/noticias"
        result = scraper._convert_to_absolute_url(absolute_url, base_url)
        assert result == absolute_url
        
    def test_find_links_by_text(self, scraper):
        """Test finding links by text content."""
        html = """
        <div>
            <a href="/news">Notícias</a>
            <a href="/contact">Contato</a>
            <a href="/more">Mais Notícias</a>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test finding "notícias"
        links = scraper._find_links_by_text(soup, "notícias")
        assert len(links) == 2  # Should find both "Notícias" and "Mais Notícias"
        
        # Test finding "mais notícias"
        links = scraper._find_links_by_text(soup, "mais notícias")
        assert len(links) == 1
        assert links[0].get('href') == '/more'
        
    def test_extract_link_url(self, scraper):
        """Test extracting URL from link tag."""
        html = '<a href="/noticias">Notícias</a>'
        soup = BeautifulSoup(html, 'html.parser')
        link = soup.find('a')
        
        result = scraper._extract_link_url(link, "https://example.gov.br")
        assert result == "https://example.gov.br/noticias"
        
        # Test link without href
        html_no_href = '<a>Notícias</a>'
        soup_no_href = BeautifulSoup(html_no_href, 'html.parser')
        link_no_href = soup_no_href.find('a')
        
        result = scraper._extract_link_url(link_no_href, "https://example.gov.br")
        assert result is None
        
    def test_search_footer_news_links_success(self, scraper, sample_html_with_footer_news):
        """Test successful footer news link search."""
        soup = BeautifulSoup(sample_html_with_footer_news, 'html.parser')
        
        result = scraper._search_footer_news_links(soup, "https://example.gov.br")
        assert result == "https://example.gov.br/noticias"
        
    def test_search_footer_news_links_no_footer(self, scraper, sample_html_no_footer):
        """Test footer search when no footer exists."""
        soup = BeautifulSoup(sample_html_no_footer, 'html.parser')
        
        result = scraper._search_footer_news_links(soup, "https://example.gov.br")
        assert result is None
        
    def test_search_more_news_links_success(self, scraper, sample_html_with_mais_noticias):
        """Test successful 'Mais Notícias' search."""
        soup = BeautifulSoup(sample_html_with_mais_noticias, 'html.parser')
        
        result = scraper._search_more_news_links(soup, "https://example.gov.br")
        assert result == "https://example.gov.br/mais-noticias"
        
    def test_search_latest_news_links_success(self, scraper, sample_html_with_ultimas_noticias):
        """Test successful 'Últimas Notícias' search."""
        soup = BeautifulSoup(sample_html_with_ultimas_noticias, 'html.parser')
        
        result = scraper._search_latest_news_links(soup, "https://example.gov.br")
        assert result == "https://example.gov.br/ultimas-noticias"
        
    @patch('govbr_news_scraper.requests.get')
    def test_make_request_success(self, mock_get, scraper, mock_successful_response):
        """Test successful HTTP request."""
        mock_get.return_value = mock_successful_response
        
        result = scraper._make_request("https://example.gov.br")
        assert result is not None
        assert isinstance(result, BeautifulSoup)
        
    @patch('govbr_news_scraper.requests.get')
    def test_make_request_timeout(self, mock_get, scraper):
        """Test HTTP request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = scraper._make_request("https://example.gov.br")
        assert result is None
        
    @patch('govbr_news_scraper.requests.get')
    def test_make_request_http_error(self, mock_get, scraper):
        """Test HTTP request error."""
        mock_get.side_effect = requests.exceptions.RequestException("HTTP Error")
        
        result = scraper._make_request("https://example.gov.br")
        assert result is None
        
    @patch.object(NewsLinkScraper, '_make_request')
    def test_find_news_link_footer_strategy(self, mock_request, scraper, sample_html_with_footer_news):
        """Test find_news_link with footer strategy."""
        mock_request.return_value = BeautifulSoup(sample_html_with_footer_news, 'html.parser')
        
        result = scraper.find_news_link("https://example.gov.br")
        assert result == "https://example.gov.br/noticias"
        
    @patch.object(NewsLinkScraper, '_make_request')
    def test_find_news_link_mais_noticias_strategy(self, mock_request, scraper, sample_html_with_mais_noticias):
        """Test find_news_link with 'Mais Notícias' fallback strategy."""
        mock_request.return_value = BeautifulSoup(sample_html_with_mais_noticias, 'html.parser')
        
        result = scraper.find_news_link("https://example.gov.br")
        assert result == "https://example.gov.br/mais-noticias"
        
    @patch.object(NewsLinkScraper, '_make_request')
    def test_find_news_link_ultimas_noticias_strategy(self, mock_request, scraper, sample_html_with_ultimas_noticias):
        """Test find_news_link with 'Últimas Notícias' fallback strategy."""
        mock_request.return_value = BeautifulSoup(sample_html_with_ultimas_noticias, 'html.parser')
        
        result = scraper.find_news_link("https://example.gov.br")
        assert result == "https://example.gov.br/ultimas-noticias"
        
    @patch.object(NewsLinkScraper, '_make_request')
    def test_find_news_link_no_news_found(self, mock_request, scraper, sample_html_no_news):
        """Test find_news_link when no news links are found."""
        mock_request.return_value = BeautifulSoup(sample_html_no_news, 'html.parser')
        
        result = scraper.find_news_link("https://example.gov.br")
        assert result == ""
        
    @patch.object(NewsLinkScraper, '_make_request')
    def test_find_news_link_request_fails(self, mock_request, scraper):
        """Test find_news_link when HTTP request fails."""
        mock_request.return_value = None
        
        result = scraper.find_news_link("https://example.gov.br")
        assert result == ""
        
    def test_process_csv_file_not_found(self, scraper):
        """Test processing non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            scraper.process_csv_file("nonexistent.csv", "output.csv")
            
    def test_process_csv_file_missing_portal_column(self, scraper, temp_csv_file):
        """Test processing CSV with missing Portal column."""
        with pytest.raises(KeyError):
            scraper.process_csv_file(temp_csv_file, "output.csv", portal_column="NonExistent")
            
    @patch.object(NewsLinkScraper, 'find_news_link')
    @patch('govbr_news_scraper.time.sleep')  # Mock sleep to speed up tests
    def test_process_csv_file_success(self, mock_sleep, mock_find_news, scraper, temp_csv_file):
        """Test successful CSV processing."""
        # Mock find_news_link to return different results
        mock_find_news.side_effect = [
            "https://example.gov.br/site1/noticias",
            "",  # No news found for site2
            "https://example.gov.br/site3/noticias"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as output_file:
            total_sites, sites_with_news = scraper.process_csv_file(
                temp_csv_file, 
                output_file.name
            )
            
            assert total_sites == 3
            assert sites_with_news == 2
            
            # Verify output file content
            result_df = pd.read_csv(output_file.name)
            assert 'Noticias' in result_df.columns
            assert result_df.loc[0, 'Noticias'] == "https://example.gov.br/site1/noticias"
            # Handle both empty string and NaN for missing values
            assert pd.isna(result_df.loc[1, 'Noticias']) or result_df.loc[1, 'Noticias'] == ""
            assert result_df.loc[2, 'Noticias'] == "https://example.gov.br/site3/noticias"
            
        os.unlink(output_file.name)
        
    @patch.object(NewsLinkScraper, 'find_news_link')
    @patch('govbr_news_scraper.time.sleep')
    def test_process_csv_file_with_existing_news_column(self, mock_sleep, mock_find_news, scraper):
        """Test processing CSV that already has news column with some data."""
        # Create CSV with existing news data
        df = pd.DataFrame({
            'Portal': [
                'https://example.gov.br/site1',
                'https://example.gov.br/site2',
                'https://example.gov.br/site3'
            ],
            'Órgão ou Entidade': ['A', 'B', 'C'],
            'Noticias': [
                'https://example.gov.br/site1/existing-news',
                '',  # Empty - should be processed
                ''   # Empty - should be processed
            ]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as input_file:
            df.to_csv(input_file.name, index=False)
            
            # Mock find_news_link for the two empty entries
            mock_find_news.side_effect = [
                "https://example.gov.br/site2/noticias",
                "https://example.gov.br/site3/noticias"
            ]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as output_file:
                total_sites, sites_with_news = scraper.process_csv_file(
                    input_file.name,
                    output_file.name
                )
                
                assert total_sites == 3
                assert sites_with_news == 3
                
                # Verify the first site's news link wasn't changed
                result_df = pd.read_csv(output_file.name)
                assert result_df.loc[0, 'Noticias'] == 'https://example.gov.br/site1/existing-news'
                assert result_df.loc[1, 'Noticias'] == 'https://example.gov.br/site2/noticias'
                assert result_df.loc[2, 'Noticias'] == 'https://example.gov.br/site3/noticias'
                
                # Verify find_news_link was called only for empty entries
                assert mock_find_news.call_count == 2
                
            os.unlink(output_file.name)
        os.unlink(input_file.name)


class TestMainFunction:
    """Test cases for the main function."""
    
    @patch.object(NewsLinkScraper, 'process_csv_file')
    @patch('os.path.exists')
    def test_main_with_existing_processed_file(self, mock_exists, mock_process):
        """Test main function with existing processed file."""
        from govbr_news_scraper import main
        
        # Mock file existence check
        mock_exists.return_value = True
        mock_process.return_value = (162, 156)
        
        # Should not raise any exceptions
        main()
        
        mock_process.assert_called_once()
        
    @patch.object(NewsLinkScraper, 'process_csv_file')
    @patch('os.path.exists')
    def test_main_with_original_file_only(self, mock_exists, mock_process):
        """Test main function when only original file exists."""
        from govbr_news_scraper import main
        
        # Mock file existence - processed file doesn't exist, original does
        mock_exists.side_effect = lambda path: path == 'all-govbr-sites.csv'
        mock_process.return_value = (162, 156)
        
        main()
        
        mock_process.assert_called_once()
        # Verify it used the original file
        call_args = mock_process.call_args[0]
        assert call_args[0] == 'all-govbr-sites.csv'
        
    @patch.object(NewsLinkScraper, 'process_csv_file')
    @patch('os.path.exists')
    def test_main_with_exception(self, mock_exists, mock_process):
        """Test main function when an exception occurs."""
        from govbr_news_scraper import main
        
        mock_exists.return_value = True
        mock_process.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            main()
