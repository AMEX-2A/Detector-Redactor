from presidio_analyzer import (
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
    AnalyzerEngine,
)
import pprint
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer

# Define the regex pattern
regex = r"\b[A-Za-z0-9]{8,20}\b"
password_pattern = Pattern(name="PASSWORD", regex=regex, score=0.01)

# Define the recognizer with the defined pattern
password_recognizer = PatternRecognizer(
    supported_entity="PASSWORD", 
    patterns=[password_pattern],
    context=["password", "pass"],
)
context_aware_enhancer = LemmaContextAwareEnhancer(
    context_similarity_factor=0.45, min_score_with_context_similarity=0.4
)

registry = RecognizerRegistry()
registry.add_recognizer(password_recognizer)
analyzer = AnalyzerEngine(registry=registry, context_aware_enhancer=context_aware_enhancer)

# Test
text1 = ["My password is BellaHadidi80", "My password is doggypaddle", "my password is emmalio"]

for text in text1:
    results = analyzer.analyze(text=text, language="en", return_decision_process=True)

    # decision_process = results[0].analysis_explanation

    # pp = pprint.PrettyPrinter()
    # print("Decision process output:\n")
    # pp.pprint(decision_process.__dict__)

    print("\nResult:")
    print(f"Original text: {text}")

    for result in results:
        detected_word = text[result.start:result.end]
        print(f"Detected Word: {detected_word}, Type: {result.entity_type}, Score: {result.score}")

