import os
import google.generativeai as genai
from google.generativeai import caching
import datetime
import time
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ['API_KEY'])

with open("test.txt", "r") as f:
    text = f.readlines()


system_instructions = """
You are a professional translator for light novels. Your job is to translate the given text into English while meeting the following requirements:

### Conditions:
1. Use the glossary provided to translate specific terms. Use the exact English word from the glossary whenever a glossary term appears in the text.
2. Maintain the format and paragraph structure of the original text.
3. Identify proper nouns, unique names, or terms that are not in the glossary but appear to be significant (e.g., names, titles, locations, etc.). Provide a list of these terms separately. The names will be presented to user manually to be translated.
4. Translate the text line by line and word by word. Each line should be mapped internally to a line in the translated text.

### Expected Output:
1. Translated Text: A fluent English translation of the input text that incorporates the glossary terms.
2. Extracted Terms: A list of new unique words or phrases (not found in the glossary) with their context in the sentence. Only the words whose suspected translation is literal should be included in the list.

### Return Format:
{
  "translated_text": "<Translated English Text>",
  "extracted_terms": [
      {"term": "<Japanese Term>", "pronunciation": "<literal word in english>", "suggestions": "possibly name/verb/noun/man/machine/animal/etc."},
  ]
}
"""
inputs = """
    ### Input:
1. Original text: 
   [{}]
   
2. Glossary (list of words and their mapped English terms):
   [{}]
   """

cache = caching.CachedContent.create(
    model='models/gemini-1.5-flash-8b-001',
    display_name='Testing the init model',
    system_instruction=system_instructions,
    ttl=datetime.timedelta(minutes=5)
)

model=genai.GenerativeModel.from_cached_content(cached_content=cache)
glossaries = []
while True:
    text = str(input("Enter the text file to be translated: "))
    with open(text, "r") as f:
        text = f.read()
    print("Enter new glossaries in format glossary, word (if any), once done type 'done'")
    
    while True:
        glossary = str(input("Enter the glossary: "))
        if glossary == "done":
            break
        jp, en = glossary.split(", ")
        glossaries.append({jp: en})

    

    response = model.generate_content([
    inputs.format(text, "\n".join([f"{list(g.keys())[0]}: {list(g.values())[0]}" for g in glossaries])),
    ])

    print(response.usage_metadata)

    print(response.text)

    print("Cached content:")
    for c in caching.CachedContent.list():
        print(c)