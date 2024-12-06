import os
import google.generativeai as genai
from google.generativeai import caching
import datetime
from dotenv import load_dotenv
import base64

def initialize_model():
    """Initialize and configure the Gemini model"""
    load_dotenv()
    genai.configure(api_key=os.environ['API_KEY'])
    system_instructions = os.environ['SYSTEM_INSTRUCTIONS']
    inputs = os.environ['INPUTS']
    
    system_instructions = base64.b64decode(system_instructions).decode()
    inputs = base64.b64decode(inputs).decode()

    
    cache = caching.CachedContent.create(
        model='models/gemini-1.5-flash-8b-001',
        display_name='Testing the init model',
        system_instruction=system_instructions,
        ttl=datetime.timedelta(minutes=10)
    )
    
    return genai.GenerativeModel.from_cached_content(cached_content=cache), inputs

def translate_text(text, glossaries, model, input_template):
    """Translate text using the model with given glossaries"""
    formatted_glossaries = "\n".join([f"{list(g.keys())[0]}: {list(g.values())[0]}" for g in glossaries])
    response = model.generate_content([
        input_template.format(text, formatted_glossaries),
    ])
    return response.text

def get_cached_content():
    """Get list of cached content"""
    return [str(c) for c in caching.CachedContent.list()]

def process_glossaries(glossary_list):
    """Process glossaries from list of strings in format 'jp, en'"""
    processed = []
    for glossary in glossary_list:
        jp, en = glossary.split(", ")
        processed.append({jp: en})
    return processed
