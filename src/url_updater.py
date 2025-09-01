#!/usr/bin/env python3
"""
URL Updater Module

Updates the site_urls.yaml file based on scraped results and validation logic.
"""

import logging
import re
from typing import Dict, List, Tuple

import pandas as pd
import yaml


class URLUpdater:
    """Updates site_urls.yaml based on scraped results and intelligent validation."""

    def __init__(self, log_level: int = logging.INFO):
        """Initialize the URL updater."""
        self.logger = self._setup_logger(log_level)

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """Set up and configure the logger for the updater."""
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger

    def extract_agency_code(self, portal_url: str) -> str:
        """Extract agency code from portal URL."""
        match = re.search(r'https://www\.gov\.br/([^/]+)/pt-br', portal_url)
        return match.group(1) if match else ""

    def load_yaml_urls(self, yaml_file: str) -> Dict[str, str]:
        """Load URLs from YAML file."""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('agencies', {})
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo YAML {yaml_file}: {e}")
            raise

    def save_yaml_urls(self, urls: Dict[str, str], output_file: str) -> None:
        """Save URLs to YAML file."""
        try:
            data = {'agencies': urls}
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=True)
            self.logger.info(f"URLs atualizadas salvas em {output_file}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivo YAML {output_file}: {e}")
            raise

    def load_scraped_csv(self, csv_file: str) -> pd.DataFrame:
        """Load scraped results from CSV file."""
        try:
            df = pd.read_csv(csv_file)
            self.logger.info(f"CSV carregado com {len(df)} linhas")
            return df
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo CSV {csv_file}: {e}")
            raise

    def is_url_contained(self, extracted_url: str, correct_url: str) -> bool:
        """Check if extracted URL is contained within the correct URL."""
        if not extracted_url or not correct_url:
            return False
            
        extracted_clean = extracted_url.strip().rstrip('/')
        correct_clean = correct_url.strip().rstrip('/')
        
        return extracted_clean in correct_clean

    def validate_and_update_urls(self, scraped_df: pd.DataFrame, yaml_urls: Dict[str, str]) -> Tuple[Dict[str, str], List[Dict]]:
        """Validate scraped URLs against YAML truth source and generate updates."""
        updated_urls = yaml_urls.copy()
        discrepancies = []
        
        for _, row in scraped_df.iterrows():
            portal_url = row['Portal']
            extracted_url = row.get('Noticias', '')
            
            agency_code = self.extract_agency_code(portal_url)
            if not agency_code:
                continue
                
            if agency_code not in yaml_urls:
                if pd.notna(extracted_url) and extracted_url.strip():
                    updated_urls[agency_code] = extracted_url.strip()
                    self.logger.info(f"Nova agência adicionada: {agency_code} -> {extracted_url}")
                continue
                
            correct_url = yaml_urls[agency_code]
            
            if pd.isna(extracted_url) or not extracted_url.strip():
                continue
                
            extracted_url = extracted_url.strip()
            
            if extracted_url == correct_url:
                continue
                
            if self.is_url_contained(extracted_url, correct_url):
                self.logger.info(f"URL extraída válida (contida na correta): {agency_code}")
                continue
                
            discrepancy = {
                'agency': agency_code,
                'portal_url': portal_url,
                'extracted_url': extracted_url,
                'correct_url': correct_url,
                'action': 'discrepancy'
            }
            discrepancies.append(discrepancy)
            
        self.logger.info(f"Validação concluída. {len(discrepancies)} discrepâncias encontradas")
        return updated_urls, discrepancies

    def generate_report(self, discrepancies: List[Dict]) -> str:
        """Generate a human-readable report of discrepancies."""
        if not discrepancies:
            return "✅ Nenhuma discrepância encontrada! Todos os URLs estão corretos."
            
        report = [f"📊 RELATÓRIO DE DISCREPÂNCIAS ({len(discrepancies)} encontradas)", "=" * 60, ""]
        
        for i, disc in enumerate(discrepancies, 1):
            report.extend([
                f"{i}. **{disc['agency'].upper()}**",
                f"   Portal: {disc['portal_url']}",
                f"   ❌ Extraído: {disc['extracted_url']}",
                f"   ✅ Correto:  {disc['correct_url']}",
                ""
            ])
            
        return "\n".join(report)

    def update_urls_from_csv(self, csv_file: str, yaml_input: str, yaml_output: str) -> Tuple[int, int]:
        """Complete update process: load data, validate, and save results."""
        scraped_df = self.load_scraped_csv(csv_file)
        yaml_urls = self.load_yaml_urls(yaml_input)
        
        updated_urls, discrepancies = self.validate_and_update_urls(scraped_df, yaml_urls)
        
        report = self.generate_report(discrepancies)
        print(report)
        
        self.save_yaml_urls(updated_urls, yaml_output)
        
        total_yaml_agencies = len(yaml_urls)
        total_discrepancies = len(discrepancies)
        accuracy_rate = ((total_yaml_agencies - total_discrepancies) / total_yaml_agencies) * 100
        
        self.logger.info("ESTATÍSTICAS FINAIS:")
        self.logger.info(f"Agências no YAML: {total_yaml_agencies}")
        self.logger.info(f"Discrepâncias encontradas: {total_discrepancies}")
        self.logger.info(f"Taxa de acerto: {accuracy_rate:.1f}%")
        
        return total_yaml_agencies, total_discrepancies
