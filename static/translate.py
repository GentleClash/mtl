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
    text = """「だから、私は『ミス・ミューズ』に応募した覚えはないんです！」
 珍しく燈とう子こ先輩が声を荒らげてそう言った。
「でもね、ここにちゃんと桜さくら島じまさんが所属するサークルか
ら、参加希望が申請されているんだよ。これ、協議会に登録している
正式なサークルのメルアドでしょ」
 サークル協議会の担当者もさっきから同じ言葉を繰り返している。
 俺はこのやり取りを聞いていて、微妙な違和感を感じていた。
 改めてこれまでの状況を振り返ってみると……"""
    previous_translation = ""
    previous_chunk = ""

    model, inputs = initialize_model()
    print(translate_text(text=text, model=model, input_template=inputs, previous_chunk=previous_chunk, previous_translation=previous_translation, glossaries=""))
