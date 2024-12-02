import os
import google.generativeai as genai
from google.generativeai import caching
import datetime
import time
from dotenv import load_dotenv
import base64
import prompts

load_dotenv()

genai.configure(api_key=os.environ['API_KEY'])

with open("test.txt", "r") as f:
    text = f.readlines()


verbose=True
system_instructions=base64.b64decode(prompts.system_instructions).decode()
inputs = base64.b64decode(prompts.inputs).decode()

if verbose:
    print(system_instructions)
    print(inputs)
exit()

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