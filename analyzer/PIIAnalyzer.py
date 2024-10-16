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
    """
    A class for analyzing and detecting Personally Identifiable Information (PII) in text.

    This class provides methods for loading configurations, creating recognizer registries,
    analyzing text for PII, and managing supported languages.

    Attributes:
        config (Dict): Configuration dictionary for the analyzer.
        nlp_engine_provider (NlpEngineProvider): Provider for NLP engine.
        recognizer_registry (RecognizerRegistry): Registry of PII recognizers.
        analyzer_engine (AnalyzerEngine): Engine for analyzing text.
    """

    def __init__(self, config_path: Optional[str] = None, custom_recognizers_path: Optional[str] = None):
        """
        Initialize the PIIAnalyzer.

        Args:
            config_path (Optional[str]): Path to the configuration file.
            custom_recognizers_path (Optional[str]): Path to custom recognizers configuration.

        Returns:
            None
        """
        configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "es", "model_name": "es_core_news_md"},
                {"lang_code": "en", "model_name": "en_core_web_lg"}],
}
        self.config = self.load_config(config_path)
        self.nlp_engine_provider = NlpEngineProvider(nlp_configuration=configuration)
        self.recognizer_registry = self.create_recognizer_registry(custom_recognizers_path)
        self.analyzer_engine = AnalyzerEngine(
            nlp_engine=self.nlp_engine_provider.create_engine(),
            registry=self.recognizer_registry,
            supported_languages=self.config.get("supported_languages", ["en"])
        )
        self.anonymizer_engine = AnonymizerEngine()

    def load_config(self, config_path: Optional[str]) -> Dict:
        """
        Load configuration from a file.

        Args:
            config_path (Optional[str]): Path to the configuration file.

        Returns:
            Dict: Loaded configuration as a dictionary.

        Raises:
            ValueError: If the config file format is unsupported.
        """
        if not config_path:
            return {}
        
        with open(config_path, 'r') as file:
            if config_path.endswith('.yml') or config_path.endswith('.yaml'):
                return yaml.safe_load(file)
            elif config_path.endswith('.json'):
                return json.load(file)
        raise ValueError("Unsupported config file format. Use .yml, .yaml, or .json")

    def create_recognizer_registry(self, custom_recognizers_path: Optional[str] = None) -> RecognizerRegistry:
        """
        Create a recognizer registry with predefined and custom recognizers.

        Args:
            custom_recognizers_path (Optional[str]): Path to custom recognizers configuration.

        Returns:
            RecognizerRegistry: A registry containing predefined and custom recognizers.
        """
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()

        if custom_recognizers_path:
            custom_recognizers_provider = RecognizerRegistryProvider(conf_file=custom_recognizers_path)
            custom_registry = custom_recognizers_provider.create_recognizer_registry()
            for recognizer in custom_registry.recognizers:
                registry.add_recognizer(recognizer)

        return registry

    def save_config(self, config_path: str, format: str = "yaml") -> str:
        """
        Save the current configuration to a file.

        Args:
            config_path (str): Path where the configuration will be saved.
            format (str): Format of the configuration file ('yaml' or 'json').

        Returns:
            str: Path where the configuration was saved.

        Raises:
            ValueError: If an unsupported format is specified.
        """
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

        Returns:
            None
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
        )
        
        return [result.to_dict() for result in analyzer_results]

    def update_config(self, **kwargs):
        """
        Update configuration attributes.

        Args:
            **kwargs: Arbitrary keyword arguments to update the configuration.

        Returns:
            None
        """
        self.config.update(kwargs)
        # Reinitialize components that depend on the updated config
        self.recognizer_registry = self.create_recognizer_registry(kwargs.get("custom_recognizers_path"))
        self.analyzer_engine = AnalyzerEngine(
            nlp_engine=self.nlp_engine_provider.create_engine(),
            registry=self.recognizer_registry,
            supported_languages=self.config["supported_languages"]
        )
    def analyze_and_anonymize(self, text: str, language: str = "en"):
        
        analyzer_results = self.analyzer_engine.analyze(text=text, language=language)
        
        operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "[ANONYMIZED]"})
        }

        anonymized_text = self.anonymizer_engine.anonymize(text=text, analyzer_results=analyzer_results, operators=operators)
        
        return anonymized_text

def main():
    """
    Main function to run the PII Analyzer.

    This function sets up command-line argument parsing, initializes the PIIAnalyzer,
    and runs an example analysis.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="PII Analyzer with custom recognizers")
    parser.add_argument("--config", help="Path to the main configuration file", default="config.yml")
    parser.add_argument("--recognizers", help="Path to the custom recognizers configuration file", default="recognizers-config.yml")
    args = parser.parse_args()

    analyzer = PIIAnalyzer(config_path=args.config, custom_recognizers_path=args.recognizers)

    # Example usage
    text = "My credit card CVV is 123 and my AMEX account number is 371449635398431"
    results = analyzer.analyze_text(text)
    print("Analyzed results:", results)
    anonymized_text = analyzer.analyze_and_anonymize(text)
    print("Anonymized Text:" ,anonymized_text)

if __name__ == "__main__":
    main()