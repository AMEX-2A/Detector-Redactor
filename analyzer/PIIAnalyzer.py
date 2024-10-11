import yaml
import json
import argparse
from typing import Dict, List, Union, Optional
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, EntityRecognizer, Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistryProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import re

class PIIAnalyzer:
    def __init__(self, config_path: Optional[str] = None, custom_recognizers_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.nlp_engine_provider = NlpEngineProvider(nlp_engine_name=self.config.get("nlp_engine", "spacy"))
        self.recognizer_registry = self.create_recognizer_registry(custom_recognizers_path)
        self.analyzer_engine = AnalyzerEngine(
            nlp_engine=self.nlp_engine_provider.create_engine(),
            registry=self.recognizer_registry,
            supported_languages=self.config.get("supported_languages", ["en", "es"])
        )

    def load_config(self, config_path: Optional[str]) -> Dict:
        if not config_path:
            return {}
        
        with open(config_path, 'r') as file:
            if config_path.endswith('.yml') or config_path.endswith('.yaml'):
                return yaml.safe_load(file)
            elif config_path.endswith('.json'):
                return json.load(file)
        raise ValueError("Unsupported config file format. Use .yml, .yaml, or .json")

    def create_recognizer_registry(self, custom_recognizers_path: Optional[str] = None) -> RecognizerRegistry:
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()

        if custom_recognizers_path:
            custom_recognizers_provider = RecognizerRegistryProvider(conf_file=custom_recognizers_path)
            custom_registry = custom_recognizers_provider.create_recognizer_registry()
            for recognizer in custom_registry.recognizers:
                registry.add_recognizer(recognizer)

        return registry

    def save_config(self, config_path: str, format: str = "yaml") -> str:
        with open(config_path, 'w') as file:
            if format == "yaml":
                yaml.dump(self.config, file)
            elif format == "json":
                json.dump(self.config, file, indent=2)
            else:
                raise ValueError("Unsupported format. Use 'yaml' or 'json'")
        return config_path

    def add_language(self, language_code: str, model_path: Optional[str] = None):
        """
        Add support for a new language.
        
        Args:
            language_code (str): The ISO code for the language (e.g., 'fr' for French)
            model_path (Optional[str]): Path to the custom NLP model for this language
        """
        if language_code not in self.config.get("supported_languages", []):
            self.config["supported_languages"].append(language_code)
        
        if model_path:
            self.config["language_models"] = self.config.get("language_models", {})
            self.config["language_models"][language_code] = model_path
        
        # Reinitialize the analyzer engine with the updated languages
        self.analyzer_engine = AnalyzerEngine(
            nlp_engine=self.nlp_engine_provider.create_engine(),
            registry=self.recognizer_registry,
            supported_languages=self.config["supported_languages"]
        )

    def analyze_text(self, text: str, language: str = "en", trace: bool = False) -> List[Dict]:
        """
        Analyze text and return recognized entities.
        
        Args:
            text (str): The text to analyze
            language (str): The language of the text
            trace (bool): Whether to include analysis explanation
        
        Returns:
            List[Dict]: List of recognized entities with their details
        """
        analyzer_results = self.analyzer_engine.analyze(
            text=text,
            language=language,
            entities=self.config.get("entities_to_analyze"),
            allow_list=self.config.get("allow_list"),
            trace=trace
        )
        
        return [result.to_dict() for result in analyzer_results]

    def update_config(self, **kwargs):
        """Update configuration attributes."""
        self.config.update(kwargs)
        # Reinitialize components that depend on the updated config
        self.recognizer_registry = self.create_recognizer_registry(kwargs.get("custom_recognizers_path"))
        self.analyzer_engine = AnalyzerEngine(
            nlp_engine=self.nlp_engine_provider.create_engine(),
            registry=self.recognizer_registry,
            supported_languages=self.config["supported_languages"]
        )

def main():
    parser = argparse.ArgumentParser(description="PII Analyzer with custom recognizers")
    parser.add_argument("--config", help="Path to the main configuration file", default="config.yml")
    parser.add_argument("--recognizers", help="Path to the custom recognizers configuration file", default="recognizers-config.yml")
    args = parser.parse_args()

    analyzer = PIIAnalyzer(config_path=args.config, custom_recognizers_path=args.recognizers)

    # Example usage
    text = "My credit card CVV is 123 and my AMEX account number is 371449635398431"
    results = analyzer.analyze_text(text)
    print("Analyzed results:", results)

if __name__ == "__main__":
    main()