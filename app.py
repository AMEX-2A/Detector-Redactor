import streamlit as st
from analyzer.PIIAnalyzer import PIIAnalyzer
import yaml
import os

#! TODO: Configuration Options
#! Make encryption more format-preserving in a way that is easy for an llm to still understand the context of the message.
#^ idea: build pipeline to feed redacted text into a LLM for further processing.

st.set_page_config(page_title="PII Detector-Redactor", layout="wide")

def load_analyzer() -> PIIAnalyzer:
    """Initialize and return a PIIAnalyzer instance
    
    Returns:
        PIIAnalyzer: Configured analyzer for detecting PII
    """
    if 'analyzer' not in st.session_state:                   # cache analyzer instance
        st.session_state.analyzer = PIIAnalyzer()
    return st.session_state.analyzer

def main() -> None:
    """Main application function that sets up the Streamlit UI and handles user interactions"""
    
    # Custom CSS for styling
    st.markdown("""
        <style>
        .title-text { 
            font-size: 64px;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(45deg, #2A0066, #00BFFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 20px 0;
            text-align: center;
        }
        .stButton button {
            background-color: #2a5298;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stTextArea textarea {
            border-radius: 5px;
            border: 1px solid #2a5298;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='title-text'>🛡️ AMEX Team 2A: Detector-Redactor 🛡️</h1>", unsafe_allow_html=True)
    st.write("Upload text files or enter text directly to detect and redact personally identifiable information.")
    
    with st.expander("What is PII?"):
        st.write("""
        Personally Identifiable Information (PII) includes:
        - Names
        - Phone numbers
        - Email addresses
        - Credit card numbers
        - IP addresses
        - Account numbers
        - Social security numbers
        - Physical addresses
        And more...
        """)                                # show info about PII types in expandable section
    
    with st.expander("How to use"):
        st.write("""
        1. Choose your preferred input method (text or file upload)
        2. Select the language of your text
        3. Enter or upload your text
        4. Click 'Analyze Text' to detect PII
        5. Optionally click 'Anonymize Text' to redact detected PII
        6. Download the anonymized version if needed
        """)                                # show usage instructions in expandable section
    
    analyzer = load_analyzer()              # init analyzer instance from session state
    
    language = st.selectbox(
        "Select language for analysis:",
        ["en", "es"],
        index=0,
        help="Currently supports English (en) and Spanish (es)"
    )                                       # lang selector for text analysis

    # Text input above columns
    text_input = st.text_area("Enter text to analyze:", height=200, key="text_input")

    # Choose redaction methods
    if "anonymization_method" not in st.session_state:
        st.session_state.anonymization_method = "FPE"  # Default method is FPE

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔐 FPE Anonymizer", key="fpe_button"):
            st.session_state.anonymization_method = "FPE"  # Set FPE as the selected method

    with col2:      
        if st.button("Entity Masking Anonymizer", key="entities_button"):
            st.session_state.anonymization_method = "Entities"  # Set Entities as the selected method
    
    with col3:
        if st.button("Simple Redactor", key = "simple_button"):
            st.session_state.anonymization_method = "Simple"

    if text_input:
        input_text = text_input
        
        try:
            with st.spinner('Analyzing text...'):
                results = analyzer.analyze_text(input_text, language=language)
            
            col1, col2 = st.columns(2)      # split results into two columns
            
            with col1:
                st.markdown("### 🔍 Detected PII")
                if results:
                    pii_data = []
                    for result in results:
                        detected_text = input_text[result.start:result.end]
                        pii_data.append({
                            "Type": result.entity_type,
                            "Text": detected_text,
                            "Position": f"{result.start}-{result.end}"
                        })
                    st.table(pii_data)      # show detected PII in styled table
                else:
                    st.info("No PII detected in the text.")
                    
            with col2:
                st.markdown("### 🔐 Anonymized Text")
                # Add buttons for toggling between FPE and Entity Masking
                
            
                anonymized_text = None  # Initialize variable for anonymized text
            
                # Handle button clicks
                if st.session_state.anonymization_method == "FPE":
                    anonymized_text = analyzer.analyze_and_anonymize_FPE(input_text)
                elif st.session_state.anonymization_method == "Entities":
                    anonymized_text = analyzer.analyze_and_anonymize_entities(input_text)
                elif st.session_state.anonymization_method == "Simple":
                    anonymized_text = analyzer.analyze_and_anonymize_simple(input_text)

                st.text_area("", anonymized_text, height=200)
                st.download_button(          # download button for anonymized text
                    label="📥 Download Anonymized Text",
                    data=anonymized_text,
                    file_name="anonymized_text.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # File uploader section
    st.markdown("### 📁 Or Upload a File")
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=['txt', 'csv', 'json'],
        help="Supported formats: .txt, .csv, .json"
    )
    
    if uploaded_file:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            content = uploaded_file.getvalue().decode()
            if file_extension == 'json':
                import json                     # lazy import json when needed
                try:
                    json_content = json.loads(content)
                    input_text = ' '.join(str(v) for v in json_content.values() if isinstance(v, str))  # extract strings from json
                except json.JSONDecodeError:
                    st.error("Invalid JSON file format")
                    input_text = ""
            elif file_extension == 'csv':
                import pandas as pd            # lazy import pandas for csv handling
                import io
                try:
                    df = pd.read_csv(io.StringIO(content))
                    text_columns = df.select_dtypes(include=['object']).columns
                    input_text = ' '.join(df[text_columns].astype(str).values.flatten())  # combine text cols
                    
                    st.write("#### Preview of processed CSV content:")
                    st.dataframe(df.head(), height=150)
                except Exception as e:
                    st.error(f"Error processing CSV file: {str(e)}")
                    input_text = ""
            else:                    # handle txt files directly
                input_text = content
                
            if input_text:           # show processed content if valid
                st.session_state.text_input = input_text  # update session state
                st.experimental_rerun()      # rerun to process the text
                
        except UnicodeDecodeError:
            st.error("Unable to read file. Please ensure it's a valid text file.")

if __name__ == "__main__":
    main()