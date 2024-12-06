import fitz 
import json
import os
from langdetect import detect  
import jieba  
import MeCab 
import re

PROGRESS_FILE = "state/pdf_progress.json"
WORD_LIMIT = 100
MIN_WORDS = 20

def file_name_from_path(file_path):
    """Extract the file name from the file path."""
    if file_path.endswith('/'):
        file_path = file_path[:-1]
        assert file_path.split('.')[-1] in {"pdf", "txt", "docx", "epub"}, "Unsupported file format"
    return file_path.split('/')[-1]

def save_progress(file_path, page_number, cursor, language):
    """Save the current progress to a JSON file."""
    progress = []
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                progress = json.load(f)
        except json.JSONDecodeError:
            progress = []
    for i in range(len(progress)):
        if file_name_from_path(progress[i]["file_path"]) == file_name_from_path(file_path):
            progress[i]["page_number"] = page_number
            progress[i]["cursor"] = cursor
            progress[i]["language"] = language
            with open(PROGRESS_FILE, "w") as f:
                json.dump(progress, f)
            return

    progress.append({
        "file_path": file_name_from_path(file_path),
        "page_number": page_number,
        "cursor": cursor,
        "language": language
    })
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

def load_progress(file_path):
    """Load progress from the JSON file if it exists."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                for i in json.load(f):
                    if file_name_from_path(i["file_path"]) == file_name_from_path(file_path):
                        return i
        except json.JSONDecodeError:
            return None
    return None

def tokenize_text(text, lang):
    """Tokenize text based on detected language."""
    if "zh" in lang :  # Chinese
        sentences = split_sentences(text)
        tokens = [jieba.cut(sentence) for sentence in sentences]
        return [token.strip() for token in tokens if token.strip()]

 
    elif lang == "ja":  # Japanese
        tagger = MeCab.Tagger()
        return tagger.parse(text).split()
    else: 
        return text.split()
    
def split_sentences(text):
    """Split text into sentences while handling ellipses and keeping punctuation."""
    sentence_endings = r'(?<!\.)\.(?!\.)|[!?]'  
    sentences = re.split(sentence_endings, text)
    return [s.strip() + '.' for s in sentences if s.strip()]



def detect_language(text):
    """Detect the language of the given text."""
    try:
        lang = detect(text)
        return lang
    except:
        return "unknown"

def parse_pdf(file_path):
    """Parse the PDF incrementally."""
    doc = fitz.open(file_path)
    progress = load_progress(file_path)
    page_number, cursor, lang = 0, 0, None
    FLAG = True if not lang else False

    if progress:
        page_number, cursor, lang = progress["page_number"], progress["cursor"], progress["language"]
        print(f"Resuming from page {page_number + 1}, cursor position {cursor}")

    partial_sentence, current_chunk = "", []
    while page_number < len(doc):
        page = doc[page_number]
        text = page.get_text("text")
        if not text.strip():  # Skip empty pages
            page_number += 1
            continue

        if FLAG:  # Detect language once per document
            lang = detect_language(text[:100])

        sentences = split_sentences(text)
        i = cursor
        word_count = 0

        # Carry over partial sentence from previous chunk
        if partial_sentence:
            current_chunk.append(partial_sentence)
            partial_sentence = ""

        while i < len(sentences):
            sentence = sentences[i]
            tokens = tokenize_text(sentence, lang)

            if word_count + len(tokens) <= WORD_LIMIT:
                current_chunk.append(sentence)
                word_count += len(tokens)
                i += 1
            else:
                partial_sentence = sentence  # Carry over unfinished sentence
                break

            # Handle page-end but not sentence-end
            if i >= len(sentences) and len(current_chunk) < MIN_WORDS:
                partial_sentence = sentence
                break

        # Print the current chunk
        if current_chunk:
            print(f"Page {page_number + 1}, Chunk starting at sentence {cursor + 1}:")
            print('\n'.join(current_chunk))

            user_input = input("Continue parsing? (y/n/save): ").strip().lower()
            if user_input == "n":
                # Discard current chunk and save progress only up to the last saved state
                save_progress(file_path, page_number, cursor, lang)
                return
            elif user_input == "save":
                # Save progress including the current chunk
                save_progress(file_path, page_number, i, lang)
                return
            elif user_input == "y":
                save_progress(file_path, page_number, i, lang)

        current_chunk = []  # Reset the chunk
        cursor = i  # Update cursor for the next iteration

        if i >= len(sentences):  # Move to the next page only after processing all sentences
            cursor = 0
            page_number += 1

    print("Reached the end of the document.")
    save_progress(file_path, page_number, 0, lang)

if __name__ == "__main__":
    if not os.path.exists("state"):
        os.makedirs("state")

    pdf_path = input("Enter the path to the PDF file: ").strip()
    if os.path.exists(pdf_path):
        parse_pdf(pdf_path)
    else:
        print("File not found!")
