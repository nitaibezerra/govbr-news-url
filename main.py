#!/usr/bin/env python3
"""
News URL Scraper - Main Module
"""

import argparse
import os
import sys
from typing import Optional

from src.scraper import NewsLinkScraper
from src.url_updater import URLUpdater


def scrape_command(args: Optional[argparse.Namespace] = None) -> None:
    """Execute the scraping command."""
    input_file = "data/input/all-govbr-sites.csv"
    output_file = "data/stage/scraped_urls.csv"

    os.makedirs("data/stage", exist_ok=True)

    if not os.path.exists(input_file):
        print(f"❌ Arquivo de entrada não encontrado: {input_file}")
        sys.exit(1)

    print("🚀 Iniciando raspagem de URLs de notícias...")
    print(f"📂 Entrada: {input_file}")
    print(f"📂 Saída: {output_file}")
    print()

    scraper = NewsLinkScraper()

    try:
        total_sites, sites_with_news = scraper.scrape_from_csv(input_file, output_file)
        success_rate = (sites_with_news / total_sites) * 100

        print()
        print("✅ Raspagem concluída!")
        print(f"📊 {sites_with_news}/{total_sites} sites com links de notícias")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💾 Resultados salvos em: {output_file}")

    except Exception as e:
        print(f"❌ Erro durante a raspagem: {e}")
        sys.exit(1)


def update_urls_command(args: Optional[argparse.Namespace] = None) -> None:
    """Execute the URL update command."""
    csv_file = "data/stage/scraped_urls.csv"
    yaml_input = "data/input/site_urls.yaml"
    yaml_output = "data/output/site_urls.yaml"

    os.makedirs("data/output", exist_ok=True)

    if not os.path.exists(csv_file):
        print(f"❌ Arquivo de resultados não encontrado: {csv_file}")
        print("💡 Execute primeiro: python main.py scrape")
        sys.exit(1)

    if not os.path.exists(yaml_input):
        print(f"❌ Arquivo YAML de entrada não encontrado: {yaml_input}")
        sys.exit(1)

    print("🔄 Iniciando atualização de URLs...")
    print(f"📂 CSV de entrada: {csv_file}")
    print(f"�� YAML de entrada: {yaml_input}")
    print(f"📂 YAML de saída: {yaml_output}")
    print()

    updater = URLUpdater()

    try:
        total_agencies, discrepancies = updater.update_urls_from_csv(
            csv_file, yaml_input, yaml_output
        )

        accuracy_rate = ((total_agencies - discrepancies) / total_agencies) * 100

        print()
        print("✅ Atualização concluída!")
        print(f"📊 {total_agencies - discrepancies}/{total_agencies} URLs corretos")
        print(f"📈 Taxa de acerto: {accuracy_rate:.1f}%")
        print(f"💾 YAML atualizado salvo em: {yaml_output}")

    except Exception as e:
        print(f"❌ Erro durante a atualização: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="News URL Scraper for Brazilian Government Websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python main.py scrape        # Raspar URLs de notícias
    python main.py update_urls   # Atualizar arquivo de configuração
        """
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Comandos disponíveis',
        title='Comandos'
    )

    scrape_parser = subparsers.add_parser(
        'scrape',
        help='Raspar URLs de notícias dos sites governamentais'
    )

    update_parser = subparsers.add_parser(
        'update_urls',
        help='Atualizar arquivo site_urls.yaml baseado nos resultados'
    )

    args = parser.parse_args()

    if args.command == 'scrape':
        scrape_command(args)
    elif args.command == 'update_urls':
        update_urls_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
