import yaml
import json
import argparse
import argparse
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer.entities import OperatorConfig
from PIIAnalyzer import PIIAnalyzer  # Assuming the earlier code is in this module

def amex_account_number(text, analyzer):
    """
    Analyze and redact AMEX account numbers in the given text.

    Args:
        text (str): The input text to analyze.
        analyzer (PIIAnalyzer): The PIIAnalyzer instance.

    Returns:
        str: The text with AMEX account numbers redacted.
    """
    # Analyze the text for AMEX account numbers
    check_result = analyzer.analyzer_engine.analyze(
        text=text, 
        language="en", 
        entities=["AMEX_ACCOUNT_NUMBER"]
    )
    print("Result for AMEX account numbers: ", check_result)

    # Redact detected AMEX account numbers
    offset = 0
    for result in check_result:
        start = result.start + offset
        end = result.end + offset
        text = text[:start] + "[REDACTED]" + text[end:]
        offset += len("[REDACTED]") - (end - start)

    return text


def main():
    """
    Main function to run AMEX account number redaction on test data.
    """
    parser = argparse.ArgumentParser(description="AMEX Account Number Redactor")
    parser.add_argument("--config", help="Path to the main configuration file", default="config.yml")
    parser.add_argument("--recognizers", help="Path to the custom recognizers configuration file", default="recognizers-config.yml")
    args = parser.parse_args()

    # Initialize the PIIAnalyzer
    analyzer = PIIAnalyzer(config_path=args.config, custom_recognizers_path=args.recognizers)

    # Example test data
    test_data = "Dear Customer Support,Im experiencing issues with my American Express cards and need assistance urgently. My first AMEX card number is 3714-4963-5398-431, and I’ve been using it for years without any trouble. Recently, when I tried to make a purchase online, the payment failed. The website showed an error stating that my card was declined. Then, I used another AMEX card with the number 3782 8224 6310 005 and faced the same issue. These problems have been consistent for over a week now.For reference, the expiration date for the first card is 03/2026, and its CVV code is 321. The second card has an expiration date of 11/2025, with a CVV code of 654. To add to the frustration, the first card number is also stored in another system as 3714 49-63 5398 431 without the usual formatting, and I’m not sure if this inconsistency is causing the problem.Last week, I tried to use the first card to make a payment of $120.45 at a grocery store, where it is saved in their database as `371449635398431`. The transaction failed. For my second card, I noticed that it was stored by another merchant with an even stranger format: `3782-82-24 63-10005`. Despite these variations, both cards are active and should be working. I am deeply concerned that there may be a technical error with how the system reads my card numbers.Additionally, I tried making another payment of $75.32 at a gas station using the card number 37 14 49 6353 98 43 1, but it was also declined. I rely heavily on these cards for daily purchases, and this situation is becoming increasingly frustrating. Please note that the second card number also appears in some of my records as 37-828-2246-3100-05, which makes me wonder if the formatting inconsistency is at fault.Could you please check both cards, including any formatting or validation issues? My primary concern is to ensure that both card numbers (3714-4963-5398-431 and 3782 8224 6310 005) are functional again. Your immediate attention to this matter would be greatly appreciated.Sincerely,  John Doe"
    # Analyze and redact AMEX account numbers
    redacted_data = amex_account_number(test_data, analyzer)
    print("Redacted Data:", redacted_data)


if __name__ == "__main__":
    main()
