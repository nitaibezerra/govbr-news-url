# GovBR News URL Scraper

A robust web scraper that finds news links in Brazilian government websites (gov.br domain). Uses multiple fallback strategies to maximize link discovery success rate.

## Features

- **Multi-level fallback strategy**: Searches for news links using three different approaches:
  1. "Notícias" links in website footer
  2. "Mais Notícias" links throughout the page
  3. "Últimas Notícias" links throughout the page

- **High success rate**: Achieves 96%+ success rate in finding news links
- **Rate limiting**: Built-in delays to avoid overloading government servers
- **Progress tracking**: Saves progress periodically and provides detailed logging
- **CSV processing**: Batch process multiple websites from CSV files
- **Robust error handling**: Handles timeouts, HTTP errors, and malformed HTML

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from govbr_news_scraper import NewsLinkScraper

# Create scraper instance
scraper = NewsLinkScraper()

# Find news link for a single website
news_url = scraper.find_news_link("https://www.gov.br/anvisa/pt-br")
print(f"News URL: {news_url}")
```

### CSV Batch Processing

```python
from govbr_news_scraper import NewsLinkScraper

# Create scraper instance
scraper = NewsLinkScraper()

# Process CSV file with government websites
total_sites, sites_with_news = scraper.process_csv_file(
    input_file="govbr_sites.csv",
    output_file="govbr_sites_with_news.csv"
)

print(f"Success rate: {sites_with_news/total_sites*100:.1f}%")
```

### Command Line Usage

```bash
python govbr_news_scraper.py
```

## CSV Format

The input CSV file should have at minimum a column with website URLs:

```csv
Portal,Órgão ou Entidade
https://www.gov.br/anvisa/pt-br,ANVISA
https://www.gov.br/ana/pt-br,ANA
https://www.gov.br/anatel/pt-br,ANATEL
```

The scraper will add a "Noticias" column with the discovered news URLs:

```csv
Portal,Órgão ou Entidade,Noticias
https://www.gov.br/anvisa/pt-br,ANVISA,https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa
https://www.gov.br/ana/pt-br,ANA,https://www.gov.br/ana/pt-br/assuntos/noticias-e-eventos
https://www.gov.br/anatel/pt-br,ANATEL,https://www.gov.br/anatel/pt-br/noticias
```

## Configuration Options

```python
scraper = NewsLinkScraper(
    request_timeout=30,     # HTTP request timeout in seconds
    request_delay=2.0,      # Delay between requests in seconds
    user_agent="Custom-Agent"  # Custom User-Agent string
)
```

## Search Strategy

The scraper uses a three-level fallback strategy:

1. **Footer Search**: Looks for "Notícias" links in `<div class="footer-wrapper">`
2. **Page-wide "Mais Notícias"**: Searches entire page for "Mais Notícias" links
3. **Page-wide "Últimas Notícias"**: Searches entire page for "Últimas Notícias" links

This approach maximizes the chances of finding news sections across different website layouts.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=govbr_news_scraper

# Run specific test file
pytest tests/test_govbr_news_scraper.py
```

### Code Quality

```bash
# Format code
black govbr_news_scraper.py tests/

# Lint code
flake8 govbr_news_scraper.py tests/

# Type checking
mypy govbr_news_scraper.py
```

## Project Structure

```
├── govbr_news_scraper.py      # Main scraper class
├── find_news_links.py         # Legacy script (deprecated)
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures
│   └── test_govbr_news_scraper.py  # Main tests
├── all-govbr-sites.csv       # Input data
└── all-govbr-sites-with-news.csv  # Output data
```

## Performance

- **Success Rate**: 96.3% (156/162 sites)
- **Rate Limiting**: 2-second delay between requests (configurable)
- **Memory Efficient**: Processes files incrementally
- **Progress Saving**: Saves progress every 5 sites to prevent data loss

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Changelog

### v1.0.0
- Initial release with object-oriented design
- Multi-level fallback strategy
- Comprehensive test suite
- CSV batch processing
- Rate limiting and error handling
