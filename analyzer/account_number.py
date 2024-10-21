from presidio_analyzer import Pattern, PatternRecognizer, RecognizerRegistry, AnalyzerEngine

class accountNumberRecognizer(PatternRecognizer):
    # #acc 8 - 12 digits 
    account_num_pattern = Pattern(name="account_number_pattern", regex="^[0-9]+$", score=0.5 )

    number_recognizer = PatternRecognizer(
        supported_entity="NUMBER", patterns=[account_num_pattern]
    )

    text1 = "My account number is 635802010014976"
    # num_result = number_recognizer.analyze(text=text1, entities=["NUMBER"])

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()

    # Add the recognizer to the existing list of recognizers
    registry.add_recognizer(number_recognizer)

    # Set up analyzer with our updated recognizer registry
    analyzer = AnalyzerEngine(registry=registry)

    # Run with input text
    text1 = ["My account number is 635802010014976", "My acc num is 635802010014976"]

    for text in text1:
        results = analyzer.analyze(text=text, language="en")

        print("Result:")
        print(f"Original text: {text}")

        for result in results:
            detected_word = text[result.start:result.end]
            print(f"Detected Word: {detected_word}, Type: {result.entity_type}, Score: {result.score}\n")
