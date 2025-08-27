"""Test configuration and fixtures for govbr-news-scraper tests."""

import pytest
import tempfile
import os
from unittest.mock import Mock
import pandas as pd
from bs4 import BeautifulSoup


@pytest.fixture
def scraper():
    """Create a NewsLinkScraper instance for testing."""
    from govbr_news_scraper import NewsLinkScraper
    return NewsLinkScraper(request_delay=0.1)  # Faster for tests


@pytest.fixture
def sample_html_with_footer_news():
    """HTML with news link in footer."""
    return """
    <html>
        <body>
            <div class="content">Some content</div>
            <div class="footer-wrapper">
                <a href="/noticias">Notícias</a>
                <a href="/contato">Contato</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_with_mais_noticias():
    """HTML with 'Mais Notícias' link but no footer news."""
    return """
    <html>
        <body>
            <div class="content">
                <a href="/mais-noticias">Mais Notícias</a>
            </div>
            <div class="footer-wrapper">
                <a href="/contato">Contato</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_with_ultimas_noticias():
    """HTML with 'Últimas Notícias' link but no other news links."""
    return """
    <html>
        <body>
            <div class="content">
                <a href="/ultimas-noticias">Últimas Notícias</a>
            </div>
            <div class="footer-wrapper">
                <a href="/contato">Contato</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_no_news():
    """HTML with no news links."""
    return """
    <html>
        <body>
            <div class="content">Some content</div>
            <div class="footer-wrapper">
                <a href="/contato">Contato</a>
                <a href="/sobre">Sobre</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_no_footer():
    """HTML without footer wrapper."""
    return """
    <html>
        <body>
            <div class="content">
                <a href="/mais-noticias">Mais Notícias</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return pd.DataFrame({
        'Portal': [
            'https://example.gov.br/site1',
            'https://example.gov.br/site2',
            'https://example.gov.br/site3'
        ],
        'Órgão ou Entidade': [
            'Ministério A',
            'Ministério B', 
            'Ministério C'
        ]
    })


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_csv_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_successful_response():
    """Mock a successful HTTP response."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = """
    <html>
        <body>
            <div class="footer-wrapper">
                <a href="/noticias">Noticias</a>
            </div>
        </body>
    </html>
    """.encode('utf-8')
    return mock_response


@pytest.fixture
def mock_failed_response():
    """Mock a failed HTTP response."""
    from requests.exceptions import RequestException
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = RequestException("Test error")
    return mock_response
