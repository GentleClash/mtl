import os
import google.generativeai as genai
from google.generativeai import caching
import datetime
from dotenv import load_dotenv
import base64
from static.prompts import UserPrompt, TranslationOutput

os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
def initialize_model():
    """Initialize and configure the Gemini model"""
    load_dotenv()

    genai.configure(api_key=os.environ['API_KEY'])
    system_instructions = UserPrompt().system_instructions
    inputs = UserPrompt().inputs

    print("Creating cached content")
    cache = caching.CachedContent.create(
        model='models/gemini-1.5-flash-8b-001',
        display_name='Testing the init model',
        system_instruction=system_instructions,
        ttl=datetime.timedelta(minutes=15)
    )
    
    return genai.GenerativeModel.from_cached_content(cached_content=cache), inputs

def translate_text(text, glossaries, model, input_template, previous_chunk, previous_translation):
    """Translate text using the model with given glossaries"""
 
    response = model.generate_content(
        input_template.format(
            text, 
            glossaries or "",  # Use empty string if None
            previous_chunk or "",  # Use empty string if None
            previous_translation or ""  # Use empty string if None
        ),
        generation_config=genai.GenerationConfig(
            response_mime_type='application/json',
            response_schema=TranslationOutput.RESPONSE_SCHEMA
        )
    )
    return response.text


def get_cached_content():
    """Get list of cached content"""
    return [str(c) for c in caching.CachedContent.list()]

def process_glossaries(glossary_list):
    """Process glossaries from list of strings in format 'lang, en'"""
    processed = []
    for glossary in glossary_list:
        lang, en = glossary.split(", ")
        processed.append({lang: en})
    return processed



if __name__=="__main__":
    previous_chunk = """」 「それは解わかりますが……」 　燈子先輩が渋い調子で答える。 『メイ・フェスティバル』。通称は『春祭』と呼ばれているこのイ ベントは、言ってみれば『春の大学祭』だ。"""
    previous_translation = " \"I understand, but...\".  Senior Tsukiko replies with a thoughtful tone.  \"The Mei Festival\".  Its nickname is \"Spring Festival\". This event is, in essence, a \"Spring University Festival.\""
    text = "ただ通常の大学祭とは 違って外部に告知などはせず、参加者は主に城都大生を対象として いる。（他学生を排除している訳ではない） 　その主な趣旨は彼が言った通り「新入生により早く大学生活に馴 な染じんでもらおう」といったもの. PROMPT_TEST_NOTICE : GENERATE EXTRACTED TERMS AND TRANSLATION NOTES FOR THIS CHUNK."

    model, inputs = initialize_model()
    print(translate_text(text=text, model=model, input_template=inputs, previous_chunk=previous_chunk, previous_translation=previous_translation, glossaries={"ミス・ミューズ" : "Miss Tokyo"}))
